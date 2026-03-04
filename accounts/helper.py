import requests
from .models import OTP, User
from datetime import timedelta
from django.utils import timezone
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.contrib.auth.hashers import make_password
import jwt
import json
from jwt.algorithms import RSAAlgorithm

def verify_otp(email, otp_code):
    try:
        otp_obj = OTP.objects.filter(user__email=email).latest('created_at')
    except OTP.DoesNotExist:
        return {"status": False, "message": "Invalid OTP or email."}

    # Check expiry
    if otp_obj.is_expired():
        return {"status": False, "message": "OTP has expired."}

    # Verify OTP
    if otp_obj.otp != otp_code:
        return {"status": False, "message": "Invalid OTP."}

    # OTP verified, activate user & delete OTP
    user = otp_obj.user
    user.is_active = True
    user.save()
    otp_obj.delete()

    return {"status": True, "message": "OTP verified successfully."}

