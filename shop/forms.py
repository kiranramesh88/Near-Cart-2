from django import forms
from shop.models import *

class ShopForm(forms.ModelForm):
    class Meta:
        model=Shop
        exclude=["owner","is_verified","is_active","created_at","updated_at","working_days"]

class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        exclude = [
            "shop",
            "created_by",
            "coupons_used",
            "total_views",
            "is_deleted",
            "created_at",
            "updated_at"
        ]

