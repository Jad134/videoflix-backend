from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import  SimpleUserSerializer, UserRegistrationSerializer
from rest_framework.permissions import AllowAny
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str 
from django.contrib.auth import login
from django.contrib.auth.forms import SetPasswordForm
from django.contrib import messages

User = get_user_model()


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
            user = UserCreator.create_inactive_user(serializer)
            
            activation_link = ActivationLinkGenerator.build_activation_link(request, user)
            
            EmailSender.send_activation_email(user, activation_link)
            
            return Response({
                "message": "User created successfully. Check your email to activate your account."
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserCreator():
   
   @staticmethod
   def create_inactive_user(serializer):
       
    
       user = serializer.save()
       user.is_active = False
       user.save()
       return user


class ActivationLinkGenerator():

    @staticmethod
    def build_activation_link(request, user):
        return request.build_absolute_uri(
            reverse('activate', kwargs={
                'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
        )


class EmailSender:


    @staticmethod
    def send_activation_email(user, activation_link):
        """
        Send an activation link to the User.

        :param user: The user to whom the activation email is sent.
        :type user: User
        :param activation_link: The activation link contained in the email.
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
            plain_message,  
            settings.DEFAULT_FROM_EMAIL,
            [user.username], 
            fail_silently=False,
            html_message=html_message
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
        user = UserFromUidService.from_uidb64(uidb64)

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
        user = UserFetcher.by_username(username)
        error_response = LoginValidator.validate(user, password)
        if error_response:
         return error_response

        login(request, user)
        
        serialized_user = SimpleUserSerializer(user).data
        return Response({"message": "Login successful.", "user": serialized_user}, status=status.HTTP_200_OK)


class LoginValidator():

    @staticmethod
    def validate(user, password): 
      if not user:
           return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
      if not user.check_password(password):
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
      if not user.is_active:
            return Response({"detail": "User account is not activated."}, status=status.HTTP_403_FORBIDDEN)


class UserFetcher:
    @staticmethod
    def by_username(username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None


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
            
            activation_link = ActivationLinkGenerator.build_activation_link(request, user)
            EmailSender.send_activation_email(user, activation_link)
            
            return Response({"message": "Activation link resent successfully. Check your email."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    
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
        
        reset_link = ResetPasswordLinkGenerator.build_reset_passwort_link(request, user) 
        PasswordResetEmailSender.send(user, reset_link)

        return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)


class ResetPasswordLinkGenerator:

    @staticmethod
    def build_reset_passwort_link(request, user):
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        return request.build_absolute_uri(
            reverse('password_reset_form', kwargs={
                'uidb64': uid,
                'token': token
            })
        )


class PasswordResetEmailSender:
    @staticmethod
    def send(user, reset_link):
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
        user = UserFromUidService.from_uidb64(uidb64)

        if user is not None and default_token_generator.check_token(user, token):
            form = SetPasswordForm(user)
            return render(request, 'password_reset_confirm.html', {'form': form, 'uid': uidb64, 'token': token})
        else:
            messages.error(request, 'The password reset link is invalid or has expired.')
            return redirect('password_reset_request')  

    def post(self, request, uidb64, token):
        user = UserFromUidService.from_uidb64(uidb64)

        if user is not None and default_token_generator.check_token(user, token):
            form = SetPasswordForm(user, data=request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been reset successfully.')
                frontend_url = settings.FRONTEND_URL
                return HttpResponseRedirect(frontend_url) 
            else:
                return render(request, 'password_reset_confirm.html', {'form': form, 'uid': uidb64, 'token': token})
        else:
            messages.error(request, 'The password reset link is invalid or has expired.')
            return redirect('password_reset_request')  
        

class PasswordResetFormView(View):
    def get(self, request, uidb64, token):
        user = UserFromUidService.from_uidb64(uidb64)

        if user is not None and default_token_generator.check_token(user, token):
            form = SetPasswordForm(user)
            return render(request, 'password_reset_confirm.html', {
                'form': form,
                'uid': uidb64,
                'token': token
            })
        else:
            messages.error(request, 'The password reset link is invalid or has expired.')
            return redirect('password_reset_request')
        

class PasswordResetSubmitView(View):
    def post(self, request, uidb64, token):
        user = UserFromUidService.from_uidb64(uidb64)

        if user is not None and default_token_generator.check_token(user, token):
            form = SetPasswordForm(user, data=request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been reset successfully.')
                return redirect(settings.FRONTEND_URL)
            else:
                return render(request, 'password_reset_confirm.html', {
                    'form': form,
                    'uid': uidb64,
                    'token': token
                })
        else:
            messages.error(request, 'The password reset link is invalid or has expired.')
            return redirect('password_reset_request')
        

class UserFromUidService:
    @staticmethod
    def from_uidb64(uidb64):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            return user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None
        









# class FavoriteVideoToggle(APIView):
#     """
#     Toggle a video as a favorite for a user.
#     """

#     def post(self, request, video_id):
#         """
#         Handles adding or removing a video from user's favorites.
#         """
#         user = self._get_user(request.data.get('user_id'))
#         if isinstance(user, Response):
#             return user

#         video = self._get_video(video_id)
#         if isinstance(video, Response):
#             return video

#         return self._toggle_favorite(user, video)

#     def _get_user(self, user_id):
#         """
#         Retrieve a user by ID.
#         """
#         if not user_id:
#             return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             return User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

#     def _get_video(self, video_id):
#         """
#         Retrieve a video by ID.
#         """
#         try:
#             return Video.objects.get(id=video_id)
#         except Video.DoesNotExist:
#             return Response({"error": "Video not found."}, status=status.HTTP_404_NOT_FOUND)

#     def _toggle_favorite(self, user, video):
#         """
#         Toggle the favorite status of a video for a user.
#         """
#         if video in user.favorite_videos.all():
#             user.favorite_videos.remove(video)
#             return Response({"message": "Video removed from favorites."}, status=status.HTTP_200_OK)
#         else:
#             user.favorite_videos.add(video)
#             return Response({"message": "Video added to favorites."}, status=status.HTTP_200_OK)

        

# class UserFavoritesByIdView(APIView):
#     def get(self, request, user_id):
#         try:
#             user = CustomUser.objects.get(id=user_id)
#         except CustomUser.DoesNotExist:
#             return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

#         favorite_videos = user.favorite_videos.all()  
#         video_ids = favorite_videos.values_list('id', flat=True)  
#         return Response(video_ids, status=status.HTTP_200_OK)