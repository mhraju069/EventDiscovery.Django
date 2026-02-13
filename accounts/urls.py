from django.urls import path
from .views import *

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signin/', SignInView.as_view(), name='signin'),
    path('get-otp/', GetOtpView.as_view(), name='get-otp'),
    path('verify-otp/', OtpVerifyView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPassword.as_view(), name='reset-password'),
    path('profile/', GetProfileView.as_view(), name='get-profile'),
    path('profile-update/', UserRetrieveUpdateDestroyView.as_view(), name='profile-update'),
    path('oauth/<str:provider>/', OAuthLoginView.as_view(), name='oauth-login'),
]