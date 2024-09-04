from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

from content.models import Video
from content.serializers import VideoSerializer
from users.models import CustomUser
from .serializers import SetNewPasswordSerializer, UserRegistrationSerializer
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
from django.contrib.auth.forms import SetPasswordForm
from django.contrib import messages



class UserRegistrationView(APIView):
    """
    A view to register users.
    """

    def post(self, request):
        """
        Handle user registration and send activation email.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = self._create_inactive_user(serializer)
            activation_link = self._build_activation_link(request, user)
            self._send_activation_email(user, activation_link)
            return Response({"message": "User created successfully. Check your email to activate your account."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _create_inactive_user(self, serializer):
        """
        Create an inactive user from the serializer data.
        
        :param serializer: The validated serializer.
        :type serializer: UserRegistrationSerializer
        :return: The created user.
        :rtype: User
        """
        user = serializer.save()
        user.is_active = False
        user.save()
        return user

    def _build_activation_link(self, request, user):
        """
        Build the activation link for the user.
        
        :param request: The HTTP request object.
        :type request: HttpRequest
        :param user: The user for whom the activation link is being built.
        :type user: User
        :return: The activation link.
        :rtype: str
        """
        return request.build_absolute_uri(
            reverse('activate', kwargs={
                'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
        )

    def _send_activation_email(self, user, activation_link):
        """
        Send an activation email to the user.
        
        :param user: The user to whom the activation email will be sent.
        :type user: User
        :param activation_link: The activation link to include in the email.
        :type activation_link: str
        """
        html_message = render_to_string('activation_email.html', {
            'activation_link': activation_link,
            'user': user
        })
        plain_message = (
            f"Hi {user.username},\n\n"
            f"Thank you for registering with us. To activate your account, please click the link below:\n"
            f"{activation_link}\n\n"
            f"If you did not create this account, you can safely ignore this email."
        )

        send_mail(
            'Activate Your Account',
            plain_message,  # Text-Inhalt als Fallback
            settings.DEFAULT_FROM_EMAIL,
            [user.username],  # E-Mail-Adresse des Benutzers
            fail_silently=False,
            html_message=html_message  # HTML-Inhalt
        )


class CheckUsernameView(APIView):
    """
    Checks if the username is already axist
    """
    permission_classes = [AllowAny]
    def get(self, request, username):
        username = username.lower()
        if User.objects.filter(username__iexact=username).exists():
            return Response({"exists": True, "message": "Username is already taken."}, status=status.HTTP_200_OK)
        return Response({"exists": False, "message": "Username is available."}, status=status.HTTP_200_OK)

class ActivateAccountView(APIView):
    """
    Activates the user's account after clicking the email link to complete registration
    """
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
    """
    Logs the user in and returns the user data.
    """

    def post(self, request):
        """
        Handle user login.
        """
        username = request.data.get('username')
        password = request.data.get('password')
        user = self._get_user(username)
        if isinstance(user, Response):
            return user

        if not user.check_password(password):
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({"detail": "User account is not activated."}, status=status.HTTP_403_FORBIDDEN)

        login(request, user)
        return Response({"message": "Login successful.", "user": self._get_user_data(user)}, status=status.HTTP_200_OK)

    def _get_user(self, username):
        """
        Retrieve user by username.
        """
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

    def _get_user_data(self, user):
        """
        Retrieve user data for response.
        """
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

        


class ResendActivationLinkView(APIView):
    """
    Send a new Activation Link to the Email
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')

        try:
            user = User.objects.get(username=username)
            if user.is_active:
                return Response({"detail": "User account is already activated."}, status=status.HTTP_400_BAD_REQUEST)
            
            activation_link = request.build_absolute_uri(
                reverse('activate', kwargs={'uidb64': urlsafe_base64_encode(force_bytes(user.pk)), 
                                            'token': default_token_generator.make_token(user)}))
            html_message = render_to_string('activation_email.html', {'activation_link': activation_link, 'user': user})
            plain_message = (f"Hi {user.username},\n\nThank you for registering with us. To activate your account, "
                             f"please click the link below:\n{activation_link}\n\nIf you did not create this account, you can safely ignore this email.")
            send_mail('Activate Your Account', plain_message, settings.DEFAULT_FROM_EMAIL, [user.username], 
                      fail_silently=False, html_message=html_message)
            return Response({"message": "Activation link resent successfully. Check your email."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    


class FavoriteVideoToggle(APIView):
    """
    Toggle a video as a favorite for a user.
    """

    def post(self, request, video_id):
        """
        Handles adding or removing a video from user's favorites.
        """
        user = self._get_user(request.data.get('user_id'))
        if isinstance(user, Response):
            return user

        video = self._get_video(video_id)
        if isinstance(video, Response):
            return video

        return self._toggle_favorite(user, video)

    def _get_user(self, user_id):
        """
        Retrieve a user by ID.
        """
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    def _get_video(self, video_id):
        """
        Retrieve a video by ID.
        """
        try:
            return Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return Response({"error": "Video not found."}, status=status.HTTP_404_NOT_FOUND)

    def _toggle_favorite(self, user, video):
        """
        Toggle the favorite status of a video for a user.
        """
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
    

class PasswordResetRequestView(APIView):
    """
    Sends an email with a link to reset the password.
    """
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Email address not found."}, status=status.HTTP_400_BAD_REQUEST)
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = request.build_absolute_uri(
            reverse('password_reset_confirm', kwargs={
                'uidb64': uid,
                'token': token
            })
        )
        self._send_reset_email(user, reset_link)
        return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)

    def _send_reset_email(self, user, reset_link):
        html_message = render_to_string('password_reset_email.html', {
            'reset_link': reset_link,
            'user': user
        })
        plain_message = (
            f"Hi {user.username},\n\n"
            f"To reset your password, please click the link below:\n"
            f"{reset_link}\n\n"
            f"If you did not request this, please ignore this email."
        )
        send_mail(
            'Password Reset Request',
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=html_message
        )


class PasswordResetConfirmView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            form = SetPasswordForm(user)
            return render(request, 'password_reset_confirm.html', {'form': form, 'uid': uidb64, 'token': token})
        else:
            messages.error(request, 'The password reset link is invalid or has expired.')
            return redirect('password_reset_request')  # URL zur Seite zur Anforderung eines neuen Links oder zur Anmeldung

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            form = SetPasswordForm(user, data=request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been reset successfully.')
                # Weiterleiten zur gewünschten URL Ihrer Frontend-Anwendung
                frontend_url = settings.FRONTEND_URL
                return HttpResponseRedirect(frontend_url)  # Ersetzen Sie die URL entsprechend
            else:
                return render(request, 'password_reset_confirm.html', {'form': form, 'uid': uidb64, 'token': token})
        else:
            messages.error(request, 'The password reset link is invalid or has expired.')
            return redirect('password_reset_request')  # URL zur Seite zur Anforderung eines neuen Links oder zur Anmeldung