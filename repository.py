from model import Batch

import abc


class AbstractRepository(abc.ABC):
    """Самый простой из возможных абстрактных репозиториев"""
    # В реальной жизни абстрактные базовые классы удаляются из производственного кода, потому python
    # легко игнорирует их и они в конечном итоге остаются без поддержки.
    # Здесь абстрактные классы используются для наглядности интерфейсов в python

    @abc.abstractmethod
    def add(self, batch: Batch):
        raise NotImplementedError()

    @abc.abstractmethod
    def get(self, reference: str) -> Batch:
        raise NotImplementedError()
