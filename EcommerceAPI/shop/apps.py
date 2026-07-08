from django.apps import AppConfig



class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'
    
    def ready(self):
        from shop.catalog.payments.paymentHandler import register_handlers
        register_handlers()
