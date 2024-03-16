#! /usr/bin/env python3
import csv
import hashlib
import logging
import os
import timeit
from enum import Enum
from itertools import chain
from pathlib import Path
from typing import Callable, TypedDict

import typer
from seahash import SeaHash
from git import Repo

TEST_DATA_SIZE = 1024 * 1024 * 1024  # 1GB


def prepare_test_data(size: int) -> (bytes, Path):
    path = Path("test.bin")
    if path.exists() and os.path.getsize(path) == size:
        logging.info("Found an already prepared test file, neat!")
        return path.read_bytes(), path

    logging.info(f"Preparing {size} bytes test data, this might take a while ...")
    buffer = os.urandom(size)
    path.write_bytes(buffer)
    logging.info(f"Finished preparing: {path}")
    return buffer, path


def hashit(hashfunc: Callable, buffer: bytes | Path) -> Callable[[], None]:
    if isinstance(buffer, bytes):

        def _hashit() -> None:
            hash = hashfunc()
            hash.update(buffer)
    elif isinstance(buffer, Path):

        def _hashit() -> None:
            with buffer.open("rb") as f:
                hashlib.file_digest(f, hashfunc)
    else:
        raise TypeError()
    return _hashit


Run = TypedDict(
    "Run",
    {
        "name": str,
        "commit": str,
        "dirty": bool,
        "1GB in-memory time (s)": float,
        "1GB file time (s)": float,
        "number of runs": float,
    },
)


class Bench(Enum):
    ALL = "all"
    SEAHASH = "sea"
    SHA1 = "sha1"


def main(bench: Bench, number: int):
    seahash_lambda = ("SeaHash", lambda: SeaHash())
    match bench:
        case Bench.ALL:
            hashes = chain(
                map(
                    lambda a: (a, lambda: hashlib.new(a)), hashlib.algorithms_available
                ),
                [seahash_lambda],
            )
        case Bench.SEAHASH:
            hashes = [seahash_lambda]
        case Bench.SHA1:
            hashes = [("SHA1", lambda: hashlib.sha1())]
        case _:
            raise TypeError
    history_csv = Path("bench_history_v2.csv")

    repo = Repo(".")
    dirty = repo.is_dirty()
    commit = repo.head.commit.hexsha

    # Prepare the history csv file the first time it is used.
    if not history_csv.exists():
        with history_csv.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=Run.__annotations__.keys())
            writer.writeheader()

    test_buffer, path = prepare_test_data(TEST_DATA_SIZE)
    for name, hashfunc in hashes:
        print(f"Measuring {name}...")
        mem_time = timeit.timeit(hashit(hashfunc, test_buffer), number=number)
        print(f"{name} in-memory: {mem_time}")
        file_time = timeit.timeit(hashit(hashfunc, path), number=number)
        print(f"{name} file digest: {file_time}")
        print(f"File hash time to in-memory hash time ratio: {file_time / mem_time}")
        run: Run = {
            "name": name,
            "commit": commit,
            "dirty": dirty,
            "number of runs": number,
            "1GB in-memory time (s)": mem_time,
            "1GB file time (s)": file_time,
        }
        with history_csv.open("a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=Run.__annotations__.keys())
            writer.writerow(run)


if __name__ == "__main__":
    typer.run(main)
