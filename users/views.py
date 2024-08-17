from django.conf import settings
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
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
            return Response({"message": "Login successful."}, status=status.HTTP_200_OK)
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