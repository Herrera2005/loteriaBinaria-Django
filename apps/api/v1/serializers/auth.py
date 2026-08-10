from __future__ import annotations

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from apps.accounts.policies import (
    assigned_role_codes,
    is_operational_user,
)


User = get_user_model()


INVALID_CREDENTIALS_MESSAGE = (
    "Las credenciales ingresadas no son válidas."
)

ACCOUNT_DISABLED_MESSAGE = (
    "La cuenta no se encuentra habilitada."
)


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(
        max_length=254,
        trim_whitespace=True,
    )
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        identifier = attrs["identifier"].strip()
        password = attrs["password"]

        if not identifier:
            raise serializers.ValidationError(
                {
                    "identifier": [
                        "Ingrese su usuario o correo electrónico."
                    ]
                }
            )

        user = self._find_user(identifier)

        if user is None:
            raise serializers.ValidationError(
                {
                    "identifier": [
                        INVALID_CREDENTIALS_MESSAGE
                    ]
                }
            )

        authenticated_user = authenticate(
            request=self.context.get("request"),
            username=user.username,
            password=password,
        )

        if authenticated_user is None:
            # Django puede rechazar aquí tanto credenciales incorrectas
            # como cuentas con is_active=False.
            #
            # Si la contraseña realmente pertenece al usuario pero la cuenta
            # está deshabilitada, devolvemos el mensaje de estado operativo.
            if user.check_password(password) and not is_operational_user(user):
                raise serializers.ValidationError(
                    {
                        "identifier": [
                            ACCOUNT_DISABLED_MESSAGE
                        ]
                    }
                )

            raise serializers.ValidationError(
                {
                    "identifier": [
                        INVALID_CREDENTIALS_MESSAGE
                    ]
                }
            )

        if not is_operational_user(authenticated_user):
            raise serializers.ValidationError(
                {
                    "identifier": [
                        ACCOUNT_DISABLED_MESSAGE
                    ]
                }
            )

        attrs["user"] = authenticated_user

        return attrs

    @staticmethod
    def _find_user(identifier):
        user = (
            User.objects
            .filter(username__iexact=identifier)
            .first()
        )

        if user is not None:
            return user

        return (
            User.objects
            .filter(email__iexact=identifier)
            .first()
        )


class AuthUserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "roles",
        )
        read_only_fields = fields

    def get_roles(self, obj):
        return list(
            assigned_role_codes(obj)
        )