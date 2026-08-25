import abc
import smtplib

from src.allocation import config

DEFAULT_HOST = config.get_email_host_and_port()['host']
DEFAULT_PORT = config.get_email_host_and_port()['port']

class AbstractNotifications(abc.ABC):

    @abc.abstractmethod
    def send(self, destination, message):
        raise NotImplementedError()


class EmailNotifications(AbstractNotifications):

    def __init__(self, smtp_host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.server = smtplib.SMTP(smtp_host, port)
        self.server.noop()

    def send(self, destination, message):
        msg = f"Subject: allocation service notification\n{message}"
        self.server.sendmail(
            from_addr='allocations@example.com',
            to_addrs=[destination],
            msg=msg
        )
