from django.shortcuts import render,redirect
from django.contrib import messages
from shop.models import *
from shop.forms import *
from customer.models import *
from users.models import *
from math import radians, cos, sin, asin, sqrt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views import View
from django.db.models import Q
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.db.models import Avg
import random
import string
import qrcode
from io import BytesIO
from django.core.files import File
from datetime import timedelta
from django.utils.timezone import now
import math
from django.views.decorators.cache import never_cache
from django.db.models import Case, When, Value, IntegerField, F

# def calculate_storedis(lat1, lon1, lat2, lon2):
#     R = 6371  # Earth radius in km

#     dlat = math.radians(lat2 - lat1)
#     dlon = math.radians(lon2 - lon1)

#     a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) \
#         * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2

#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
#     return R * c
# # Create your views here.
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

def generate_qr_code(code):
    qr = qrcode.make(code)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    return buffer



def generate_coupon_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=9))

def calculate_distance(lat1, lon1, lat2, lon2):
    if None in [lat1, lon1, lat2, lon2]:
        return None

    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    r = 6371
    return round(r * c, 2)
@login_required
@never_cache
def explore_offers(request):
    offers = Offer.objects.select_related('shop').filter(is_deleted=False)

    user_lat = request.GET.get("lat")
    user_lon = request.GET.get("lon")

    category = request.GET.getlist("category")
    max_distance = request.GET.get("distance")
    min_discount = request.GET.get("discount")
    sort_by = request.GET.get("sort")
    profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    saved_offer_ids = set(
    SavedOffer.objects.filter(user=request.user).values_list('offer_id', flat=True)) if request.user.is_authenticated else set()

    filtered_offers = []

    for offer in offers:
        shop = offer.shop
        offer.is_saved = offer.id in saved_offer_ids
        offer.is_expired_flag = offer.is_expired   
        offer.rating = shop.rating or 0
        
      
        if not shop.latitude or not shop.longitude:
            continue

        
        if user_lat and user_lon:
            distance = calculate_distance(
                float(user_lat),
                float(user_lon),
                shop.latitude,
                shop.longitude
            )
        else:
            distance = None

        # Attach distance
        offer.distance = round(distance, 1) if distance is not None else None
        # print("USER:", user_lat, user_lng)
        # print("SHOP:", shop.latitude, shop.longitude)
        # print("DIST:", distance)

        if max_distance and distance:
            if distance > float(max_distance):
                continue

        if category:
            if shop.category not in category:
                continue

        if min_discount:
            if offer.discount_percentage < int(min_discount):
                continue
        if request.GET.get("verified"):
            if not shop.is_verified:
                continue

        filtered_offers.append(offer)

    # SORTING
    if sort_by == "distance":
        filtered_offers.sort(key=lambda x: x.distance or 999)
    elif sort_by == "discount":
        filtered_offers.sort(key=lambda x: x.discount_percentage, reverse=True)
    else:
        # Recommended (default)
        filtered_offers.sort(
    key=lambda x: (
        x.is_expired_flag,                          
        -(x.discount_percentage or 0),              
        -(x.rating or 0),                           
        x.end_date,                                 
        x.distance if x.distance is not None else 999
    )
)
    offers_count = len(filtered_offers)
    context = {
        "offers": filtered_offers,
        "offers_count": offers_count,
        "profile":profile
    }

    return render(request, "customerhome.html", context)


@login_required
@never_cache
def toggle_save_offer(request, offer_id):
    offer = Offer.objects.get(id=offer_id)

    saved, created = SavedOffer.objects.get_or_create(
        user=request.user,
        offer=offer
    )

    if not created:
        saved.delete()
        return JsonResponse({"status": "removed"})
    
    return JsonResponse({"status": "saved"})

@login_required
@never_cache
def saved_offers_view(request):
    saved_offers = SavedOffer.objects.filter(user=request.user)\
        .select_related('offer', 'offer__shop')\
        .order_by('-created_at')

    # Extract actual offers
    offers = [item.offer for item in saved_offers]
    for item in saved_offers:
        print(item.offer)

    context = {
        "offers": offers,
        "offers_count": len(offers)
    }

    return render(request, "saved_offers.html", context)

