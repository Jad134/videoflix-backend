from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes, force_str
from content.serializers import VideoSerializer
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)


    class Meta:
        model = User
        fields = ('username', 'password', 'email','first_name', 'last_name', 'custom', 'address', 'phone')

        
    def create(self, validated_data):
        custom = validated_data.pop('custom', '')
        address = validated_data.pop('address', '')
        phone = validated_data.pop('phone', '')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            custom=custom,
            address=address,
            phone=phone
        )
        return user
    
class SetNewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    uidb64 = serializers.CharField()
    token = serializers.CharField()

    def validate(self, data):
        uidb64 = data.get('uidb64')
        token = data.get('token')
        new_password = data.get('new_password')

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            raise serializers.ValidationError('Invalid token or user.')

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError('Invalid token or user.')

        return {
            'user': user,
            'new_password': new_password
        }