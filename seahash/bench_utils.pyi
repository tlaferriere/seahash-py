from os import PathLike
from pathlib import Path


def prepare_test_data(path: PathLike | Path, size: int) -> (bytes, int): ...
