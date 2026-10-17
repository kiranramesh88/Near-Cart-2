from django.db import models
from django.contrib.auth.models import AbstractUser
from random import randint

# Create your models here.

class User(AbstractUser):
    role_options=[
        ("Customer","Customer"),
        ("Vendor","Vendor")
    ]
    role=models.CharField(max_length=20,choices=role_options,default="Customer")
    phone=models.CharField(max_length=100)
    is_verified=models.BooleanField(default=False)
    otp=models.CharField(max_length=100,null=True,blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def generate_otp(self):
        otp_number=str(randint(1000,9000))+str(self.id)
        self.otp=otp_number
        self.save()

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile")

    phone = models.CharField(max_length=15, blank=True, default="")
    profile_image = models.ImageField(upload_to="customer_profiles/", null=True, blank=True)

    address = models.TextField(blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")

    date_of_birth = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
    
class VendorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="vendor_profile")

    phone = models.CharField(max_length=15, blank=True, default="")
    profile_image = models.ImageField(upload_to="vendor_profiles/", null=True, blank=True)

    address = models.TextField(blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")

    business_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
