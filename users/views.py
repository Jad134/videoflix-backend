from django.conf import settings
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from users.helpers.helpers import ActivationLinkGenerator, EmailSender, LoginValidator, PasswordResetEmailSender, ResetPasswordLinkGenerator, UserCreator, UserFetcher, UserFromUidService
from .serializers import  SimpleUserSerializer, UserRegistrationSerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth.tokens import default_token_generator
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
        
