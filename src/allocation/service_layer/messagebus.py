from __future__ import annotations
from typing import List, Dict, Callable, Type, TYPE_CHECKING, Union
import logging

from src.allocation.domain import events, commands
from src.allocation.service_layer import handlers


if TYPE_CHECKING:
    from . import unit_of_work

logger = logging.getLogger(__name__)


Message = Union[events.Event, commands.Command]


def handle_event(event: events.Event, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
    for handler in EVENT_HANDLERS(type(event)):
        try:
            logger.debug('handling event %s with handler %s', event, handler)
            handler(event, uow)
            queue.extend(uow.collect_new_events())
        except Exception:
            logger.exception('Exception handling event %s', event)
            continue


def handle_command(command: commands.Command, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
    logger.debug("handling command %s", command)
    try:
        handler = COMMAND_HANDLERS(type(command))
        result = handler(command, uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception:
        logger.exception('Exception handling command %s', command)
        raise


def handle(message: Message, uow: unit_of_work.AbstractUnitOfWork):
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            cmd_result = handle_command(message, queue, uow)
            results.append(cmd_result)
        else:
            raise Exception(f'{message} was not an Event or Command')
    return results


EVENT_HANDLERS = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}


COMMAND_HANDLERS = {
    commands.Allocate: handlers.allocate,
    commands.CreateBatch: handlers.add_batch,
    commands.ChangeBatchQuantity: handlers.change_batch_quantity,
}


HANDLERS = {
    events.BatchCreated: [handlers.add_batch],
    events.BatchQuantityChanged: [handlers.change_batch_quantity],
    events.AllocationRequired: [handlers.allocate],
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}  # type: Dict[Type[events.Event], List[Callable]]