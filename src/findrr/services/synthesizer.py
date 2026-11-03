"""Algorithmic generalized job title synthesizer."""

import re
from collections import Counter
from typing import Dict, List, Optional

from findrr.models.profile import ProfileCategory, ProfileEntry, UserProfile
from findrr.models.title import GeneralizedTitleCreate


class InsufficientProfileDataError(ValueError):
    """Raised when profile data is insufficient to synthesize an objective title."""

    def __init__(self, missing_fields: List[str]):
        self.missing_fields = missing_fields
        missing_str = ", ".join(missing_fields)
        super().__init__(
            f"Cannot synthesize generalized title due to missing profile data: {missing_str}. "
            "Please provide verified profile entries first."
        )


# Domain clusters and characteristic keywords
DOMAIN_CLUSTERS: Dict[str, Dict[str, List[str]]] = {
    "Software Engineering": {
        "titles": [
            "Software Engineer",
            "Software Developer",
            "Backend Engineer",
            "Frontend Engineer",
            "Full Stack Engineer",
            "Applications Developer",
        ],
        "keywords": [
            "python",
            "java",
            "c++",
            "c#",
            "golang",
            "rust",
            "typescript",
            "javascript",
            "backend",
            "frontend",
            "fullstack",
            "full stack",
            "api",
            "rest",
            "graphql",
            "django",
            "flask",
            "fastapi",
            "react",
            "vue",
            "angular",
            "node",
            "sql",
            "git",
        ],
    },
    "Data Science & Machine Learning": {
        "titles": [
            "Data Scientist",
            "Machine Learning Engineer",
            "AI Engineer",
            "Data Analyst",
            "Data Engineer",
        ],
        "keywords": [
            "machine learning",
            "deep learning",
            "nlp",
            "computer vision",
            "pytorch",
            "tensorflow",
            "pandas",
            "numpy",
            "scikit-learn",
            "data science",
            "data analysis",
            "sql",
            "statistics",
            "feature engineering",
            "llm",
            "transformers",
            "kaggle",
        ],
    },
    "DevOps & Cloud Systems": {
        "titles": [
            "DevOps Engineer",
            "Cloud Platform Engineer",
            "Site Reliability Engineer",
            "Infrastructure Engineer",
        ],
        "keywords": [
            "docker",
            "kubernetes",
            "aws",
            "gcp",
            "azure",
            "ci/cd",
            "terraform",
            "linux",
            "bash",
            "ansible",
            "cloud",
            "infrastructure",
            "jenkins",
            "prometheus",
        ],
    },
    "Product & Project Management": {
        "titles": [
            "Product Manager",
            "Technical Project Manager",
            "Scrum Master",
            "Product Owner",
        ],
        "keywords": [
            "agile",
            "scrum",
            "product management",
            "roadmap",
            "stakeholder",
            "jira",
            "backlog",
            "user stories",
            "kpis",
            "sprint planning",
            "requirements gathering",
        ],
    },
    "UI/UX Design": {
        "titles": [
            "UI/UX Designer",
            "Product Designer",
            "User Experience Researcher",
        ],
        "keywords": [
            "figma",
            "penpot",
            "wireframing",
            "prototyping",
            "user research",
            "usability",
            "design system",
            "information architecture",
            "interaction design",
        ],
    },
}


