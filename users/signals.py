from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import User
from users.models import VendorProfile,CustomerProfile

@receiver(post_save, sender=User)
def create_profiles(sender, instance, created, **kwargs):
    if created:
        if instance.role == "Vendor":
            VendorProfile.objects.get_or_create(user=instance)
        else:
            CustomerProfile.objects.get_or_create(user=instance)