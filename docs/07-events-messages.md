#События и сообщения

**Принцип единой обязанности (SRP)** - каждый класс должен иметь только одну причину для его изменения.

Например, нам надо отправлять email в отдел закупок, если товар закончился.
Размещение отправки email модели предметной области, в API, в сервисном слое будет нарушением принципа единой обязанности.

Для обеспечения соблюдения этого принципа, можно использовать паттерны:
- События предметной области
- Шина сообщений

#### Модель регистрирует события

Вместо того чтобы беспокоиться об отправке email, модель будет отвечать за регистрацию **событий** - фактов произошедшего.
Используем шину сообщений, через которую будем реагировать на события и вызывать новую операцию.

#### События - это простые датаклассы

**Событие** - это вид объекта-значения. У событий нет поведения, потому что они представляют собой чистые структуры 
данных. События должны называться на языке предметной области и ее частью.

Например:
```python
#/domain/events.py

from dataclasses import dataclass
class Event:
    pass
    
    
@dataclass
class OutOfStock(Event):
    sku: str
```

#### Модель инициирует события

Когда модель предметной области регистрирует произошедший факт, мы говорим, что она инициирует событие.

#### Шина сообщений попарно сопоставляет события с обработчиками

Шина сообщений, в сущности, говорит "Когда я вижу это событие, я должна вот эту функцию-обработчик"
Это простая система "Издатель-подписчик".
Обработчики подписываются на получение событий, которые публикуются в канале. 

> Шина сообщений не обеспечивает согласованность, поскольку выполняется по одному обработчику за раз.
> Цель состоит не в том, чтобы поддерживать параллельные потоки, а в том, чтобы разделить задачи концептуально и 
> сделать каждый UoW как можно меньше

## Далее можно реализовать несколькими способами

### Вариант 1: сервисный слой берет события из модели предметной области и помещает их в шину сообщений

Модель предметной области инициирует события.

Шина сообщений вызывает нужные обработчики.

Соответственно, теперь нужно сделать публикацию событий.

Если возложить это на сервисный слой, то это может выглядеть так:
```python
# src/allocation/service_layer/services.py

from . import messagebus
...
def allocate(
    orderid: str, sku: str, qty: int,
    uow: unit_of_work.AbstractUnitOfWork
    ) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f'Недопустимый артикул {line.sku}')
        try:
            batchref = product.allocate(line)
            uow.commit()
            return batchref
        finally:
            messagebus.handle(product.events) 
```

### Вариант 2: сервисный слой инициирует собственные события

Еще один вариант - сделать так, чтобы сервисный слой непостредственно отвечал за создание и инициирование событий,
а не за получение их модели предметной области, которая инициирует их.
```python
# src/allocation/service_layer/services.py

def allocate(
        orderid: str, sku: str, qty: int,
        uow: unit_of_work.AbstractUnitOfWork
):
    line = OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(sku=sku)
        if product is None:
            raise InvalidSku(f'Недопустимый артикул {line.sku}')
        batchref = product.allocate(line)
        uow.commit()
        
        if batchref is None:
            messagebus.handle(events.OutOfStock(line.sku))
        return batchref
```

### Вариант 3: UoW публикует события в шине сообщений

```python
# src/allocation/service_layer/unit_of_work.py

class AbstactUnitOfWork(abc.ABC):
    ...
    def commit(self):
        self._commit()
        self.publish_events()

    def publish_events(self):
        for product in self.products.seen:
            while product.events:
                event = product.events.pop(0)
                messagebus.handle(event)
    
    @abc.abstractmethod
        def _commit(self):
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    ...
    def _commit(self):
        self.session.commit()
```

А репозиторий отслеживает проходящие через него агрегаты:
```python
# src/allocation/adapters/repository.py

class AbstractRepository:
    
    def __init__(self):
        self.seen = set()

    def add(self, product: model.Product):
        self._add(product)
        self.seen.add(product)
    def get(self, sku) -> model.Product:
        product = self._get(sku)
        if product:
            self.seen.add(product)  
        return product
    @abc.abstractmethod
    def _add(self, product: model.Product):
        raise NotImplementedError
    
    @abc.abstractmethod
    def _get(self, sku) -> model.Product:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    
    def __init__(self, session):
        super().__init__()
        self.session = session
        
    def _add(self, product):
        self.session.add(product)

    def _get(self, sku):
        return self.session.query(model.Product).filter_by(sku=sku).first()
```

Чтобы паттерн UoW мог публиковать новые события, он должен иметь возможность узнавать у репозитория, какие объекты 
Product использовались во время этого сеанса. Для их хранения применяется множество под названием .seen. Это означает, 
что наши реализации должны вызывать super().__init__()

