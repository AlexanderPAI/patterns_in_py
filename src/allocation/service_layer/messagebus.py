from __future__ import annotations

from typing import List, Dict, Callable, Type, TYPE_CHECKING, Union
import logging
from tenacity import Retrying, RetryError, stop_after_attempt, wait_exponential

from src.allocation.domain import events, commands
from src.allocation.service_layer import handlers


if TYPE_CHECKING:
    from . import unit_of_work

logger = logging.getLogger(__name__)


Message = Union[events.Event, commands.Command]


class MessageBus:

    def __init__(
            self,
            uow: unit_of_work.AbstractUnitOfWork,
            event_handlers: Dict[Type[events.Event], List[Callable]],
            command_handlers: Dict[Type[commands.Command], Callable],
    ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    def handle(self, message: Message) -> Message:
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message)
            elif isinstance(message, commands.Command):
                self.command_handle(message)
            else:
                raise Exception(f"Сообщение {message} не было Событием или Командой")

    def handle_event(self, event: events.Event):
        for handler in self.event_handlers[type(event)]:
            try:
                logger.debug('обрабатывается событие %s обработчиком %s', event, handler)
                handler(event)
                self.queue.extend(self.uow.collect_new_messages())
            except Exception:
                logger.exception('Событие обработки исключения %s', event)
                continue

    def command_handle(self, command: commands.Command):
        try:
            logger.debug('обрабаотывается команда %s', command)
            handler = self.command_handlers[type(command)]
            handler(command)
            self.queue.extend(self.uow.collect_new_messages())
        except Exception:
            logger.exception('Команда обработки исключения %s', command)
            raise



def handle_event(event: events.Event, queue : List[Message], uow: unit_of_work.AbstractUnitOfWork):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(),
            ):
                with attempt:
                    logger.debug(f"Обработка события %s обработчиком %s", event, handler)
                    handler(event, uow)
                    queue.extend(uow.collect_new_messages())
        except RetryError as retry_failure:
            logger.error(
                'Не получилсоь обработать событие %s раз, отказ!',
                retry_failure.last_attempt.attempt_number
            )
            continue


def handle_command(command: commands.Command, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
    logger.debug("handling command %s", command)
    try:
        handler = COMMAND_HANDLERS[type(command)]
        result = handler(command, uow)
        queue.extend(uow.collect_new_messages())
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
    events.Allocated: [handlers.publish_allocated_event, handlers.add_allocation_to_read_model],
    events.Deallocated: [handlers.remove_allocation_from_read_model, handlers.reallocate],
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}


COMMAND_HANDLERS = {
    commands.Allocate: handlers.allocate,
    commands.CreateBatch: handlers.add_batch,
    commands.ChangeBatchQuantity: handlers.change_batch_quantity,
}


# HANDLERS = {
#     events.BatchCreated: [handlers.add_batch],
#     events.BatchQuantityChanged: [handlers.change_batch_quantity],
#     events.AllocationRequired: [handlers.allocate],
#     events.OutOfStock: [handlers.send_out_of_stock_notification],
# }  # type: Dict[Type[events.Event], List[Callable]]