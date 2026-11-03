"""Database repositories for profiles, generalized titles, and search configurations."""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, List, Optional

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
