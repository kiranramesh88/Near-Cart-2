from django.shortcuts import render,redirect
from users.forms import *
from users.models import *
from shop.models import *
from django.views import View
from django.core.mail import send_mail
from django.contrib.auth import login,authenticate,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.conf import settings as django_settings
from django.utils.timezone import now



# Create your views here.


def send_otp(user_instance):
    user_instance.generate_otp()
    send_mail(
        subject="Django App Authentication OTP",
        message=f"Your generated OTP is : {user_instance.otp}",
        from_email=django_settings.EMAIL_HOST_USER,
        recipient_list=[user_instance.email],
        fail_silently=True

    )
    
class LandingView(View):
    def get(self,request):
        offers = (
            Offer.objects
            .select_related("shop")
            .filter(is_deleted=False, end_date__gt=now())  # not expired
            .order_by("-created_at")[:4]  # latest 4
        )
        return render(request,"landing.html",{"offers":offers})
    
class trendingOfferview(View):
    def get(self,request):
        return render(request,"trending_offr.html")

class UserRegistrationView(View):

    def get(self, request):

        form = UserRegistrationForm()

        return render(request, "vendor_reg.html", {"form": form})


    def post(self, request):

        form = UserRegistrationForm(request.POST)

        if form.is_valid():

            # check location permission
            if not request.POST.get("latitude"):

                form.add_error(None, "Please allow location access")

                messages.error(request, "Please allow location access")

                return render(request, "vendor_reg.html", {"form": form})


            user = form.save(commit=False)

            # set username = email (required internally by Django)
            # get role from template (customer/vendor)
            role = request.POST.get("role")

            user.role = role
            print()
            # location
            user.latitude = request.POST.get("latitude")
            user.longitude = request.POST.get("longitude")

            user.save()

            send_otp(user)

            request.session["email"] = user.email

            return redirect("verify_otp")

        print(form.errors)
        messages.warning(request, "Enter valid details")

        return render(request, "vendor_reg.html",{"form": form})

class VerifyOtpview(View):
    def get(slef,request):
        return render(request,"verify_otp.html")
    def post(self,request):
        otpval=request.POST.get('otpnum')
        try:
            user_instance=User.objects.get(otp=otpval)
            user_instance.is_verified=True
            user_instance.is_active=True
            user_instance.otp=None
            user_instance.save()
            messages.success(request,"User Registration Completed!!")
            return redirect('userlogin')
           
        except:
            messages.warning(request,"Invalid otp")
            return redirect('verify_otp')
        
class userLoginView(View):
    def get(self,request):
        form=UserLoginFrom()
        return render(request,"userlogin.html",{"data":form})
    def post(self,request):
        form_data=UserLoginFrom(data=request.POST)
        if form_data.is_valid():
            username=form_data.cleaned_data.get('username')
            password=form_data.cleaned_data.get('password')
            user=authenticate(request,username=username,password=password)
            if user:
                login(request,user)
                messages.success(request,"Login Successfull")
                if user.role=="Vendor":
                    if Shop.objects.filter(owner=user).exists():
                        return redirect("vendordash")
                    else:
                        return redirect("vendorhome")
                elif user.role=="Customer":
                    return redirect("userhome")
        messages.warning(request,"Invalid credentials")
        return render(request,"userlogin.html",{"form":form_data})


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class UserHomeView(View):
    def get(self,request):
        user=request.user
        return render(request,"userhome.html",{"data":user})


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class vendorHomeView(View):
    def get(self,request):
        user=request.user
        return render(request,"vendor-home.html",{"data":user})
    
class LogoutView(View):
    def get(self,request):
        logout(request)
        messages.success(request,"You have been logged out.")
        return redirect('userlogin')
    
        