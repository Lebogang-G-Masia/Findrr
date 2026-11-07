"""Database repositories for profiles, generalized titles, and search configurations."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from findrr.models.application import (
    ApplicationDocument,
    ApplicationRecord,
    ApplicationStatus,
    DocumentType,
)
from findrr.models.posting import JobPosting, PostingAvailability
from findrr.models.profile import (
    ProfileCategory,
    ProfileEntry,
    ProvenanceSource,
    UserProfile,
)
from findrr.models.search_config import (
    RemotePreference,
    SearchConfiguration,
    SeniorityLevel,
)
from findrr.models.title import GeneralizedTitle


def _parse_timestamp(val: Any) -> datetime:
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            return datetime.strptime(val, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


class ProfileRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save_profile(self, profile: UserProfile) -> UserProfile:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO user_profiles (
                    id, full_name, email, phone, location,
                    professional_summary, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    full_name = excluded.full_name,
                    email = excluded.email,
                    phone = excluded.phone,
                    location = excluded.location,
                    professional_summary = excluded.professional_summary,
                    updated_at = excluded.updated_at
                """,
                (
                    profile.id,
                    profile.full_name,
                    profile.email,
                    profile.phone,
                    profile.location,
                    profile.professional_summary,
                    profile.created_at.isoformat(),
                    profile.updated_at.isoformat(),
                ),
            )
            if profile.entries:
                self.save_entries(profile.entries)
        return self.get_profile(profile.id) or profile

    def get_profile(self, profile_id: str) -> Optional[UserProfile]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, full_name, email, phone, location,
                   professional_summary, created_at, updated_at
            FROM user_profiles WHERE id = ?
            """,
            (profile_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        entries = self.get_entries(profile_id)
        return UserProfile(
            id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            phone=row["phone"],
            location=row["location"],
            professional_summary=row["professional_summary"],
            created_at=_parse_timestamp(row["created_at"]),
            updated_at=_parse_timestamp(row["updated_at"]),
            entries=entries,
        )

    def list_profiles(self) -> List[UserProfile]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM user_profiles ORDER BY created_at DESC")
        rows = cursor.fetchall()
        profiles = []
        for row in rows:
            p = self.get_profile(row["id"])
            if p:
                profiles.append(p)
        return profiles

    def delete_profile(self, profile_id: str) -> bool:
        with self.conn:
            cursor = self.conn.execute("DELETE FROM user_profiles WHERE id = ?", (profile_id,))
            return cursor.rowcount > 0

    def save_entries(self, entries: List[ProfileEntry]) -> None:
        with self.conn:
            for entry in entries:
                meta = json.dumps(entry.metadata_json) if entry.metadata_json is not None else None
                self.conn.execute(
                    """
                    INSERT INTO profile_entries (
                        id, profile_id, category, title, organization, start_date, end_date,
                        description, metadata_json, source, collection_date, is_verified
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        category = excluded.category,
                        title = excluded.title,
                        organization = excluded.organization,
                        start_date = excluded.start_date,
                        end_date = excluded.end_date,
                        description = excluded.description,
                        metadata_json = excluded.metadata_json,
                        source = excluded.source,
                        is_verified = excluded.is_verified
                    """,
                    (
                        entry.id,
                        entry.profile_id,
                        entry.category.value,
                        entry.title,
                        entry.organization,
                        entry.start_date,
                        entry.end_date,
                        entry.description,
                        meta,
                        entry.source.value,
                        entry.collection_date.isoformat(),
                        1 if entry.is_verified else 0,
                    ),
                )

    def get_entries(self, profile_id: str) -> List[ProfileEntry]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, profile_id, category, title, organization, start_date, end_date,
                   description, metadata_json, source, collection_date, is_verified
            FROM profile_entries
            WHERE profile_id = ?
            ORDER BY collection_date ASC
            """,
            (profile_id,),
        )
        rows = cursor.fetchall()
        entries: List[ProfileEntry] = []
        for row in rows:
            meta = json.loads(row["metadata_json"]) if row["metadata_json"] else None
            entries.append(
                ProfileEntry(
                    id=row["id"],
                    profile_id=row["profile_id"],
                    category=ProfileCategory(row["category"]),
                    title=row["title"],
                    organization=row["organization"],
                    start_date=row["start_date"],
                    end_date=row["end_date"],
                    description=row["description"],
                    metadata_json=meta,
                    source=ProvenanceSource(row["source"]),
                    collection_date=_parse_timestamp(row["collection_date"]),
                    is_verified=bool(row["is_verified"]),
                )
            )
        return entries

    def update_entry_verification(self, entry_id: str, is_verified: bool) -> bool:
        with self.conn:
            cursor = self.conn.execute(
                "UPDATE profile_entries SET is_verified = ? WHERE id = ?",
                (1 if is_verified else 0, entry_id),
            )
            return cursor.rowcount > 0

    def delete_entry(self, entry_id: str) -> bool:
        with self.conn:
            cursor = self.conn.execute("DELETE FROM profile_entries WHERE id = ?", (entry_id,))
            return cursor.rowcount > 0


class TitleRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save_title(self, title: GeneralizedTitle) -> GeneralizedTitle:
        with self.conn:
            if title.is_active:
                # Deactivate previously active titles for this profile
                self.conn.execute(
                    "UPDATE generalized_titles SET is_active = 0 WHERE profile_id = ?",
                    (title.profile_id,),
                )
            self.conn.execute(
                """
                INSERT INTO generalized_titles (
                    id, profile_id, primary_title, rationale,
                    supporting_skills, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    primary_title = excluded.primary_title,
                    rationale = excluded.rationale,
                    supporting_skills = excluded.supporting_skills,
                    is_active = excluded.is_active
                """,
                (
                    title.id,
                    title.profile_id,
                    title.primary_title,
                    title.rationale,
                    json.dumps(title.supporting_skills),
                    1 if title.is_active else 0,
                    title.created_at.isoformat(),
                ),
            )
        return title

    def get_active_title(self, profile_id: str) -> Optional[GeneralizedTitle]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, profile_id, primary_title, rationale,
                   supporting_skills, is_active, created_at
            FROM generalized_titles
            WHERE profile_id = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (profile_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        skills = json.loads(row["supporting_skills"]) if row["supporting_skills"] else []
        return GeneralizedTitle(
            id=row["id"],
            profile_id=row["profile_id"],
            primary_title=row["primary_title"],
            rationale=row["rationale"],
            supporting_skills=skills,
            is_active=bool(row["is_active"]),
            created_at=_parse_timestamp(row["created_at"]),
        )

    def list_titles(self, profile_id: str) -> List[GeneralizedTitle]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, profile_id, primary_title, rationale,
                   supporting_skills, is_active, created_at
            FROM generalized_titles
            WHERE profile_id = ?
            ORDER BY created_at DESC
            """,
            (profile_id,),
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            skills = json.loads(row["supporting_skills"]) if row["supporting_skills"] else []
            result.append(
                GeneralizedTitle(
                    id=row["id"],
                    profile_id=row["profile_id"],
                    primary_title=row["primary_title"],
                    rationale=row["rationale"],
                    supporting_skills=skills,
                    is_active=bool(row["is_active"]),
                    created_at=_parse_timestamp(row["created_at"]),
                )
            )
        return result


class SearchConfigRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save_configuration(self, config: SearchConfiguration) -> SearchConfiguration:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO search_configurations (
                    id, profile_id, target_locations, remote_preference, seniority_level,
                    min_compensation, currency, min_results_per_title, max_results_per_title,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(profile_id) DO UPDATE SET
                    target_locations = excluded.target_locations,
                    remote_preference = excluded.remote_preference,
                    seniority_level = excluded.seniority_level,
                    min_compensation = excluded.min_compensation,
                    currency = excluded.currency,
                    min_results_per_title = excluded.min_results_per_title,
                    max_results_per_title = excluded.max_results_per_title,
                    updated_at = excluded.updated_at
                """,
                (
                    config.id,
                    config.profile_id,
                    json.dumps(config.target_locations),
                    config.remote_preference.value,
                    config.seniority_level.value if config.seniority_level else None,
                    config.min_compensation,
                    config.currency,
                    config.min_results_per_title,
                    config.max_results_per_title,
                    config.created_at.isoformat(),
                    config.updated_at.isoformat(),
                ),
            )
        return self.get_configuration(config.profile_id) or config

    def get_configuration(self, profile_id: str) -> Optional[SearchConfiguration]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, profile_id, target_locations, remote_preference, seniority_level,
                   min_compensation, currency, min_results_per_title, max_results_per_title,
                   created_at, updated_at
            FROM search_configurations
            WHERE profile_id = ?
            """,
            (profile_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        locations = json.loads(row["target_locations"]) if row["target_locations"] else []
        seniority = SeniorityLevel(row["seniority_level"]) if row["seniority_level"] else None
        return SearchConfiguration(
            id=row["id"],
            profile_id=row["profile_id"],
            target_locations=locations,
            remote_preference=RemotePreference(row["remote_preference"]),
            seniority_level=seniority,
            min_compensation=row["min_compensation"],
            currency=row["currency"],
            min_results_per_title=row["min_results_per_title"],
            max_results_per_title=row["max_results_per_title"],
            created_at=_parse_timestamp(row["created_at"]),
            updated_at=_parse_timestamp(row["updated_at"]),
        )


class PostingRepository:
    """Repository for storing and querying discovered job postings (Module 4)."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save_posting(self, posting: JobPosting) -> JobPosting:
        """Insert or update a job posting, enforcing content_hash uniqueness."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO job_postings (
                    id, search_term_id, title, company, location,
                    description, requirements_extracted, source_url,
                    direct_apply_url, content_hash, status, posting_date,
                    discovered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(content_hash) DO UPDATE SET
                    title = excluded.title,
                    company = excluded.company,
                    location = excluded.location,
                    description = excluded.description,
                    requirements_extracted = excluded.requirements_extracted,
                    direct_apply_url = excluded.direct_apply_url,
                    status = excluded.status,
                    posting_date = excluded.posting_date
                """,
                (
                    posting.id,
                    posting.search_term_id,
                    posting.title,
                    posting.company,
                    posting.location,
                    posting.description,
                    json.dumps(posting.requirements_extracted or []),
                    posting.source_url,
                    posting.direct_apply_url,
                    posting.content_hash,
                    posting.status.value,
                    posting.posting_date,
                    posting.discovered_at.isoformat(),
                ),
            )
        return self.get_by_content_hash(posting.content_hash) or posting

    def get_posting(self, posting_id: str) -> Optional[JobPosting]:
        """Fetch a job posting by primary ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, search_term_id, title, company, location,
                   description, requirements_extracted, source_url,
                   direct_apply_url, content_hash, status, posting_date,
                   discovered_at
            FROM job_postings WHERE id = ?
            """,
            (posting_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_model(row)

    def get_by_content_hash(self, content_hash: str) -> Optional[JobPosting]:
        """Fetch a job posting by unique content hash."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, search_term_id, title, company, location,
                   description, requirements_extracted, source_url,
                   direct_apply_url, content_hash, status, posting_date,
                   discovered_at
            FROM job_postings WHERE content_hash = ?
            """,
            (content_hash,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_model(row)

    def list_postings_by_term(self, search_term_id: str) -> List[JobPosting]:
        """List all postings associated with a specific search term."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, search_term_id, title, company, location,
                   description, requirements_extracted, source_url,
                   direct_apply_url, content_hash, status, posting_date,
                   discovered_at
            FROM job_postings
            WHERE search_term_id = ?
            ORDER BY discovered_at DESC
            """,
            (search_term_id,),
        )
        return [self._row_to_model(r) for r in cursor.fetchall()]

    def list_all_postings(self, limit: int = 100) -> List[JobPosting]:
        """List discovered postings with a limit."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, search_term_id, title, company, location,
                   description, requirements_extracted, source_url,
                   direct_apply_url, content_hash, status, posting_date,
                   discovered_at
            FROM job_postings
            ORDER BY discovered_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [self._row_to_model(r) for r in cursor.fetchall()]

    def count_postings(self) -> int:
        """Count total postings stored."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM job_postings")
        row = cursor.fetchone()
        return row["total"] if row else 0

    def _row_to_model(self, row: sqlite3.Row) -> JobPosting:
        raw_req = row["requirements_extracted"]
        requirements = json.loads(raw_req) if raw_req else []
        return JobPosting(
            id=row["id"],
            search_term_id=row["search_term_id"],
            title=row["title"],
            company=row["company"],
            location=row["location"],
            description=row["description"],
            requirements_extracted=requirements,
            source_url=row["source_url"],
            direct_apply_url=row["direct_apply_url"],
            content_hash=row["content_hash"],
            status=PostingAvailability(row["status"]),
            posting_date=row["posting_date"],
            discovered_at=_parse_timestamp(row["discovered_at"]),
        )