@login_required
@never_cache
def search_api(request):
    query = request.GET.get("q", "")

    offers = Offer.objects.filter(
        # is_active=True,
        is_deleted=False
    ).select_related('shop')

    if query:
        offers = offers.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query) |
            Q(shop__shop_name__icontains=query)
        )

    saved_offer_ids = set(
        SavedOffer.objects.filter(user=request.user)
        .values_list('offer_id', flat=True)
    ) if request.user.is_authenticated else set()

    for offer in offers:
        offer.is_saved = offer.id in saved_offer_ids
        offer.distance = None  

    html = render_to_string(
        "components/search_results.html",
        {"offers": offers},
        request=request   
    )

    return JsonResponse({"html": html})

@login_required
@never_cache
def offer_details(request, offer_id):
    offer = get_object_or_404(
        Offer.objects.select_related("shop"),
        id=offer_id,
        is_deleted=False
    )

    shop = offer.shop
    reviews = Review.objects.filter(offer=offer).select_related('user').order_by('-created_at')
    user_review = None

    if request.user.is_authenticated:
        user_review = Review.objects.filter(
            user=request.user,
            offer=offer
        ).first()
    rating_data = reviews.aggregate(avg=Avg("rating"))
    avg_rating = round(rating_data["avg"] or 0, 1)
    stars = get_stars(avg_rating)
    total_reviews = reviews.count()
    user_lat = request.GET.get("lat")
    user_lng = request.GET.get("lng")
    current_time=now()
    related_offers = Offer.objects.filter(
    title__icontains=offer.title,   
    # is_active=True,
    is_deleted=False
    ).exclude(
        shop=offer.shop   
    ).exclude(
        id=offer.id       
    )[:6]
    other_offers = Offer.objects.filter(
    shop=offer.shop,
    is_deleted=False,
    end_date__gt=current_time
    ).exclude(id=offer.id)[:4]

    distance = None
    if user_lat and user_lng and shop.latitude and shop.longitude:
        distance = round(
            calculate_distance(
                float(user_lat),
                float(user_lng),
                shop.latitude,
                shop.longitude
            ), 1
        )

    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedOffer.objects.filter(
            user=request.user,
            offer=offer
        ).exists()

    context = {
        "offers":related_offers,
        "offer": offer,
        "shop": shop,
        "other_offers": other_offers,
        "reviews": reviews,
        "user_review": user_review,
        "avg_rating": float(avg_rating),
        "stars": stars,
        "total_reviews": total_reviews,
        "distance": distance,
        "is_saved": is_saved,
    }

    return render(request, "offer_details.html", context)

@login_required
@never_cache
def add_review(request, offer_id):
    if request.method == "POST":
        error = None
        rating = request.POST.get("rating")
        review_text = request.POST.get("review")

        offer = Offer.objects.get(id=offer_id)
        if not rating:
            error = "Please select a rating."
        elif not review_text or review_text.strip() == "":
            error = "Please write a review."
        else:
            review, created = Review.objects.get_or_create(
                user=request.user,
                offer=offer,
                defaults={
                    "shop": offer.shop,
                    "rating": int(rating),
                    "comment": review_text.strip()
                }
            )

            if not created:
                # ✅ update existing review
                review.rating = int(rating)
                review.comment = review_text.strip()
                review.save()
            return redirect("offer_details", offer_id=offer.id)
    context = {
        "offer": offer,
        "error": error,
        "old_rating": rating,
        "old_review": review_text
    }

    return render(request, "offer_details.html", context)   


from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseNotAllowed
from django.utils.timezone import now
from datetime import timedelta
from django.db import transaction

