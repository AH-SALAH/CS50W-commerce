from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver
from .models import Listing, Bid

# # ######################################


@receiver(post_save, sender=Bid)
def post_save_bid_receiver(sender, instance, created, *args, **kwargs):
    if instance.listing:
        try:
            # update last_price in the listing
            Listing.objects.filter(pk=instance.listing.pk).update(
                last_price=instance.amount)

            # from django.core.mail import send_mail

            # send_mail(
            #     'new bid has been made!',
            #     f'a new bid made on - {instance.listing.title} - with amount of ${instance.amount}',
            #     'auctions_app@django.com',
            #     ['mail@ymail.com'],
            #     fail_silently=False,
            # )
        except Exception:
            pass


@receiver(post_delete, sender=Listing)
def post_delete_listing_receiver(sender, instance, *args, **kwargs):
    if instance.image:
        try:
            # remove old img after deleting instance
            instance.image.delete(save=False)

        except Exception as er:
            print("post_delete:img_del_from_model:signal: ", er)


@receiver(pre_save, sender=Listing)
def pre_save_listing_receiver(sender, instance, *args, **kwargs):
    if instance.image:
        try:
            # remove old img on update
            # print("instance_img: ", instance.image)

            # get old img
            old_instance = instance.__class__.objects.get(pk=instance.pk)
            old_img_path = old_instance.image.path if old_instance.image else ''
            # print("old_path: ", old_img_path)
            old_img = old_img_path.replace(
                '\\', '/').split('/')[-1] if old_img_path else ''
            # print("old_img: ", old_img)
            # get new instace image
            new_img_path = instance.image.path
            # print("new_path: ", new_img_path)
            new_img = new_img_path.replace('\\', '/').split('/')[-1]
            # print("new_img: ", new_img)

            if new_img_path and old_img_path and new_img != old_img:
                import os
                # print("pre_save:listing: ", "\nold_img_path: ", old_img_path, "\nnew_img_path: ", new_img_path)
                os.remove(old_img_path)

        except Exception as er:
            print("pre_save:img_del:signal: ", er)
    else:
        try:
            old_instance = instance.__class__.objects.get(pk=instance.pk)
            instance.image = old_instance.image
        except Exception as er:
            print("pre_save:old=new:signal: ", er)
