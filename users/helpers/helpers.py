from django.urls import reverse
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str 

User = get_user_model()

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


class UserFromUidService:

    @staticmethod
    def from_uidb64(uidb64):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            return user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None
        