"""HTML parsing, content extraction, and content hash computation (Module 4, FR-015, FR-016)."""

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional

from bs4 import BeautifulSoup

from findrr.models.posting import JobPostingCreate, PostingAvailability
from findrr.search.link_resolver import LinkResolver

logger = logging.getLogger(__name__)

MAX_DESCRIPTION_LENGTH = 50000


def normalize_text_for_hash(text: str) -> str:
    """Normalize text by lowercasing, stripping punctuation, and collapsing whitespace."""
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    return " ".join(cleaned.split())


def compute_content_hash(company: str, title: str, description: str) -> str:
    """Compute deterministic SHA-256 content hash for duplicate detection (FR-016)."""
    norm_comp = normalize_text_for_hash(company)
    norm_title = normalize_text_for_hash(title)
    # Take first 500 chars of normalized description to absorb minor layout differences
    norm_desc = normalize_text_for_hash(description)[:500]

    raw_signature = f"{norm_comp}|{norm_title}|{norm_desc}".encode("utf-8")
    return hashlib.sha256(raw_signature).hexdigest()


def detect_availability(text: str) -> PostingAvailability:
    """Determine posting availability status from textual indicators."""
    lower_text = text.lower()
    closed_indicators = [
        "this job has expired",
        "no longer accepting applications",
        "position has been filled",
        "applications are now closed",
        "job is no longer available",
        "closed for applications",
        "this vacancy is closed",
    ]
    for ind in closed_indicators:
        if ind in lower_text:
            return PostingAvailability.CLOSED

    return PostingAvailability.ACTIVE


def extract_skills_keywords(text: str) -> List[str]:
    """Extract common tech/professional skills from job text without fabricating."""
    common_skills = [
        "python",
        "java",
        "c++",
        "c#",
        "golang",
        "rust",
        "typescript",
        "javascript",
        "sql",
        "postgresql",
        "mysql",
        "mongodb",
        "redis",
        "elasticsearch",
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "terraform",
        "ansible",
        "linux",
        "git",
        "ci/cd",
        "rest",
        "graphql",
        "microservices",
        "react",
        "vue",
        "fastapi",
        "django",
        "flask",
        "spring",
        "agile",
        "scrum",
    ]
    lower_text = text.lower()
    found: List[str] = []
    for skill in common_skills:
        # Match whole word boundaries
        if re.search(r"\b" + re.escape(skill) + r"\b", lower_text):
            found.append(skill)
    return sorted(list(set(found)))


