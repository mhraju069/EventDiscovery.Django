from .models import OTP, User
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_otp(email):
    try:
        user = User.objects.get(email=email)
        otp_obj = OTP.generate_otp(user)
        
        subject = f"Your OTP for email verification"
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]
        
        html_message = render_to_string('email/otp_email.html', {
            'otp': otp_obj.otp,
        })
        plain_message = f"Your OTP for email verification is: {otp_obj.otp}"
        send_mail(subject, plain_message, email_from, recipient_list, html_message=html_message)
        
        return {"status": True, "log": f"OTP sent successfully to {email}"}
    except User.DoesNotExist:
        return {"status": False, "log": "User with this email does not exist."}
    except Exception as e:
        return {"status": False, "log": str(e)}


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

