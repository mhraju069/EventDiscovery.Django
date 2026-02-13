import requests
from .models import OTP, User
from datetime import timedelta
from django.utils import timezone
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.contrib.auth.hashers import make_password

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

