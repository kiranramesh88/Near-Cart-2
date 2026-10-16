from django.shortcuts import render,redirect
from django.views import View
from shop.models import *
from shop.forms import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count
from django.db.models import Case, When, Value, IntegerField
from django.db.models import Count, Q

def get_stars(rating):
    stars = []
    for i in range(1, 6):
        if rating >= i:
            stars.append("full")
        elif rating >= i - 0.5:
            stars.append("half")
        else:
            stars.append("empty")
    return stars

class CreateShopView(View):
    def get(self,request):
        form=ShopForm()
        return render(request,"create_shop.html",{"form":form})

    def post(self,request):
            
            form = ShopForm(request.POST, request.FILES)

            if form.is_valid():
                shop = form.save(commit=False)

                shop.owner = request.user
                working_days = request.POST.getlist("working_days")
                shop.working_days = working_days
                if shop.category != "other":
                    shop.custom_category = None


                shop.save()

                return redirect("vendordash")

            print(form.errors)

            return render(request, "create_shop.html", {"form": form})
    
class VendorDashboardView(View):
     def get(self,request):
          user=request.user
        #   profile, _ = VendorProfile.objects.get_or_create(user=request.user)

          shop=Shop.objects.get(owner=user)
          current_time=now()
        #   offer=Offer.objects.filter(shop=shop)
          offers = Offer.objects.filter(shop=shop,is_deleted=False).annotate(redeemed_count=Count('coupons',filter=Q(coupons__is_redeemed=True)),is_expired_order=Case(
        When(end_date__lt=current_time, then=Value(1)),  # expired → lower priority
        default=Value(0),  # active → higher priority
        output_field=IntegerField())).order_by('is_expired_order', '-end_date')
          total_views = StoreView.objects.filter(shop=shop).count()
          total_redemptions = Coupon.objects.filter(shop=shop,is_redeemed=True).count()
          profile, _ = VendorProfile.objects.get_or_create(user=user)

          active_offers = Offer.objects.filter(shop=shop,end_date__gte=current_time,is_deleted=False).count()
          revenue = Coupon.objects.filter(shop=shop,is_redeemed=True).aggregate(total=Sum('offer__discount_price'))['total'] or 0
          context = {
            "data":user,
            "shop": shop,
            "total_views": total_views,
            "total_redemptions": total_redemptions,
            "active_offers": active_offers,
            "revenue": revenue,
            "profile": profile,
            "offers": offers,
            # "profile": profile
            }

          return render(request,"vendor_dash.html",context)

class EditShopView(View):

    def get(self, request, **kwargs):
        sid = kwargs.get('sid')
        shop = Shop.objects.get(id=sid)

        form = ShopForm(instance=shop)

        return render(request, "edit_shop.html", {"form": form, "shop": shop})

    def post(self, request, **kwargs):
        sid = kwargs.get('sid')
        shop = Shop.objects.get(id=sid)

        form = ShopForm(data=request.POST,files=request.FILES,instance=shop)

        if form.is_valid():
            shop = form.save(commit=False)

            shop.owner = request.user

           
            working_days = request.POST.getlist("working_days")
            shop.working_days = working_days

            
            if shop.category != "other":
                shop.custom_category = None

            shop.save()

            return redirect("vendordash")

        print(form.errors)

        return render(request, "edit_shop.html", {"form": form, "shop": shop})

class OfferCreationView(View):
    def get(self,request):
          form=OfferForm()
          return render(request,"create_offer.html",{"form":form})
    def post(self, request):
        form = OfferForm(request.POST, request.FILES)

        if form.is_valid():
            offer = form.save(commit=False)

            offer.shop = Shop.objects.get(owner=request.user)

            offer.created_by = request.user

            offer.is_coupon_based = request.POST.get("is_coupon_based") == "on"
            offer.notify_users = request.POST.get("notify_users") == "on"
            offer.is_active = request.POST.get("is_active") == "on"

            offer.save()

            return redirect("vendordash") 
        
        print(form.errors)

        return render(request, "create_offer.html", {"form": form})


class MyOffersView(View):
     def get(self, request):
        shop = Shop.objects.filter(owner=request.user).first()

        if not shop:
            return render(request, "my_offers.html", {"offers": []})

        filter_type = request.GET.get("filter", "all")

        offers = Offer.objects.filter(shop=shop, is_deleted=False)

        now = timezone.now()

        if filter_type == "active":
            offers = offers.filter(end_date__gte=now)
        elif filter_type == "expired":
            offers = offers.filter(end_date__lt=now)

       
        offer_list = []

        for offer in offers:
            delta = offer.end_date - now
            days = delta.days

            if offer.end_date < now:
                expiry_text = "Expired"
                status = "expired"
            elif days == 0:
                expiry_text = "Expires Today!"
                status = "urgent"
            elif days == 1:
                expiry_text = "Expires Tomorrow"
                status = "warning"
            elif days <= 2:
                expiry_text = f"Expires in {days} days"
                status = "warning"
            else:
                expiry_text = offer.end_date.strftime("%b %d, %Y")
                status = "normal"

            offer_list.append({
                "obj": offer,
                "expiry_text": expiry_text,
                "status": status
            })

        context = {
            "offers": offer_list,
            "filter": filter_type,
            "all_count": Offer.objects.filter(shop=shop,is_deleted=False).count(),
            "active_count": Offer.objects.filter(shop=shop, end_date__gte=now,is_deleted=False).count(),
            "expired_count": Offer.objects.filter(shop=shop, end_date__lt=now,is_deleted=False).count(),
        }

        return render(request, "my_offers.html", context)


