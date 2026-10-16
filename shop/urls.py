from django.urls import path
from shop.views import *
from django.conf import settings
from django.conf.urls.static import static


urlpatterns=[
    path('createshop',CreateShopView.as_view(),name="createshop"),
    path('vendordash',VendorDashboardView.as_view(),name="vendordash"),
    path('editshop/<int:sid>',EditShopView.as_view(),name="editshop"),
    path('createoffer',OfferCreationView.as_view(),name="createoffer"),
    path('myoffers',MyOffersView.as_view(),name="myoffers"),
    path('deleteoffer/<int:oid>',DeleteOfferView.as_view(),name="deleteoffer"),
    path('updateoffer/<int:oid>',UpdateOfferView.as_view(),name="updateoffer"),
    path('verifyshop',verify_shop,name="verifyshop"),
    path('vendorreview',vendor_reviews,name="vendorreview"),
    path('redeem_coupon',redeem_coupon,name="redeem_coupon"),
    path('confirm_redeem/<int:coupon_id>/',confirm_redeem,name="confirm_redeem"),
    path("vendor_profile/", VendorProfileCompleteView.as_view(), name="vendor_profile")
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)