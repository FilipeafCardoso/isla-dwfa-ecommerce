from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView


class MeSerializer(serializers.Serializer):
    """Formato da resposta de GET /api/v1/me/ (documentação no Swagger)."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    groups = serializers.ListField(child=serializers.CharField())


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MeSerializer  # drf-spectacular usa para o schema

    @extend_schema(responses=MeSerializer)
    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "groups": list(user.groups.values_list("name", flat=True)),
            }
        )


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """Login com limite de tentativas (scope "auth") contra força bruta."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"
