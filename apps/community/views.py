from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status as drf_status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import (
    MAX_IMAGES_PER_REPORT,
    IssueReport,
    IssueReportImage,
    NewsletterEntry,
)
from .serializers import IssueReportSerializer, NewsletterEntrySerializer

_STATUS_NAME_TO_VALUE = {
    "open": IssueReport.Status.OPEN,
    "in_progress": IssueReport.Status.IN_PROGRESS,
    "resolved": IssueReport.Status.RESOLVED,
}


def _unwrap(data, prefix: str) -> dict:
    nested = data.get(prefix)
    if isinstance(nested, dict):
        return nested
    bracket = f"{prefix}["
    unwrapped = {
        k[len(bracket):-1]: v
        for k, v in data.items()
        if k.startswith(bracket) and k.endswith("]")
    }
    return unwrapped if unwrapped else data


def _is_admin(user) -> bool:
    return getattr(user, "role", None) == "admin"


@extend_schema(
    tags=["newsletter"],
    parameters=[OpenApiParameter("limit", int, description="List cap (default 25, max 100).")],
)
class NewsletterEntryViewSet(viewsets.ModelViewSet):
    serializer_class = NewsletterEntrySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = NewsletterEntry.objects.select_related("author").order_by(
            "-published_at", "-created_at"
        )
        if self.action == "list":
            qs = qs[: self._list_limit()]
        return qs

    def _list_limit(self) -> int:
        try:
            raw = int(self.request.query_params.get("limit", 0))
        except (TypeError, ValueError):
            raw = 0
        if raw <= 0:
            return 25
        return min(raw, 100)

    def create(self, request, *args, **kwargs):
        if not _is_admin(request.user):
            raise PermissionDenied("Only admins can publish newsletter entries")
        payload = request.data.get("newsletter_entry", request.data)
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save(author=request.user)
        return Response(
            self.get_serializer(entry).data, status=drf_status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        entry = self.get_object()
        if entry.author_id != request.user.id:
            raise PermissionDenied("Only the publication creator can perform this action")
        payload = request.data.get("newsletter_entry", request.data)
        serializer = self.get_serializer(entry, data=payload, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        entry = self.get_object()
        if entry.author_id != request.user.id:
            raise PermissionDenied("Only the publication creator can perform this action")
        entry.delete()
        return Response(status=drf_status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["issue_reports"],
    parameters=[
        OpenApiParameter("status", str, enum=["open", "in_progress", "resolved", "all"]),
        OpenApiParameter("q", str, description="Text search in title/description."),
        OpenApiParameter("page", int),
        OpenApiParameter("per_page", int, description="Max 50, default 10."),
    ],
)
class IssueReportViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = IssueReportSerializer
    permission_classes = [IsAuthenticated]

    def _filter_queryset(self):
        params = self.request.query_params
        qs = (
            IssueReport.objects.select_related("reporter")
            .prefetch_related("images")
            .order_by("-created_at")
        )

        status_filter = params.get("status") or ""
        if status_filter == "all":
            pass
        elif status_filter in _STATUS_NAME_TO_VALUE:
            qs = qs.filter(status=_STATUS_NAME_TO_VALUE[status_filter])
        else:
            qs = qs.filter(status=IssueReport.Status.OPEN)

        q = params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

        return qs

    def get_queryset(self):
        return self._filter_queryset()

    def list(self, request, *args, **kwargs):
        qs = self._filter_queryset()
        try:
            per_page = int(request.query_params.get("per_page", 0))
        except (TypeError, ValueError):
            per_page = 0
        per_page = min(per_page, 50)
        if per_page <= 0:
            per_page = 10

        try:
            page = int(request.query_params.get("page", 0))
        except (TypeError, ValueError):
            page = 0
        if page <= 0:
            page = 1

        total_count = qs.count()
        total_pages = (total_count + per_page - 1) // per_page
        items = qs[(page - 1) * per_page : page * per_page]

        return Response(
            {
                "items": self.get_serializer(items, many=True).data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_count": total_count,
                    "total_pages": total_pages,
                },
            }
        )

    def create(self, request, *args, **kwargs):
        payload = _unwrap(request.data, "issue_report")
        images = request.FILES.getlist("images") or request.FILES.getlist(
            "issue_report[images][]"
        )
        if len(images) > MAX_IMAGES_PER_REPORT:
            raise ValidationError(
                {"images": [f"must include at most {MAX_IMAGES_PER_REPORT} images"]}
            )

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            report = serializer.save(reporter=request.user)
            for uploaded in images:
                image = IssueReportImage(
                    issue_report=report,
                    image=uploaded,
                    content_type=getattr(uploaded, "content_type", "") or "",
                    byte_size=uploaded.size,
                )
                try:
                    image.full_clean()
                except DjangoValidationError as exc:
                    raise ValidationError({"images": exc.messages})
                image.save()

        return Response(
            self.get_serializer(report).data, status=drf_status.HTTP_201_CREATED
        )
