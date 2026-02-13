from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework import permissions
from .serializers import *
from .models import *
from .helper import *
from rest_framework_simplejwt.tokens import RefreshToken

# Create your views here.

class SignUpView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name')
        
        if not email or not password or not name:
            return Response({'success': False,'log': 'name, email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({'success': False,'log': 'User with this email already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(email=email, name=name)
        user.set_password(password)
        user.save()
        
        token = RefreshToken.for_user(user)
        return Response({
            'refresh': str(token),
            'access': str(token.access_token),
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_201_CREATED)
        return Response({'success': False,'log': 'User creation failed'}, status=status.HTTP_400_BAD_REQUEST)


class SignInView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if email and password:
            user = User.objects.filter(email=email).first()
            if user and user.check_password(password):

                if not user.is_active:
                    return Response({'success': False,'log': 'User is not active'}, status=status.HTTP_400_BAD_REQUEST)
                if user.block:
                    return Response({'success': False,'log': 'User is blocked'}, status=status.HTTP_400_BAD_REQUEST)

                token = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(token),
                    'access': str(token.access_token),
                    'user': UserProfileSerializer(user).data
                }, status=status.HTTP_201_CREATED)
            
        return Response({'success': False,'log': 'User authentication failed'}, status=status.HTTP_400_BAD_REQUEST)


class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self):
        return User.objects.filter(email=self.request.user.email).first()


class GetOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        task = request.data.get('task', '')
        if not email:
            return Response(
                {"status": False,"log": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        res = send_otp(email, task)

        if res['success']:
            return Response({"status": True, "log": res['log']}, status=status.HTTP_200_OK)
        else:
            return Response({"status": False,"log": res['log']}, status=status.HTTP_400_BAD_REQUEST)


class OtpVerifyView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp_code')

        if not email or not otp_code:
            return Response(
                {"status": False,"log": "Email and OTP code are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = verify_otp(email, otp_code)

        if result['success']:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"status": False,"log": "User not found."}, status=status.HTTP_404_NOT_FOUND)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        else:
            # 403 for lock, 400 for invalid/expired
            status_code = status.HTTP_403_FORBIDDEN if "Too many attempts" in result['log'] else status.HTTP_400_BAD_REQUEST
            return Response({"status": False, "log": result['log']}, status=status_code)


class ResetPassword(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')

        if not email or not new_password :
            return Response(
                {"error": "Email and new password are required."},
                status=400
            )
        
        elif request.user.email != email :
            return Response(
                {"error": "You can only reset your own password."},
                status=403)
        
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            return Response({"status": True, "log": "Password reset successfully"}, status=200)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)


class GetProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = User.objects.filter(email=request.user.email).first()
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


class OAuthLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, provider):

        token = request.query_params.get('token')

        if not token:
            return Response({'success': False,'log': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if provider == 'google':
            user, error = google_login(token)

        elif provider == 'apple':
            user, error = apple_login(token)
        else:
            return Response({'success': False,'log': 'Invalid provider, use google or apple'}, status=status.HTTP_400_BAD_REQUEST)
        
        if user:
            token = RefreshToken.for_user(user)
            return Response({
                'access': str(token.access_token),
                'refresh': str(token),
                'user': UserProfileSerializer(user, context={'request': request}).data
            }, status=status.HTTP_200_OK)
        else:
            return Response({'success': False,'log': error}, status=status.HTTP_400_BAD_REQUEST)