def hash(buf: bytes) -> int: ...
def hash_seeded(buf: bytes, a: int, b: int, c: int, d: int) -> int: ...

class SeaHash:
    digest_size: int
    block_size: int

    def __init__(self, data: bytes = b""): ...
    def update(self, obj: bytes | memoryview) -> None: ...
    def digest(self) -> bytes: ...
    def intdigest(self) -> int: ...
    def hexdigest(self) -> str: ...
    def copy(self) -> SeaHash: ...
