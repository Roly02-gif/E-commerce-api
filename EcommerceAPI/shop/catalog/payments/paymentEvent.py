from dataclasses import dataclass
from collections import defaultdict


@dataclass(frozen=True)
class PaymentSucceeded:
    order_id: str


@dataclass(frozen=True)
class PaymentFailed:
    order_id: str


@dataclass(frozen=True)
class PaymentExpired:
    order_id: str


class EventBus:
    def __init__(self):
        self._handlers = defaultdict(list)

    def subscribe(self, event_class, handler):
        self._handlers[event_class].append(handler)

    def publish(self, event):
        print("DEBUG PUBLISH METH: ", self._handlers)
        for handler in self._handlers[type(event)]:
            handler(event)


event_bus = EventBus()