class TitleSynthesizer:
    """Synthesizes objective generalized titles from verified user profile entries."""

    @staticmethod
    def validate_profile_readiness(profile: UserProfile) -> List[str]:
        """Check whether profile has sufficient verified entries to synthesize a title."""
        missing = []
        verified_entries = [e for e in profile.entries if e.is_verified]

        has_education = any(e.category == ProfileCategory.EDUCATION for e in verified_entries)
        has_experience = any(e.category == ProfileCategory.EXPERIENCE for e in verified_entries)
        skills_count = sum(1 for e in verified_entries if e.category == ProfileCategory.SKILL)

        if not (has_education or has_experience):
            missing.append("At least 1 verified Education or Experience entry")
        if skills_count < 1:
            missing.append("At least 1 verified Skill entry")

        return missing

    def synthesize(self, profile: UserProfile) -> GeneralizedTitleCreate:
        """Synthesize a GeneralizedTitleCreate domain schema from a verified profile."""
        missing = self.validate_profile_readiness(profile)
        if missing:
            raise InsufficientProfileDataError(missing)

        verified_entries = [e for e in profile.entries if e.is_verified]
        skills = [e.title.strip() for e in verified_entries if e.category == ProfileCategory.SKILL]
        experiences = [e for e in verified_entries if e.category == ProfileCategory.EXPERIENCE]
        education = [e for e in verified_entries if e.category == ProfileCategory.EDUCATION]

        # Analyze domain match
        scores: Counter = Counter()
        supporting_by_domain: Dict[str, List[str]] = {domain: [] for domain in DOMAIN_CLUSTERS}

        # Combine text tokens from skills and experience
        all_text = " ".join(
            [
                *[e.title for e in verified_entries],
                *[e.description or "" for e in verified_entries if e.description],
            ]
        ).lower()

        for domain, meta in DOMAIN_CLUSTERS.items():
            for kw in meta["keywords"]:
                pattern = r"\b" + re.escape(kw) + r"\b"
                matches = len(re.findall(pattern, all_text))
                if matches > 0:
                    scores[domain] += matches
                    # Check which skills match
                    for s in skills:
                        if kw in s.lower() and s not in supporting_by_domain[domain]:
                            supporting_by_domain[domain].append(s)

        # Fallback if no specific domain keywords matched
        if not scores:
            primary_domain = "Software Engineering"
            supporting = skills[:5]
        else:
            primary_domain, _ = scores.most_common(1)[0]
            supporting = supporting_by_domain[primary_domain]
            if not supporting:
                supporting = skills[:5]

        # Determine seniority from experiences
        seniority = self._determine_seniority(experiences)

        # Select representative base title
        base_title = DOMAIN_CLUSTERS[primary_domain]["titles"][0]
        if experiences:
            # Check if an existing experience title matches well
            exp_titles = [e.title for e in experiences]
            for candidate in DOMAIN_CLUSTERS[primary_domain]["titles"]:
                for et in exp_titles:
                    if candidate.lower() in et.lower():
                        base_title = candidate
                        break

        if seniority and not base_title.lower().startswith(seniority.lower()):
            primary_title = f"{seniority} {base_title}"
        else:
            primary_title = base_title

        # Build objective rationale
        exp_summary = (
            f"{len(experiences)} verified experience record(s)"
            if experiences
            else "academic and project qualifications"
        )
        edu_summary = f"education in {education[0].title}" if education else "practical experience"
        supporting_str = ", ".join(supporting[:5]) if supporting else "foundational competencies"

        rationale = (
            f"Synthesized from {exp_summary} and {edu_summary}. "
            f"Strongest alignment in {primary_domain} "
            f"supported by verified competencies: {supporting_str}."
        )

        return GeneralizedTitleCreate(
            profile_id=profile.id,
            primary_title=primary_title,
            rationale=rationale,
            supporting_skills=supporting,
            is_active=True,
        )

    def _determine_seniority(self, experiences: List[ProfileEntry]) -> Optional[str]:
        """Infer seniority prefix based on verified job titles and duration."""
        if not experiences:
            return None

        titles_str = " ".join([e.title.lower() for e in experiences])
        if any(w in titles_str for w in ["lead", "principal", "staff"]):
            return "Lead"
        if any(w in titles_str for w in ["senior", "sr.", "sr "]):
            return "Senior"
        if any(w in titles_str for w in ["junior", "jr.", "jr ", "entry", "intern", "associate"]):
            if len(experiences) <= 2:
                return "Junior"

        if len(experiences) >= 4:
            return "Senior"

        return None
