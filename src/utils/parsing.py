from __future__ import annotations

import io
from typing import Dict, Iterable, Iterator

import ijson

class StreamingBytesReader(io.RawIOBase):
    """
    Adapt a bytes iterator into a file-like stream for ijson.

    ijson expects a readable object with a read()/readinto() interface. This class
    buffers incoming chunks from an iterator and serves them through readinto so
    large JSON can be parsed incrementally without loading the full document.
    """

    def __init__(self, chunks: Iterable[bytes]) -> None:
        self._iter = iter(chunks)
        self._buffer = bytearray()

    def readable(self) -> bool:  # pragma: no cover - trivial
        return True

    def readinto(self, b: bytearray) -> int:
        while len(self._buffer) < len(b):
            try:
                self._buffer.extend(next(self._iter))
            except StopIteration:
                break
        if not self._buffer:
            return 0
        n = min(len(b), len(self._buffer))
        b[:n] = self._buffer[:n]
        del self._buffer[:n]
        return n


def iter_json_items(byte_iter: Iterable[bytes], path: str) -> Iterator[Dict]:
    """
    Stream JSON items at a given ijson path from a bytes iterator.
    Path for table-of-contents: "reporting_structure.item".
    """

    reader = StreamingBytesReader(byte_iter)
    for item in ijson.items(reader, path):
        yield item


def iter_reporting_structures(byte_iter: Iterable[bytes]) -> Iterator[Dict]:
    return iter_json_items(byte_iter, "reporting_structure.item")