class ApplicationRepository:
    """Repository for managing application records and generated documents (Modules 5 & 6)."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create_or_get_application(
        self,
        profile_id: str,
        job_posting_id: str,
        initial_status: ApplicationStatus = ApplicationStatus.DISCOVERED,
    ) -> ApplicationRecord:
        """Fetch existing application record or create a new one."""
        existing = self.get_by_profile_and_posting(profile_id, job_posting_id)
        if existing:
            return existing

        app_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO application_records (
                    id, profile_id, job_posting_id, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (app_id, profile_id, job_posting_id, initial_status.value, now, now),
            )
        return self.get_application(app_id)  # type: ignore

    def get_application(self, application_id: str) -> Optional[ApplicationRecord]:
        """Fetch an application record by ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, profile_id, job_posting_id, status, applied_at,
                   notes, contact_person, contact_email, created_at, updated_at
            FROM application_records WHERE id = ?
            """,
            (application_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_app(row)

    def get_by_profile_and_posting(
        self, profile_id: str, job_posting_id: str
    ) -> Optional[ApplicationRecord]:
        """Find an application record matching profile_id and job_posting_id."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, profile_id, job_posting_id, status, applied_at,
                   notes, contact_person, contact_email, created_at, updated_at
            FROM application_records
            WHERE profile_id = ? AND job_posting_id = ?
            """,
            (profile_id, job_posting_id),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_app(row)

    def update_status(
        self,
        application_id: str,
        status: ApplicationStatus,
        notes: Optional[str] = None,
        applied_at: Optional[datetime] = None,
    ) -> ApplicationRecord:
        """Update status and metadata for an existing application."""
        now = datetime.now(timezone.utc).isoformat()
        applied_str = applied_at.isoformat() if applied_at else None
        with self.conn:
            self.conn.execute(
                """
                UPDATE application_records
                SET status = ?,
                    notes = COALESCE(?, notes),
                    applied_at = COALESCE(?, applied_at),
                    updated_at = ?
                WHERE id = ?
                """,
                (status.value, notes, applied_str, now, application_id),
            )
        record = self.get_application(application_id)
        if not record:
            raise ValueError(f"Application {application_id} not found.")
        return record

    def list_applications_for_profile(self, profile_id: str) -> List[ApplicationRecord]:
        """List all application records for a given user profile."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, profile_id, job_posting_id, status, applied_at,
                   notes, contact_person, contact_email, created_at, updated_at
            FROM application_records
            WHERE profile_id = ?
            ORDER BY updated_at DESC
            """,
            (profile_id,),
        )
        return [self._row_to_app(r) for r in cursor.fetchall()]

    def save_document(self, doc: ApplicationDocument) -> ApplicationDocument:
        """Store a generated document artifact."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO application_documents (
                    id, application_id, document_type, file_path,
                    content_text, model_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    file_path = excluded.file_path,
                    content_text = excluded.content_text
                """,
                (
                    doc.id,
                    doc.application_id,
                    doc.document_type.value,
                    doc.file_path,
                    doc.content_text,
                    doc.model_version,
                    doc.created_at.isoformat(),
                ),
            )
        return self.get_document(doc.id) or doc

    def get_document(self, doc_id: str) -> Optional[ApplicationDocument]:
        """Fetch an application document by ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, application_id, document_type, file_path,
                   content_text, model_version, created_at
            FROM application_documents WHERE id = ?
            """,
            (doc_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_doc(row)

    def list_documents_for_application(self, application_id: str) -> List[ApplicationDocument]:
        """List all generated documents for an application."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, application_id, document_type, file_path,
                   content_text, model_version, created_at
            FROM application_documents
            WHERE application_id = ?
            ORDER BY created_at DESC
            """,
            (application_id,),
        )
        return [self._row_to_doc(r) for r in cursor.fetchall()]

    def _row_to_app(self, row: sqlite3.Row) -> ApplicationRecord:
        applied = _parse_timestamp(row["applied_at"]) if row["applied_at"] else None
        return ApplicationRecord(
            id=row["id"],
            profile_id=row["profile_id"],
            job_posting_id=row["job_posting_id"],
            status=ApplicationStatus(row["status"]),
            applied_at=applied,
            notes=row["notes"],
            contact_person=row["contact_person"],
            contact_email=row["contact_email"],
            created_at=_parse_timestamp(row["created_at"]),
            updated_at=_parse_timestamp(row["updated_at"]),
        )

    def _row_to_doc(self, row: sqlite3.Row) -> ApplicationDocument:
        return ApplicationDocument(
            id=row["id"],
            application_id=row["application_id"],
            document_type=DocumentType(row["document_type"]),
            file_path=row["file_path"],
            content_text=row["content_text"],
            model_version=row["model_version"],
            created_at=_parse_timestamp(row["created_at"]),
        )
