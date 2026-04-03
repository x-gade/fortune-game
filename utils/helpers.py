from typing import Iterable


def get_next_id(items: Iterable[object]) -> int:
    """
    Return next integer identifier for collection of objects with id.
    Вернуть следующий целочисленный идентификатор для коллекции объектов с id.
    """
    ids = [getattr(item, "id", 0) for item in items]
    return max(ids, default=0) + 1