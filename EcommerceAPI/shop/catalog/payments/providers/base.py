from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PaymentSession:
    """Résultat générique du lancement d'un paiement, quel que soit le provider."""
    provider_reference: str      # id externe (session Stripe, order PayPal, etc.)
    redirect_url: str | None     # URL vers laquelle rediriger l'acheteur (si applicable)
    raw: dict                    # payload brut du provider, pour debug/audit


@dataclass
class NormalizedEvent:
    """Événement provider traduit dans un vocabulaire commun à toute l'app."""
    event_type: str              # 'payment.succeeded' | 'payment.failed' | 'payment.expired'
    provider_reference: str      # permet de relier à Payment.provider_reference
    order_id: str | None
    raw: dict


class PaymentProvider(ABC):
    """Interface que tout moyen de paiement doit implémenter."""

    name: str  # ex: 'stripe', 'paypal', 'plaid'

    @abstractmethod
    def create_payment_session(self, order, success_url: str, cancel_url: str) -> PaymentSession:
        """Initiate a payment for an order, returning where to redirect the customer."""
        ...

    @abstractmethod
    def verify_and_parse_webhook(self, request) -> NormalizedEvent:
        """Verify the webhook signature and normalize the event into a NormalizedEvent."""
        ...