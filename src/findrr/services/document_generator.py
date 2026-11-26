"""Deterministic, fact-grounded document generation engine (Module 5, FR-020, FR-021)."""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from findrr.models.application import DocumentType, RequirementAnalysisResult, TailoredDraftResult
from findrr.models.posting import JobPosting
from findrr.models.profile import ProfileCategory, UserProfile
from findrr.services.grounding_validator import FactGroundingValidator

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """Generates tailored application materials strictly grounded in verified facts."""

    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is not None:
            self.storage_dir = Path(storage_dir)
        elif "FINDRR_DOCS_DIR" in os.environ:
            self.storage_dir = Path(os.environ["FINDRR_DOCS_DIR"])
        else:
            self.storage_dir = Path("data/applications")

    def generate_tailored_cv(
        self,
        application_id: str,
        profile: UserProfile,
        posting: JobPosting,
        analysis: RequirementAnalysisResult,
    ) -> TailoredDraftResult:
        """Render a fact-grounded tailored CV in Markdown format.

        Every statement is taken from verified profile entries or the posting itself.
        No adjectives, proficiency levels or achievements are added (BR-002, NFR-009).
        """
        display = self._skill_display_names(profile)
        matching = [s.lower() for s in analysis.matching_skills]
        matching_names = [display.get(s, s) for s in matching]
        other_verified = [
            display.get(s, s) for s in self._get_verified_skills(profile) if s not in matching
        ][:8]

        experiences = self._verified(profile, ProfileCategory.EXPERIENCE)
        education = self._verified(profile, ProfileCategory.EDUCATION)
        certifications = self._verified(profile, ProfileCategory.CERTIFICATION)
        projects = self._verified(profile, ProfileCategory.PROJECT)

        lines: List[str] = []
        lines.append(f"# {profile.full_name}")

        contact_parts: List[str] = []
        if profile.location:
            contact_parts.append(profile.location)
        contact_parts.append(profile.email)
        if profile.phone:
            contact_parts.append(profile.phone)
        lines.append(" | ".join(contact_parts))
        lines.append("")

        lines.append("## Professional Summary")
        lines.append(f"Application for the **{posting.title}** role at **{posting.company}**.")
        if profile.professional_summary:
            lines.append(profile.professional_summary.strip())
        if matching_names:
            lines.append(
                "Verified skills that match this posting: " + ", ".join(matching_names[:4]) + "."
            )
        lines.append("")

        if matching_names or other_verified:
            lines.append("## Skills")
            for name in matching_names:
                lines.append(f"- **{name}** (listed in this posting)")
            for name in other_verified:
                lines.append(f"- {name}")
            lines.append("")

        if experiences:
            lines.append("## Professional Experience")
            for exp in experiences:
                org_part = f" - {exp.organization}" if exp.organization else ""
                lines.append(f"### {exp.title}{org_part}")
                date_range = self._date_range(exp.start_date, exp.end_date)
                if date_range:
                    lines.append(f"*{date_range}*")
                if exp.description:
                    lines.append(exp.description)
                lines.append("")

        if education:
            lines.append("## Education & Credentials")
            for edu in education:
                org_part = f", {edu.organization}" if edu.organization else ""
                date_part = f" ({edu.end_date})" if edu.end_date else ""
                lines.append(f"- **{edu.title}**{org_part}{date_part}")
            lines.append("")

        if certifications:
            lines.append("## Certifications")
            for cert in certifications:
                org_part = f" — {cert.organization}" if cert.organization else ""
                lines.append(f"- **{cert.title}**{org_part}")
            lines.append("")

        if projects:
            lines.append("## Projects")
            for proj in projects:
                lines.append(f"### {proj.title}")
                if proj.description:
                    lines.append(proj.description)
                lines.append("")

        rendered_text = "\n".join(lines).strip()

        # Enforce zero-fabrication validation
        FactGroundingValidator.validate_document_grounding(rendered_text, profile, posting)

        file_path = self._save_file(application_id, "tailored_cv.md", rendered_text)
        return TailoredDraftResult(
            application_id=application_id,
            document_type=DocumentType.TAILORED_CV,
            file_path=str(file_path),
            content_text=rendered_text,
            is_grounded=True,
        )

    def generate_cover_letter(
        self,
        application_id: str,
        profile: UserProfile,
        posting: JobPosting,
        analysis: RequirementAnalysisResult,
    ) -> TailoredDraftResult:
        """Render a cover letter built only from verified profile facts (BR-002, NFR-009).

        Sections whose facts are absent from the profile are omitted, never filled in.
        """
        display = self._skill_display_names(profile)
        matching_names = [display.get(s.lower(), s) for s in analysis.matching_skills][:3]
        experiences = self._verified(profile, ProfileCategory.EXPERIENCE)
        education = self._verified(profile, ProfileCategory.EDUCATION)

        lines: List[str] = [
            f"Dear Hiring Team at {posting.company},",
            "",
            f"I am applying for the {posting.title} position.",
        ]

        if matching_names:
            lines.append("")
            lines.append(
                "My profile lists these skills that the posting asks for: "
                + ", ".join(matching_names)
                + "."
            )

        if experiences:
            exp = experiences[0]
            org_part = f" at {exp.organization}" if exp.organization else ""
            date_range = self._date_range(exp.start_date, exp.end_date)
            date_part = f" ({date_range})" if date_range else ""
            lines.append("")
            lines.append(f"My most recent listed role is {exp.title}{org_part}{date_part}.")
            if exp.description:
                lines.append(exp.description.strip())

        if education:
            edu = education[0]
            org_part = f" from {edu.organization}" if edu.organization else ""
            lines.append("")
            lines.append(f"I hold a {edu.title}{org_part}.")

        lines.extend(
            [
                "",
                "Thank you for considering my application.",
                "",
                "Sincerely,",
                "",
                profile.full_name,
                profile.email,
            ]
        )

        rendered_text = "\n".join(lines).strip()

        # Enforce zero-fabrication validation
        FactGroundingValidator.validate_document_grounding(rendered_text, profile, posting)

        file_path = self._save_file(application_id, "cover_letter.md", rendered_text)
        return TailoredDraftResult(
            application_id=application_id,
            document_type=DocumentType.COVER_LETTER,
            file_path=str(file_path),
            content_text=rendered_text,
            is_grounded=True,
        )

    @staticmethod
    def _verified(profile: UserProfile, category: ProfileCategory) -> list:
        return [e for e in profile.entries if e.is_verified and e.category == category]

    @staticmethod
    def _date_range(start: Optional[str], end: Optional[str]) -> str:
        """Render only the dates the user supplied; never invent 'Present' or a start date."""
        if start and end:
            return f"{start} — {end}"
        return start or end or ""

    @staticmethod
    def _skill_display_names(profile: UserProfile) -> Dict[str, str]:
        """Map lower-cased verified skills to the casing the user entered (e.g. 'sql' -> 'SQL')."""
        names: Dict[str, str] = {}
        for e in profile.entries:
            if e.is_verified and e.category == ProfileCategory.SKILL:
                for raw in e.title.split(","):
                    clean = raw.strip()
                    if clean and clean.lower() not in names:
                        names[clean.lower()] = clean
        return names

    def _get_verified_skills(self, profile: UserProfile) -> List[str]:
        skills: List[str] = []
        for e in profile.entries:
            if e.is_verified and e.category == ProfileCategory.SKILL:
                for s in e.title.split(","):
                    clean = s.strip().lower()
                    if clean and clean not in skills:
                        skills.append(clean)
        return sorted(skills)

    def _save_file(self, application_id: str, filename: str, content: str) -> Path:
        target_dir = self.storage_dir / application_id
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / filename
        file_path.write_text(content, encoding="utf-8")
        logger.info("Saved application document to %s", file_path)
        return file_path
