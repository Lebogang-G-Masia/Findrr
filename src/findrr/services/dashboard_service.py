"""Dashboard metrics aggregation service (Module 7, FR-025)."""

import logging
from typing import Any, Dict, List, Optional

from findrr.db.repository import ApplicationRepository, PostingRepository, ProfileRepository
from findrr.models.application import DashboardMetrics

logger = logging.getLogger(__name__)


class DashboardService:
    """Aggregates employment search and application pipeline metrics."""

    def __init__(
        self,
        application_repo: ApplicationRepository,
        posting_repo: PostingRepository,
        profile_repo: ProfileRepository,
    ):
        self.app_repo = application_repo
        self.posting_repo = posting_repo
        self.profile_repo = profile_repo

    def get_dashboard_metrics(self, profile_id: Optional[str] = None) -> DashboardMetrics:
        """Calculate complete dashboard and pipeline performance metrics (FR-025)."""
        pid = profile_id or self._get_default_profile_id()

        # 1. Search & Discovery Metrics
        search_data = self.posting_repo.get_search_metrics()

        # 2. Application Pipeline Metrics
        pipeline_counts = self.app_repo.get_pipeline_summary(pid)

        # Submitted = Applied + Interviewing + Offered + Rejected
        submitted_count = (
            pipeline_counts.get("APPLIED", 0)
            + pipeline_counts.get("INTERVIEWING", 0)
            + pipeline_counts.get("OFFERED", 0)
            + pipeline_counts.get("REJECTED", 0)
        )

        interview_count = pipeline_counts.get("INTERVIEWING", 0) + pipeline_counts.get("OFFERED", 0)
        interview_rate = (interview_count / submitted_count * 100.0) if submitted_count > 0 else 0.0
        offer_count = pipeline_counts.get("OFFERED", 0)
        offer_rate = (offer_count / submitted_count * 100.0) if submitted_count > 0 else 0.0

        # 3. Recent Application Activity
        apps = self.app_repo.list_applications_for_profile(pid)
        recent_activity: List[Dict[str, Any]] = []
        for app in apps[:5]:
            posting = self.posting_repo.get_posting(app.job_posting_id)
            recent_activity.append(
                {
                    "application_id": app.id,
                    "title": posting.title if posting else "Unknown Role",
                    "company": posting.company if posting else "Unknown Company",
                    "status": app.status.value,
                    "applied_at": (
                        app.applied_at.strftime("%Y-%m-%d") if app.applied_at else "Not submitted"
                    ),
                    "updated_at": app.updated_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

        return DashboardMetrics(
            total_postings=search_data.get("total_postings", 0),
            active_postings=search_data.get("active_postings", 0),
            closed_postings=search_data.get("closed_postings", 0),
            unique_companies=search_data.get("unique_companies", 0),
            pipeline_counts=pipeline_counts,
            submitted_count=submitted_count,
            interview_rate_pct=round(interview_rate, 1),
            offer_rate_pct=round(offer_rate, 1),
            top_companies=search_data.get("top_companies", []),
            term_yield=search_data.get("term_yield", []),
            recent_activity=recent_activity,
        )

    def _get_default_profile_id(self) -> str:
        profiles = self.profile_repo.list_profiles()
        if not profiles:
            raise ValueError("No user profiles exist. Complete onboarding first.")
        return profiles[0].id
