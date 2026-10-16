from django.db import models
from users.models import *
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Sum


# Create your models here.


class Shop(models.Model):
    CATEGORY_CHOICES = (
    ("grocery", "Grocery"),
    ("electronics", "Electronics"),
    ("fashion", "Fashion"),
    ("restaurant", "Restaurant"),
    ("pharmacy", "Pharmacy"),
    ("other", "Other"),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE,related_name="shop")

    shop_name = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    custom_category = models.CharField(max_length=100, blank=True, null=True)

    logo = models.ImageField(upload_to="shop_logos/", blank=True)

    banner = models.ImageField(upload_to="shop_banners/", blank=True)

    images= models.ImageField(upload_to="shop_images/",blank=True)

    address = models.TextField()

    city = models.CharField(max_length=100)

    district = models.CharField(max_length=100)

    state = models.CharField(max_length=100)

    pincode = models.CharField(max_length=6)

    latitude = models.FloatField()

    longitude = models.FloatField()

    phone = models.CharField(max_length=15)

    email = models.EmailField(blank=True)

    website = models.URLField(blank=True)

    opening_time = models.TimeField()

    closing_time = models.TimeField()

    is_open = models.BooleanField(default=True)

    is_verified = models.BooleanField(default=False)

    verified_at =models.DateTimeField(blank=True,null=True)

    license_number = models.CharField(max_length=100, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    rating=models.FloatField(default=0)

    total_reviews = models.IntegerField(default=0)

    WORKING_DAYS_CHOICES = [
        ("mon", "Monday"),
        ("tue", "Tuesday"),
        ("wed", "Wednesday"),
        ("thu", "Thursday"),
        ("fri", "Friday"),
        ("sat", "Saturday"),
        ("sun", "Sunday"),
    ]

    working_days = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.shop_name
    @property
    def is_open_now(self):
        now = timezone.localtime()
        current_day = now.strftime("%a").lower()[:3]
        current_time = now.time()

        if current_day not in self.working_days:
            return False

        if self.opening_time < self.closing_time:
            return self.opening_time <= current_time <= self.closing_time
        else:
            # overnight case
            return current_time >= self.opening_time or current_time <= self.closing_time
        
    @property
    def recommendation_label(self):
        rating = self.rating or 0

        if 4 <= rating <= 5:
            return "Highly Recommended"
        elif 3 <= rating < 4:
            return "Recommended"
        elif 2 <= rating < 3:
            return "Average"
        elif 1 <= rating < 2:
            return "Low Rated"
        else:
            return "No Ratings Yet"

class Offer(models.Model):
    shop = models.ForeignKey(Shop,on_delete=models.CASCADE,related_name="offers")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True,null=True)
    original_price = models.FloatField()
    discount_price = models.FloatField()
    discount_percentage = models.FloatField(blank=True, null=True)
    image = models.ImageField(upload_to="offer_images/", blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_coupon_based = models.BooleanField(default=False)
    total_coupons = models.IntegerField(blank=True, null=True)
    coupons_used = models.IntegerField(default=0)
    target_city = models.CharField(max_length=100, blank=True)
    target_radius_km = models.FloatField(blank=True, null=True)
    notify_users = models.BooleanField(default=False)
    total_views = models.IntegerField(default=0)  # optional quick access
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.shop.shop_name}"
    @property
    def is_currently_active(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
    @property
    def time_remaining(self):
        now = timezone.now()
        diff = self.end_date - now

        if diff.total_seconds() <= 0:
            return "expired"

        days = diff.days

        if days > 1:
            return f"{days} days left"

        elif days == 1:
            return "Ends tomorrow"

        else:
            # less than 1 day → show countdown
            hours = diff.seconds // 3600
            minutes = (diff.seconds % 3600) // 60
            return f"{hours}h {minutes}m left"

    @property
    def coupons_remaining(self):
        if not self.is_coupon_based or not self.total_coupons:
            return 0

        # ✅ Claimed but not expired and not redeemed
        active_claimed = Coupon.objects.filter(
            offer=self,
            is_redeemed=False,
            valid_to__gt=now()
        ).aggregate(total=Sum('quantity'))['total'] or 0

        # ✅ Permanently used coupons
        redeemed = Coupon.objects.filter(
            offer=self,
            is_redeemed=True
        ).aggregate(total=Sum('quantity'))['total'] or 0

        return max(0, self.total_coupons - active_claimed - redeemed)

    # @property
    # def coupons_remaining(self):
    #     if not self.is_coupon_based or not self.total_coupons:
    #         return 0

    #     active_coupons = Coupon.objects.filter(
    #         offer=self,
    #         is_redeemed=False,
    #         valid_to__gt=now()
    #     ).aggregate(total=Sum('quantity'))['total'] or 0

    #     return max(0, self.total_coupons - self.coupons_used)

    # ✅ AUTO CALCULATE DISCOUNT
    def save(self, *args, **kwargs):
        if self.original_price and self.discount_price:
            try:
                self.discount_percentage = (
                    (self.original_price - self.discount_price)
                    / self.original_price
                ) * 100
            except:
                self.discount_percentage = None

        super().save(*args, **kwargs) 

    @property
    def is_expired(self):
        return self.end_date < timezone.now()


import uuid
from django.utils.timezone import now
from datetime import timedelta

class Coupon(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_coupons",blank=True,null=True)

    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, related_name="coupons")
    offer = models.ForeignKey('Offer', on_delete=models.CASCADE, related_name="coupons",blank=True,null=True)

    code = models.CharField(max_length=20, unique=True)

    quantity = models.PositiveIntegerField(default=1)  

    qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True) 

    valid_from = models.DateTimeField(default=now)
    valid_to = models.DateTimeField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    is_redeemed = models.BooleanField(default=False)

    def is_valid(self):
        return self.is_active and now() <= self.valid_to
    
    def status(self):
        return "Active" if self.is_valid() else "Expired"

    def __str__(self):
        return f"{self.code} - {self.user}"
    


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('coupon', 'user')  # Prevent reuse


class Review(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    offer = models.ForeignKey(Offer,on_delete=models.CASCADE,related_name="reviews",null=True,blank=True)


    rating = models.IntegerField()  # 1 to 5
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('offer', 'user')  # one review per user

    def __str__(self):
        return f"{self.shop.shop_name} - {self.rating}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        from django.db.models import Avg

        avg_rating = self.shop.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        total = self.shop.reviews.count()

        self.shop.rating = round(avg_rating, 2)
        self.shop.total_reviews = total
        self.shop.save()
    
    def delete(self, *args, **kwargs):
        shop = self.shop
        super().delete(*args, **kwargs)

        from django.db.models import Avg

        avg_rating = shop.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        total = shop.reviews.count()

        shop.rating = round(avg_rating, 2)
        shop.total_reviews = total
        shop.save()


class StoreView(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)


    




