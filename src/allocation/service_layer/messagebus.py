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
                logger.debug(
                    "обрабатывается событие %s обработчиком %s",
                    event,
                    handler,
                )
                handler(event)
            except Exception:
                logger.exception("Событие обработки исключения %s", event)
                continue

        self.queue.extend(self.uow.collect_new_messages())

    def command_handle(self, command: commands.Command):
        try:
            logger.debug("обрабатывается команда %s", command)
            handler = self.command_handlers[type(command)]
            handler(command)
            self.queue.extend(self.uow.collect_new_messages())
        except Exception:
            logger.exception("Команда обработки исключения %s", command)
            raise
