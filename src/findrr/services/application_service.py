"""High-level application preparation service (Module 5)."""

import logging
from typing import List, Optional

from findrr.db.repository import ApplicationRepository, PostingRepository, ProfileRepository
from findrr.models.application import (
    ApplicationDocument,
    ApplicationRecord,
    ApplicationStatus,
    DocumentType,
    RequirementAnalysisResult,
)
from findrr.services.document_generator import DocumentGenerator
from findrr.services.fact_matcher import FactMatcher

logger = logging.getLogger(__name__)


class ApplicationService:
    """Service orchestrating requirement analysis and tailored document drafting."""

    def __init__(
        self,
        application_repo: ApplicationRepository,
        posting_repo: PostingRepository,
        profile_repo: ProfileRepository,
        document_generator: Optional[DocumentGenerator] = None,
    ):
        self.app_repo = application_repo
        self.posting_repo = posting_repo
        self.profile_repo = profile_repo
        self.doc_generator = document_generator or DocumentGenerator()

    def analyze_requirements(
        self, posting_id: str, profile_id: Optional[str] = None
    ) -> RequirementAnalysisResult:
        """Compare posting requirements against verified candidate profile facts."""
        posting = self.posting_repo.get_posting(posting_id)
        if not posting:
            raise ValueError(f"Job posting {posting_id} not found.")

        pid = profile_id or self._get_default_profile_id()
        profile = self.profile_repo.get_profile(pid)
        if not profile:
            raise ValueError(f"User profile {pid} not found.")

        return FactMatcher.analyze_posting_requirements(posting, profile)

    def prepare_application(
        self,
        posting_id: str,
        profile_id: Optional[str] = None,
        generate_cv: bool = True,
        generate_letter: bool = True,
    ) -> ApplicationRecord:
        """Create an application record and generate tailored CV and cover letter drafts."""
        posting = self.posting_repo.get_posting(posting_id)
        if not posting:
            raise ValueError(f"Job posting {posting_id} not found.")

        pid = profile_id or self._get_default_profile_id()
        profile = self.profile_repo.get_profile(pid)
        if not profile:
            raise ValueError(f"User profile {pid} not found.")

        # Create or fetch existing application record
        app_record = self.app_repo.create_or_get_application(
            profile_id=pid,
            job_posting_id=posting_id,
            initial_status=ApplicationStatus.DISCOVERED,
        )

        analysis = FactMatcher.analyze_posting_requirements(posting, profile)

        if generate_cv:
            cv_draft = self.doc_generator.generate_tailored_cv(
                application_id=app_record.id,
                profile=profile,
                posting=posting,
                analysis=analysis,
            )
            doc_cv = ApplicationDocument(
                application_id=app_record.id,
                document_type=DocumentType.TAILORED_CV,
                file_path=cv_draft.file_path,
                content_text=cv_draft.content_text,
            )
            self.app_repo.save_document(doc_cv)

        if generate_letter:
            letter_draft = self.doc_generator.generate_cover_letter(
                application_id=app_record.id,
                profile=profile,
                posting=posting,
                analysis=analysis,
            )
            doc_letter = ApplicationDocument(
                application_id=app_record.id,
                document_type=DocumentType.COVER_LETTER,
                file_path=letter_draft.file_path,
                content_text=letter_draft.content_text,
            )
            self.app_repo.save_document(doc_letter)

        return app_record

    def list_applications(self, profile_id: Optional[str] = None) -> List[ApplicationRecord]:
        """List application records for a profile."""
        pid = profile_id or self._get_default_profile_id()
        return self.app_repo.list_applications_for_profile(pid)

    def get_application(self, application_id: str) -> Optional[ApplicationRecord]:
        """Fetch application record by ID."""
        return self.app_repo.get_application(application_id)

    def list_documents(self, application_id: str) -> List[ApplicationDocument]:
        """List generated document artifacts for an application."""
        return self.app_repo.list_documents_for_application(application_id)

    def update_status(
        self,
        application_id: str,
        status: ApplicationStatus,
        notes: Optional[str] = None,
    ) -> ApplicationRecord:
        """Update lifecycle status of an application."""
        return self.app_repo.update_status(application_id, status=status, notes=notes)

    def _get_default_profile_id(self) -> str:
        profiles = self.profile_repo.list_profiles()
        if not profiles:
            raise ValueError("No user profiles exist. Complete onboarding first.")
        return profiles[0].id
