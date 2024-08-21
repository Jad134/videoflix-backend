from django.conf import settings
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

from content.models import Video
from content.serializers import VideoSerializer
from users.models import CustomUser
from .serializers import UserRegistrationSerializer
from rest_framework.permissions import AllowAny
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str  # force_str anstelle von force_text
from django.contrib.auth import authenticate, login
User = get_user_model()
from rest_framework.permissions import IsAuthenticated



class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = False  # Deaktiviert das Benutzerkonto bis zur Aktivierung
            user.save()

            activation_link = request.build_absolute_uri(
                reverse('activate', kwargs={
                    'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                })
            )
            message = render_to_string('activation_email.html', {'activation_link': activation_link, 'user': user})
            send_mail(
                'Activate Your Account',
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.username], #username works as mail in this project
                fail_silently=False,
            )
            return Response({"message": "User created successfully. Check your email to activate your account."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckUsernameView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, username):
        username = username.lower()
        if User.objects.filter(username__iexact=username).exists():
            return Response({"exists": True, "message": "Username is already taken."}, status=status.HTTP_200_OK)
        return Response({"exists": False, "message": "Username is available."}, status=status.HTTP_200_OK)

class ActivateAccountView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return render(request, 'account_activated.html')
        else:
            return HttpResponseBadRequest("Activation link is invalid.")



class UserLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        if user.check_password(password):
            if not user.is_active:
                return Response({"detail": "User account is not activated."}, status=status.HTTP_403_FORBIDDEN)
            
            login(request, user)
            user_data = {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
            return Response({"message": "Login successful.", "user": user_data}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
        


class ResendActivationLinkView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is already activated
        if user.is_active:
            return Response({"detail": "User account is already activated."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate new activation link and send email
        activation_link = request.build_absolute_uri(
            reverse('activate', kwargs={
                'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
        )
        message = render_to_string('activation_email.html', {'activation_link': activation_link, 'user': user})
        send_mail(
            'Activate Your Account',
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.username],  # Use the registered email as recipient
            fail_silently=False,
        )

        return Response({"message": "Activation link resent successfully. Check your email."}, status=status.HTTP_200_OK)
    


class FavoriteVideoToggle(APIView):

    def post(self, request, video_id):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return Response({"error": "Video not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if video in user.favorite_videos.all():
            user.favorite_videos.remove(video)
            return Response({"message": "Video removed from favorites."}, status=status.HTTP_200_OK)
        else:
            user.favorite_videos.add(video)
            return Response({"message": "Video added to favorites."}, status=status.HTTP_200_OK)
        

class UserFavoritesByIdView(APIView):
    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        favorite_videos = user.favorite_videos.all()  # Abrufen der favorisierten Videos
        video_ids = favorite_videos.values_list('id', flat=True)  # Nur die IDs extrahieren
        return Response(video_ids, status=status.HTTP_200_OK)