@login_required
@never_cache
@transaction.atomic
def generate_coupon(request, offer_id):

    if request.method != "POST":
        return HttpResponseNotAllowed(['POST']) 

    offer = Offer.objects.select_for_update().get(id=offer_id)
    qty = int(request.POST.get("quantity", 1))

    if offer.coupons_remaining < qty:
        return redirect('offer_details', offer_id=offer.id)

    existing = Coupon.objects.filter(
    user=request.user,
    offer=offer,
    is_redeemed=False,
    valid_to__gt=now()
    ).first()
    if existing:
        return redirect('coupon_view', coupon_id=existing.id)


    code = generate_coupon_code()

    coupon = Coupon.objects.create(
        user=request.user,
        shop=offer.shop,
        offer=offer,
        code=code,
        quantity=qty,
        valid_from=now(),
        valid_to=now() + timedelta(hours=1)
    )
    
    qr_buffer = generate_qr_code(code)
    coupon.qr_code.save(f"{code}.png", File(qr_buffer), save=True)

    return redirect('coupon_view', coupon_id=coupon.id)

@login_required
@never_cache
def view_coupon(request, coupon_id):
    coupon = Coupon.objects.get(id=coupon_id, user=request.user)

    return render(request,"coupon_view.html", {'coupon': coupon})

@login_required
@never_cache
def nearby_stores(request):

    user_lat = request.GET.get("lat")
    user_lon = request.GET.get("lng")

    shops = Shop.objects.filter(is_active=True)

    shop_list = []

    for shop in shops:
        if shop.latitude and shop.longitude:
            distance = calculate_distance(
                user_lat, user_lon,
                shop.latitude, shop.longitude
            )

            shop.distance = distance
            shop.offer_count = shop.offers.count()

            shop_list.append(shop)

    shop_list.sort(
    key=lambda x: (                                    
        -(x.rating or 0),                                                            
        x.distance if x.distance is not None else 999
    ))
    return render(request, "storelist.html", {
        "shops": shop_list
    })

@login_required
@never_cache
def shop_detail(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    session_key = f"viewed_shop_{shop_id}"

    if not request.session.get(session_key):
        StoreView.objects.create(
            shop=shop,
            user=request.user if request.user.is_authenticated else None
        )
        request.session[session_key] = True

    current_time=now()
    all_offers = Offer.objects.filter(
        shop=shop,

        is_deleted=False
    ).annotate( is_expired_order=Case(
        When(end_date__lt=current_time, then=Value(1)),
        default=Value(0),
        output_field=IntegerField()
    ),

    discount_order=F('discount_percentage'),

    ).order_by(
        'is_expired_order',     
        '-discount_order'       
    )
    total_offers = all_offers.count()

    show_all = request.GET.get('all') == 'true'

    if show_all:
        offers = all_offers
    else:
        offers = all_offers[:3] 


    reviews = Review.objects.filter(shop=shop).order_by('-created_at')

    return render(request, "shop_detail.html", {
        "shop": shop,
        "offers": offers,
        "total_offers": total_offers,
        "reviews": reviews
    })

@login_required
@never_cache
def active_coupons(request):

    coupons = Coupon.objects.select_related('shop', 'offer').filter(
        user=request.user
    )

    active_coupons_list = []

    for coupon in coupons:

        if coupon.valid_to <= now():
            continue   

        remaining_time = coupon.valid_to - now()

        minutes = remaining_time.seconds // 60

        if remaining_time.total_seconds() < 3600:
            coupon.status = "Expiring Soon"
        else:
            coupon.status = "Active"

        coupon.remaining_minutes = minutes

        active_coupons_list.append(coupon)

    context = {
        "coupons": active_coupons_list,
        "coupons_count": len(active_coupons_list)
    }

    return render(request, "active_coupons.html", context)


class CustomerProfileView(View):

    def get(self, request):
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)

        return render(request, "user_profile.html", {
            "profile": profile,
            "user": request.user
        })

    def post(self, request):
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)

        # BASIC
        request.user.first_name = request.POST.get("full_name")
        request.user.phone = request.POST.get("phone")
        request.user.save()

        # LOCATION
        profile.address = request.POST.get("address") or profile.address
        profile.city = request.POST.get("city")

        # BUSINESS
        profile.date_of_birth = request.POST.get("date_of_birth")

        # IMAGE
        if request.FILES.get("profile_image"):
            profile.profile_image = request.FILES.get("profile_image")

        profile.save()

        return redirect("userhome")

