from typing import Iterable, TypeVar


T = TypeVar("T")


def batch_iterable(iterable: Iterable[T], batch_size: int) -> Iterable[Iterable[T]]:
    this_batch = []
    for entry in iterable:
        this_batch.append(entry)
        if len(this_batch) == batch_size:
            yield this_batch
            this_batch = []
    if this_batch:
        yield this_batch
