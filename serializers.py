from rest_framework import serializers
from django.contrib.auth import authenticate
from .app.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["fname", "lname", "role", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            fname=validated_data["fname"],
            password=validated_data["password"]
        )
        user.last_name = validated_data.get("lname", "")
        user.role = validated_data.get("role", "worker")
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    fname = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(fname=data.get("fname"), password=data.get("password"))
        if not user:
            raise serializers.ValidationError("Identifiants invalides")
        data["user"] = user
        return data



"""class LoginSerializer(serializers.Serializer):
    fname = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(fname=data.get("fname"), password=data.get("password"))
        if not user:
            raise serializers.ValidationError("Identifiants invalides")
        data["user"] = user
        return data
"""