from django.db import models
from users.models import *
from shop.models import *

# Create your models here.

class SavedOffer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'offer')  # prevent duplicates

    def __str__(self):
        return f"{self.user} saved {self.offer}"