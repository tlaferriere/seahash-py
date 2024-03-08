#! /usr/bin/env python3

import hashlib
import logging
import os
import platform
import time
from itertools import chain
from typing import Callable
from pathlib import Path

import pyperf

from seahash import SeaHash

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


def bench() -> None:
    test_buffer, path = prepare_test_data(TEST_DATA_SIZE)

    runner = pyperf.Runner()
    for (name, hashfunc) in chain(
        map(lambda a: (a, lambda: hashlib.new(a)), hashlib.algorithms_available),
        [("SeaHash", lambda: SeaHash())],
    ):
        print(f"Measuring {name}...")
        mem_benchmark = runner.bench_func(
            f"{name} in-memory", hashit(hashfunc, test_buffer)
        )
        print(mem_benchmark.get_total_duration())
        file_benchmark = runner.bench_func(f"{name} file digest", hashit(hashfunc, path))
        print(file_benchmark.get_values())


if __name__ == "__main__":
    bench()