class PostingParser:
    """Extracts structured posting data from untrusted HTML documents."""

    @classmethod
    def parse_html(
        cls,
        html_content: str,
        source_url: str,
        search_term_id: Optional[str] = None,
        fallback_title: Optional[str] = None,
        fallback_company: Optional[str] = None,
    ) -> Optional[JobPostingCreate]:
        """Parse raw HTML and extract structured JobPostingCreate record.

        Treats all input as untrusted content, stripping dangerous elements and capping sizes.
        """
        if not html_content or not html_content.strip():
            return None

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract schema.org/JobPosting JSON-LD before removing script tags
            json_ld_posting = cls._extract_from_json_ld(soup)

            # Remove executable, style, and iframe tags
            for elem in soup(["style", "noscript", "iframe", "svg"]):
                elem.extract()
            for s in soup.find_all("script"):
                s.extract()

            if json_ld_posting:
                title = json_ld_posting.get("title") or fallback_title
                company = json_ld_posting.get("company") or fallback_company
                location = json_ld_posting.get("location")
                description = json_ld_posting.get("description", "")
                posting_date = json_ld_posting.get("datePosted")

                if title and company and description:
                    resolved_url, _ = LinkResolver.resolve_preferred_destination(
                        source_url, html_content
                    )
                    clean_desc = description[:MAX_DESCRIPTION_LENGTH]
                    c_hash = compute_content_hash(company, title, clean_desc)
                    status = detect_availability(clean_desc)
                    skills = extract_skills_keywords(clean_desc)

                    return JobPostingCreate(
                        search_term_id=search_term_id,
                        title=title.strip(),
                        company=company.strip(),
                        location=location.strip() if location else None,
                        description=clean_desc.strip(),
                        requirements_extracted=skills,
                        source_url=source_url,
                        direct_apply_url=resolved_url,
                        content_hash=c_hash,
                        status=status,
                        posting_date=posting_date,
                    )

            # Heuristic DOM extraction
            title = cls._extract_title(soup) or fallback_title
            company = cls._extract_company(soup) or fallback_company
            location = cls._extract_location(soup)
            description = cls._extract_description(soup)

            if not title or not company:
                logger.debug("Failed extracting mandatory title/company from %s", source_url)
                return None

            if not description:
                description = soup.get_text(separator="\n", strip=True)

            clean_desc = description[:MAX_DESCRIPTION_LENGTH].strip()
            if not clean_desc:
                return None

            c_hash = compute_content_hash(company, title, clean_desc)
            resolved_url, _ = LinkResolver.resolve_preferred_destination(source_url, html_content)
            status = detect_availability(clean_desc)
            skills = extract_skills_keywords(clean_desc)

            return JobPostingCreate(
                search_term_id=search_term_id,
                title=title.strip(),
                company=company.strip(),
                location=location.strip() if location else None,
                description=clean_desc,
                requirements_extracted=skills,
                source_url=source_url,
                direct_apply_url=resolved_url,
                content_hash=c_hash,
                status=status,
                posting_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            )

        except Exception as err:
            logger.warning("Error parsing posting HTML for %s: %s", source_url, err)
            return None

    @classmethod
    def _extract_from_json_ld(cls, soup: BeautifulSoup) -> Optional[dict]:
        """Extract posting data from schema.org JobPosting JSON-LD."""
        scripts = soup.find_all("script", type="application/ld+json")
        for s in scripts:
            try:
                data = json.loads(s.string or "")
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = [data]
                else:
                    continue

                for item in items:
                    if item.get("@type") == "JobPosting":
                        company = ""
                        hiring_org = item.get("hiringOrganization")
                        if isinstance(hiring_org, dict):
                            company = hiring_org.get("name", "")
                        elif isinstance(hiring_org, str):
                            company = hiring_org

                        loc_str = None
                        job_loc = item.get("jobLocation")
                        if isinstance(job_loc, dict):
                            addr = job_loc.get("address")
                            if isinstance(addr, dict):
                                loc_str = addr.get("addressLocality") or addr.get("addressRegion")
                            elif isinstance(addr, str):
                                loc_str = addr

                        return {
                            "title": item.get("title"),
                            "company": company,
                            "location": loc_str,
                            "description": BeautifulSoup(
                                item.get("description", ""), "html.parser"
                            ).get_text(separator="\n", strip=True),
                            "datePosted": item.get("datePosted"),
                        }
            except Exception:
                continue
        return None

    @classmethod
    def _extract_title(cls, soup: BeautifulSoup) -> Optional[str]:
        for selector in ["h1.jobsearch-JobInfoHeader-title", "h1.job-title", "h1.title", "h1"]:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                return elem.get_text(strip=True)
        if soup.title and soup.title.string:
            title_text = soup.title.string.split("-")[0].split("|")[0].strip()
            if title_text:
                return title_text
        return None

    @classmethod
    def _extract_company(cls, soup: BeautifulSoup) -> Optional[str]:
        for selector in [
            "[data-company-name='true']",
            ".company-name",
            ".employer",
            ".company",
            "[class*='company']",
            "[class*='employer']",
            "[class*='hiring-org']",
        ]:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                return elem.get_text(strip=True)

        meta_selectors = [
            ("meta[property='og:site_name']", "content"),
            ("meta[name='author']", "content"),
            ("meta[name='twitter:site']", "content"),
            ("meta[name='publisher']", "content"),
        ]
        for sel, attr in meta_selectors:
            meta_tag = soup.select_one(sel)
            if meta_tag and meta_tag.get(attr):
                val = meta_tag.get(attr, "").strip()
                if val.startswith("@"):
                    val = val[1:].strip()
                if val and len(val) <= 100:
                    return val

        return None

    @classmethod
    def _extract_location(cls, soup: BeautifulSoup) -> Optional[str]:
        selectors = [
            ".job-location",
            ".location",
            "[class*='location']",
            "span[class*='city']",
        ]
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                return elem.get_text(strip=True)
        return None

    @classmethod
    def _extract_description(cls, soup: BeautifulSoup) -> Optional[str]:
        for selector in [
            "#jobDescriptionText",
            ".job-description",
            ".description",
            "[class*='description']",
            "[class*='job-details']",
            "[class*='job-content']",
            "[class*='posting-content']",
            "article",
            "main",
            "[role='main']",
        ]:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(separator="\n", strip=True)
                if len(text) > 100:
                    return text
        return None
