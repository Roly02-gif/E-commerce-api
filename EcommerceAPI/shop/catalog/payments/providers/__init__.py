from django.conf import settings
from .stripe_provider import StripeProvider

_PROVIDERS = {
    'STRIPE': StripeProvider,
    # 'paypal': PaypalProvider,   # à ajouter plus tard, aucun autre fichier à toucher
}


def get_provider(name: str):
    provider_class = _PROVIDERS.get(name)
    if not provider_class:
        raise ValueError(f"Unknown payment provider : {name}")
    return provider_class()


def default_provider():
    return get_provider(settings.DEFAULT_PAYMENT_PROVIDER)