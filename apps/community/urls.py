from rest_framework.routers import DefaultRouter

from .views import IssueReportViewSet, NewsletterEntryViewSet

router = DefaultRouter()
router.register(r"newsletter_entries", NewsletterEntryViewSet, basename="newsletter-entry")
router.register(r"issue_reports", IssueReportViewSet, basename="issue-report")

urlpatterns = router.urls
