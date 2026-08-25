import abc
import smtplib
from email.message import EmailMessage

from src.allocation import config

DEFAULT_HOST = config.get_email_host_and_port()["host"]
DEFAULT_PORT = config.get_email_host_and_port()["port"]

FROM_ADDRESS = "allocations@example.com"
SUBJECT = "allocation service notification"


class AbstractNotifications(abc.ABC):
    @abc.abstractmethod
    def send(self, destination: str, message: str) -> None:
        raise NotImplementedError()


class EmailNotifications(AbstractNotifications):
    def __init__(self, smtp_host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.server = smtplib.SMTP(smtp_host, port)
        self.server.noop()

    def send(self, destination: str, message: str) -> None:
        email = EmailMessage()
        email["From"] = FROM_ADDRESS
        email["To"] = destination
        email["Subject"] = SUBJECT
        email.set_content(message, charset="utf-8")

        self.server.send_message(email)