class DeleteOfferView(View):
    def get(self,request,**kwargs):
        oid=kwargs.get('oid')
        offer=Offer.objects.get(id=oid,created_by=request.user)
        offer.is_deleted = True
        offer.save()
        next_url = request.GET.get('next')

        if next_url:
            return redirect(next_url)
        return redirect('myoffers')


class UpdateOfferView(View):
    def get(self, request, **kwargs):
        oid = kwargs.get('oid')
        offer = Offer.objects.get(id=oid)

        form = OfferForm(instance=offer)

        return render(request, "update_offer.html", {"form": form, "offer": offer})
    
    def post(self, request, **kwargs):
        oid = kwargs.get('oid')
        offer = Offer.objects.get(id=oid)

        form = OfferForm(request.POST, request.FILES,instance=offer)

        if form.is_valid():
            offer = form.save(commit=False)

            offer.shop = Shop.objects.get(owner=request.user)

         
            offer.created_by = request.user

          
            offer.is_coupon_based = request.POST.get("is_coupon_based") == "on"
            offer.notify_users = request.POST.get("notify_users") == "on"
            offer.is_active = request.POST.get("is_active") == "on"

            offer.save()

            return redirect("vendordash")  


        print(form.errors)

        return render(request, "create_offer.html", {"form": form})
    
from django.utils.timezone import now

VALID_LICENSES = [
    "LIC-123456",
    "LIC-234567",
    "LIC-345678",
    "LIC-456789",
    "LIC-567890",
    "LIC-678901",
    "LIC-789012",

    "IND-112233",
    "IND-223344",
    "IND-334455",
    "IND-445566",
    "IND-556677",
    "IND-667788",
    "IND-778899"
]


def verify_shop(request):
    shop = Shop.objects.get(owner=request.user)

    if request.method == "POST":
        license_number = request.POST.get("license_number")

        if license_number in VALID_LICENSES:
            shop.license_number = license_number
            shop.is_verified = True
            shop.verified_at = now()
            shop.save()

            messages.success(request, "Your shop is successfully verified ")
            return redirect("vendordash")

        else:
            messages.error(request, "Invalid license number ")

    return render(request, "verify_shop.html", {"shop": shop})

# class VendorReviewView(View):
#     def get(self,request):
#         return render(request,"vendor_review.html")
    
@login_required
def redeem_coupon(request):

    coupon = None
    error = None
    success = False

    if request.method == "POST":

        code = request.POST.get("code", "").strip().upper()

        try:
            coupon = Coupon.objects.select_related('shop', 'offer').get(code=code)

           
            if coupon.valid_to <= now():
                error = "Coupon has expired"

            
            elif hasattr(coupon, "is_redeemed") and coupon.is_redeemed:
                error = "Coupon already redeemed"

            else:
            
                success = True

        except Coupon.DoesNotExist:
            error = "Invalid coupon code"

    context = {
        "coupon": coupon,
        "error": error,
        "redeemed": False,
        "success": success
    }

    return render(request, "coupon_redeem.html", context)

@login_required
def confirm_redeem(request, coupon_id):

    coupon = get_object_or_404(Coupon, id=coupon_id)

    if coupon.valid_to <= now():
        messages.error(request, "Coupon expired")
        return redirect('redeem_coupon')

    # mark as redeemed
    coupon.is_redeemed = True
    coupon.save()

    messages.success(request, "Coupon redeemed successfully!")

    return render(request, "coupon_redeem.html", {
    "coupon": coupon,
    "redeemed": True  
    })


from django.db.models import Avg, Count
from django.utils.timezone import now

def vendor_reviews(request):

   
    shop = request.user.shop.first()  

    reviews = Review.objects.filter(shop=shop).select_related('offer', 'user')

    total_reviews = reviews.count()
    avg_rating = round(reviews.aggregate(avg=Avg('rating'))['avg'] or 0, 1)
    stars = get_stars(avg_rating)

    
    show_all = request.GET.get("all") == "true"

   
    offers = (
        reviews.values('offer__id', 'offer__title')
        .annotate(
            review_count=Count('id'),
            avg_rating=Avg('rating')
        )
        .order_by('-review_count')
    )

    offer_reviews = []

    for o in offers:
        offer_id = o['offer__id']

        all_reviews = Review.objects.filter(
            offer_id=offer_id,
            shop=shop
        ).select_related('user').order_by('-created_at')

        reviews_to_show = all_reviews if show_all else all_reviews[:3]

        offer_reviews.append({
            "offer_id": offer_id,
            "title": o['offer__title'],
            "review_count": o['review_count'],
            "reviews": reviews_to_show,
        })

    context = {
        "offer_reviews": offer_reviews,
        "total_reviews": total_reviews,
        "avg_rating": avg_rating,
        "stars": stars,
        "shop": shop,
        "show_all": show_all
    }

    return render(request, "vendor_review.html", context)


class VendorProfileCompleteView(View):

    def get(self, request):
        profile, _ = VendorProfile.objects.get_or_create(user=request.user)

        return render(request, "vendor_profile.html", {
            "profile": profile,
            "user": request.user
        })

    def post(self, request):
        profile, _ = VendorProfile.objects.get_or_create(user=request.user)

        # BASIC
        request.user.first_name = request.POST.get("full_name")
        request.user.phone = request.POST.get("phone")
        request.user.save()

        # LOCATION
        profile.address = request.POST.get("address") or profile.address
        profile.city = request.POST.get("city")

        # BUSINESS
        profile.business_name = request.POST.get("business_name")
        profile.gst_number = request.POST.get("gst_number")

        # IMAGE
        if request.FILES.get("profile_image"):
            profile.profile_image = request.FILES.get("profile_image")

        profile.save()

        return redirect("vendordash")