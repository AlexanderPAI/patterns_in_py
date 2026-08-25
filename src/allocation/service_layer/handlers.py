from __future__ import annotations

from src.allocation.adapters import email, redis_eventpublisher
from src.allocation.domain import events, model, commands
from src.allocation.service_layer import unit_of_work

class InvalidSku(Exception):
    pass


def add_batch(command: commands.CreateBatch, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get(sku=command.sku)
        if product is None:
            product = model.Product(command.sku, batches=[])
            uow.products.add(product)
        product.batches.append(model.Batch(command.ref, command.sku, command.qty, command.eta))
        uow.commit()


def allocate(command: commands.Allocate, uow: unit_of_work.AbstractUnitOfWork):
    line = model.OrderLine(command.orderid, command.sku, command.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Недопустимый артикул {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref


def reallocate(event: events.Deallocated, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get(sku=event.sku)
        product.events.append(event)
        uow.commit()


def send_out_of_stock_notification(event: events.OutOfStock, uow: unit_of_work.AbstractUnitOfWork):
    email.send_mail(
        'stock@made.com',
        f'Артикула {event.sku} нет в наличии',
    )


def change_batch_quantity(
        command: commands.ChangeBatchQuantity,
        uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get_by_batchref(batchref=command.ref)
        product.change_batch_quantity(ref=command.ref, qty=command.qty)
        uow.commit()


def publish_allocated_event(event: events.Allocated, uow: unit_of_work.AbstractUnitOfWork):
    redis_eventpublisher.publish('line_allocated', event)


def add_allocation_to_read_model(event: events.Allocated, _):
    redis_eventpublisher.update_readmodel(event.orderid, event.sku, event.batchref)


def remove_allocation_from_read_model(event: events.Deallocated, _):
    redis_eventpublisher.update_readmodel(event.orderid, event.sku, None)


EVENT_HANDLERS = {
    events.Allocated: [publish_allocated_event, add_allocation_to_read_model],
    events.Deallocated: [remove_allocation_from_read_model, reallocate],
    events.OutOfStock: [send_out_of_stock_notification],
}


COMMAND_HANDLERS = {
    commands.Allocate: allocate,
    commands.CreateBatch: add_batch,
    commands.ChangeBatchQuantity: change_batch_quantity,
}
