import abc

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

import config
from adapters import repository


class AbstractUnitOfWork(abc.ABC):
    batches: repository.AbstractRepository       # UoW предоставляет атрибут .batches, который обеспечит доступ
                                                 # к репозиторию партий товара.

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, *args):                   # __enter__ и __exit__, которые выполняются соответственно при
                                                 # входе в блок with и при выходе из него. Это фазы наладки и демонтажа
        self.rollback()                          # Если мы не выполняем фиксацию или выходим из контекстного менеджера,
                                                 # инициировав ошибку, то выполняем откат

    @abc.abstractmethod
    def commit(self):                            # Вызовем этот метод, чтобы явно зафиксировать работу,
                                                 # когда мы будем готовы
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


# Настоящий UoW использует сеансы SQLAlchemy

DEFAULT_SESSION_FACTORY = sessionmaker(bind=create_engine(config.get_postgres_uri()))


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):

    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.batches = repository.SqlAlchemyRepository(self.session)
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()