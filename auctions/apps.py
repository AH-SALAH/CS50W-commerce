from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save, pre_save


class AuctionsConfig(AppConfig):
    name = 'auctions'

    def ready(self):
        # importing model classes
        from .models import Bid, Listing

        # load it here to avoid 'apps aren't loaded yet err'
        from .signals import post_save_bid_receiver, pre_save_listing_receiver, post_delete_listing_receiver

        self.get_model('Bid')
        self.get_model('Listing')

        # registering signals with the model's string label
        post_save.connect(post_save_bid_receiver, sender='auctions.Bid')
        pre_save.connect(pre_save_listing_receiver, sender='auctions.Listing')
        post_delete.connect(post_delete_listing_receiver,
                            sender='auctions.Listing')
