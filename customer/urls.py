from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from shop.views import *
from customer.views import *

urlpatterns=[
    path('togglesave/<int:offer_id>/',toggle_save_offer, name='togglesave'),
    path('savedoffers',saved_offers_view,name="savedoffers"),
    path("search-api/",search_api, name="search_api"),
    path("offer/<int:offer_id>/",offer_details, name="offer_details"),
    path("add_review/<int:offer_id>/",add_review,name="add_review"),
    path('coupon_gen/<int:offer_id>/',generate_coupon,name="coupon_gen"),
    path('coupon_view/<int:coupon_id>/',view_coupon,name="coupon_view"),
    path('storelist',nearby_stores,name="storelist"),
    path('shop_detail/<int:shop_id>/',shop_detail,name="shop_detail"),
    path('active_coupons',active_coupons,name="active_coupons"),
    path('customerprofile',CustomerProfileView.as_view(),name="customerprofile")
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)