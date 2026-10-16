from django.urls import path
from users.views import *
from shop.views import *
from customer.views import *

urlpatterns=[
    path('userreg',UserRegistrationView.as_view(),name="userreg"),
    path('verifyotp',VerifyOtpview.as_view(),name="verify_otp"),
    path('userlogin',userLoginView.as_view(),name="userlogin"),
    path('userhome',explore_offers,name="userhome"),
    path('trending',trendingOfferview.as_view(),name="trending"),
    path('vendorhome',vendorHomeView.as_view(),name="vendorhome"),
    path('logout',LogoutView.as_view(),name="logout")
]