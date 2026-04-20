from django.contrib.auth import authenticate
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    StudentPublicProfileSerializer,
    StudentSerializer,
    StudentWriteSerializer,
    UpdateMeSerializer,
    user_payload,
)


def _issue_tokens(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


@extend_schema(
    tags=["auth"],
    request=RegisterSerializer,
    responses={201: OpenApiResponse(description="User created + JWT pair issued")},
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.data.get("user") if isinstance(request.data.get("user"), dict) else request.data
        serializer = RegisterSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        body = user_payload(user)
        body.update(_issue_tokens(user))
        return Response(body, status=status.HTTP_201_CREATED)


@extend_schema(tags=["auth"], request=LoginSerializer)
class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        data = request.data.get("user") if isinstance(request.data.get("user"), dict) else request.data
        email = data.get("email")
        password = data.get("password")
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)
        body = user_payload(user)
        body.update(_issue_tokens(user))
        return Response(body)


@extend_schema(
    tags=["auth"],
    request=None,
    responses={204: OpenApiResponse(description="Logged out")},
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request):
        return self.delete(request)


@extend_schema(tags=["auth"], request=UpdateMeSerializer)
class MeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateMeSerializer

    def get(self, request):
        return Response(user_payload(request.user))

    def patch(self, request):
        data = request.data.get("user") if isinstance(request.data.get("user"), dict) else request.data
        serializer = UpdateMeSerializer(request.user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(user_payload(request.user))


@extend_schema(tags=["students"])
class StudentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return User.objects.filter(role=User.Role.STUDENT).prefetch_related("student_groups")

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return StudentWriteSerializer
        return StudentSerializer

    def create(self, request, *args, **kwargs):
        payload = request.data.get("student") if isinstance(request.data.get("student"), dict) else request.data
        serializer = StudentWriteSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(StudentSerializer(student).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        student = self.get_object()
        payload = request.data.get("student") if isinstance(request.data.get("student"), dict) else request.data
        serializer = StudentWriteSerializer(student, data=payload, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StudentSerializer(student).data)

    @extend_schema(
        summary="Public profile for a student",
        responses=StudentPublicProfileSerializer,
    )
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def public_profile(self, request, pk=None):
        try:
            student = User.objects.get(pk=pk, role=User.Role.STUDENT)
        except User.DoesNotExist:
            raise NotFound("Student not found")
        return Response(StudentPublicProfileSerializer(student).data)
