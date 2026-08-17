from model import Batch

import abc


class AbstractRepository(abc.ABC):
    """Самый простой из возможных абстрактных репозиториев"""

    @abc.abstractmethod
    def add(self, batch: Batch):
        raise NotImplementedError()

    @abc.abstractmethod
    def get(self, reference: str) -> Batch:
        raise NotImplementedError()
