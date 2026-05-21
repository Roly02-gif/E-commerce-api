import re

from rest_framework import serializers

from shop.models import AddressModel, UserModel


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressModel
        fields = ["street_address", "city", "postal_code", "country"]


class UserSerializer(serializers.ModelSerializer):
    address = AddressSerializer(required=False, allow_null=True)

    class Meta:
        model = UserModel
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "password",
            "address",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )
        if not re.findall("[A-Z]", value):
            raise serializers.ValidationError(
                "Le mot de passe doit contenir au moins une lettre majuscule."
            )
        if not re.findall("[a-z]", value):
            raise serializers.ValidationError(
                "Le mot de passe doit contenir au moins une lettre minuscule."
            )
        return value

    def create(self, validated_data):
        address_data = validated_data.pop("address", None)
        user = UserModel.objects.create_user(**validated_data)
        if address_data:
            AddressModel.objects.create(user=user, **address_data)
        return user

    def update(self, instance, validated_data):
        address_data = validated_data.pop("address", None)
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()

        if address_data is not None:
            address, created = AddressModel.objects.get_or_create(user=instance)
            for attr, value in address_data.items():
                setattr(address, attr, value)
            address.save()

        return instance
