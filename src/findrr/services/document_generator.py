"""Deterministic, fact-grounded document generation engine (Module 5, FR-020, FR-021)."""

import logging
from pathlib import Path
from typing import List, Optional

from findrr.models.application import DocumentType, RequirementAnalysisResult, TailoredDraftResult
from findrr.models.posting import JobPosting
from findrr.models.profile import ProfileCategory, UserProfile
from findrr.services.grounding_validator import FactGroundingValidator

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """Generates tailored application materials strictly grounded in verified facts."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("data/applications")

    def generate_tailored_cv(
        self,
        application_id: str,
        profile: UserProfile,
        posting: JobPosting,
        analysis: RequirementAnalysisResult,
    ) -> TailoredDraftResult:
        """Render a fact-grounded tailored CV in Markdown format."""
        verified_matching = [s.lower() for s in analysis.matching_skills]
        verified_matching_str = (
            ", ".join(verified_matching[:4]) if verified_matching else "core technical competencies"
        )

        all_verified_skills = self._get_verified_skills(profile)
        other_verified = [s for s in all_verified_skills if s.lower() not in verified_matching][:8]

        experiences = [
            e for e in profile.entries if e.is_verified and e.category == ProfileCategory.EXPERIENCE
        ]
        education = [
            e for e in profile.entries if e.is_verified and e.category == ProfileCategory.EDUCATION
        ]
        certifications = [
            e
            for e in profile.entries
            if e.is_verified and e.category == ProfileCategory.CERTIFICATION
        ]
        projects = [
            e for e in profile.entries if e.is_verified and e.category == ProfileCategory.PROJECT
        ]

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
        lines.append(
            f"Dedicated and results-driven professional targeting the **{posting.title}** role "
            f"at **{posting.company}**. "
            f"Offering proven expertise in {verified_matching_str}. "
            "Grounded in rigorous execution, collaborative problem-solving, "
            "and continuous technical growth."
        )
        lines.append("")

        lines.append("## Core Competencies & Skills")
        for skill in verified_matching:
            lines.append(f"- **{skill.title()}** (Verified Proficiency)")
        for skill in other_verified:
            lines.append(f"- {skill.title()}")
        lines.append("")

        if experiences:
            lines.append("## Professional Experience")
            for exp in experiences:
                org_part = f" - {exp.organization}" if exp.organization else ""
                lines.append(f"### {exp.title}{org_part}")
                start = exp.start_date or "Past"
                end = exp.end_date or "Present"
                lines.append(f"*{start} — {end}*")
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
            lines.append("## Notable Projects")
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
        """Render a tailored cover letter grounded in verified candidate facts."""
        verified_matching = [s.lower() for s in analysis.matching_skills]
        verified_matching_str = (
            ", ".join(verified_matching[:3]) if verified_matching else "industry best practices"
        )

        all_verified = self._get_verified_skills(profile)
        core_skills_str = ", ".join(all_verified[:4]) if all_verified else "software engineering"

        lines: List[str] = [
            f"Dear Hiring Team at {posting.company},",
            "",
            f"I am writing to express my strong interest in the {posting.title} position. "
            f"With verified hands-on experience in {verified_matching_str}, "
            "I am confident in my ability to contribute effectively to your team from day one.",
            "",
            "Throughout my professional career, I have focused on delivering "
            "reliable, high-quality outcomes. "
            f"My background includes proven experience with {core_skills_str}, "
            "where I have developed a strong foundation in building scalable, "
            "maintainable solutions.",
            "",
            f"I am particularly excited about the opportunity at {posting.company} "
            "and look forward to discussing how my skills and qualifications align "
            "with your engineering and operational goals.",
            "",
            "Sincerely,",
            "",
            profile.full_name,
            profile.email,
        ]

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
