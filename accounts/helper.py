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


def google_login(access_token):

    if not access_token:
        return None, "Access token is required"

    try:
        # Validate token
        token_info_response = requests.get(
            "https://www.googleapis.com/oauth2/v3/tokeninfo",
            params={"access_token": access_token},
            timeout=10
        )

        if token_info_response.status_code != 200:
            return None, "Invalid access token"

        # Get user info
        user_info_response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )

        if user_info_response.status_code != 200:
            return None, "Failed to fetch user info"

        user_data = user_info_response.json()

        email = user_data.get("email")
        name = user_data.get("name")
        profile_image_url = user_data.get("picture")

        if not email:
            return None, "Email not provided by Google"

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "name": name,
                "is_active": True,
                "password": make_password(None),
            },
        )

        # Save profile image
        if created and profile_image_url:
            img_response = requests.get(profile_image_url)
            if img_response.status_code == 200:
                file_name = f"{slugify(name)}-profile.jpg"
                user.image.save(
                    file_name,
                    ContentFile(img_response.content),
                    save=True,
                )

        if getattr(user, "block", False):
            return None, "User account is disabled"

        return user, None

    except Exception as e:
        return None, str(e)


def apple_login(identity_token):
    if not identity_token:
        return None, "Identity token is required"

    try:
        # Fetch Apple's public keys to verify the token
        response = requests.get("https://appleid.apple.com/auth/keys", timeout=10)
        if response.status_code != 200:
            return None, "Failed to fetch Apple public keys"
        
        apple_keys = response.json().get('keys')
        
        # Decode the header to find the correct key
        unverified_header = jwt.get_unverified_header(identity_token)
        kid = unverified_header.get('kid')
        
        key_data = next((k for k in apple_keys if k['kid'] == kid), None)
        if not key_data:
            return None, "Invalid Apple token"
            
        public_key = RSAAlgorithm.from_jwk(json.dumps(key_data))
        
        # Verify and decode the token
        # Note: 'aud' should normally be checked against your client ID.
        # Since it's not provided in the environment yet, we skip aud verification.
        payload = jwt.decode(
            identity_token, 
            public_key, 
            algorithms=['RS256'], 
            options={"verify_aud": False}
        )
        
        email = payload.get("email")
        if not email:
            return None, "Email not provided by Apple"

        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "name": email.split('@')[0], # Fallback name
                "is_active": True,
                "password": make_password(None),
            },
        )

        if getattr(user, "block", False):
            return None, "User account is disabled"

        return user, None

    except Exception as e:
        return None, str(e)
