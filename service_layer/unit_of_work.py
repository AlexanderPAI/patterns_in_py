import abc

from adapters import repository


class AbstractUnitOfWork(abc.ABC):
    batches: repository.AbstractRepository

    @abc.abstractmethod
    def __exit__(self, *args):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError
