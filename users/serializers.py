from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'custom', 'address', 'phone')

        
    def create(self, validated_data):
        custom = validated_data.pop('custom', '')
        address = validated_data.pop('address', '')
        phone = validated_data.pop('phone', '')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            custom=custom,
            address=address,
            phone=phone
        )
        return user