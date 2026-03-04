from django.urls import path
from .views import *

urlpatterns = [
    path('get-otp/', GetOtpView.as_view(), name='get-otp'),
    path('verify-otp/', OtpVerifyView.as_view(), name='verify-otp'),
    path('profile/', UserRetrieveUpdateDestroyView.as_view(), name='profile'),
    path('', FirebaseAuthenticationView.as_view(), name='firebase-auth'),
]