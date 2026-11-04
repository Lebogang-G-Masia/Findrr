"""Interactive CLI prompts and handlers for user profiles."""

from typing import Callable, List, Optional

from findrr.models.profile import (
    ProfileCategory,
    ProfileEntryCreate,
    ProvenanceSource,
    UserProfile,
    UserProfileCreate,
)
from findrr.services.profile_service import ProfileService
from findrr.services.synthesizer import InsufficientProfileDataError


def _input(
    prompt_text: str, default: Optional[str] = None, input_fn: Optional[Callable[[str], str]] = None
) -> str:
    if input_fn is None:
        input_fn = input
    display_prompt = f"{prompt_text} [{default}]: " if default else f"{prompt_text}: "
    val = input_fn(display_prompt).strip()
    if not val and default is not None:
        return default
    return val


def run_interactive_questionnaire(
    profile_service: ProfileService,
    input_fn: Optional[Callable[[str], str]] = None,
    print_fn: Optional[Callable[..., None]] = None,
) -> Optional[UserProfile]:
    """Run interactive CLI questionnaire to ingest and verify a user profile."""
    if input_fn is None:
        input_fn = input
    if print_fn is None:
        print_fn = print
    print_fn("\n" + "=" * 60)
    print_fn("   Findrr: Interactive Profile Questionnaire (US-001)")
    print_fn("=" * 60)

    # 1. Personal Information
    print_fn("\n--- 1. Personal Information ---")
    name = ""
    while not name:
        name = _input("Full Name", input_fn=input_fn)
        if not name:
            print_fn("Full Name is required.")

    email = ""
    while not email or "@" not in email:
        email = _input("Email Address", input_fn=input_fn)
        if not email or "@" not in email:
            print_fn("Please enter a valid email address.")

    phone = _input("Phone Number (optional)", default="", input_fn=input_fn) or None
    location = (
        _input("Location (e.g. London, UK / Johannesburg, SA)", default="", input_fn=input_fn)
        or None
    )
    summary = _input("Professional Summary (optional)", default="", input_fn=input_fn) or None

    user_data = UserProfileCreate(
        full_name=name,
        email=email,
        phone=phone,
        location=location,
        professional_summary=summary,
    )

    entries: List[ProfileEntryCreate] = []

    # 2. Education
    print_fn("\n--- 2. Education ---")
    while True:
        has_edu = _input("Add an education entry? (y/n)", default="y", input_fn=input_fn).lower()
        if has_edu not in ("y", "yes"):
            break
        deg = _input("Degree / Qualification (e.g. BSc Computer Science)", input_fn=input_fn)
        inst = _input("Institution / University", input_fn=input_fn)
        start = _input("Start Date (YYYY-MM)", default="", input_fn=input_fn) or None
        end = _input("End Date (YYYY-MM or CURRENT)", default="CURRENT", input_fn=input_fn) or None
        desc = _input("Notes / Honours (optional)", default="", input_fn=input_fn) or None
        if deg:
            entries.append(
                ProfileEntryCreate(
                    category=ProfileCategory.EDUCATION,
                    title=deg,
                    organization=inst,
                    start_date=start,
                    end_date=end,
                    description=desc,
                    source=ProvenanceSource.MANUAL,
                    is_verified=False,
                )
            )

    # 3. Work Experience
    print_fn("\n--- 3. Work Experience ---")
    while True:
        has_exp = _input(
            "Add a work experience entry? (y/n)", default="y", input_fn=input_fn
        ).lower()
        if has_exp not in ("y", "yes"):
            break
        role = _input("Job Title / Role (e.g. Software Engineer)", input_fn=input_fn)
        org = _input("Company / Organization", input_fn=input_fn)
        start = _input("Start Date (YYYY-MM)", default="", input_fn=input_fn) or None
        end = _input("End Date (YYYY-MM or CURRENT)", default="CURRENT", input_fn=input_fn) or None
        desc = _input("Key Responsibilities & Achievements", default="", input_fn=input_fn) or None
        if role:
            entries.append(
                ProfileEntryCreate(
                    category=ProfileCategory.EXPERIENCE,
                    title=role,
                    organization=org,
                    start_date=start,
                    end_date=end,
                    description=desc,
                    source=ProvenanceSource.MANUAL,
                    is_verified=False,
                )
            )

    # 4. Skills
    print_fn("\n--- 4. Skills ---")
    skills_raw = _input(
        "Enter your key skills (comma-separated, e.g. Python, SQL, Docker, Linux)",
        input_fn=input_fn,
    )
    for skill_name in [s.strip() for s in skills_raw.split(",") if s.strip()]:
        entries.append(
            ProfileEntryCreate(
                category=ProfileCategory.SKILL,
                title=skill_name,
                source=ProvenanceSource.MANUAL,
                is_verified=False,
            )
        )

    # 5. Verification Review Step (FR-004 / AC-001)
    print_fn("\n" + "-" * 60)
    print_fn("   Profile Verification Review (FR-004)")
    print_fn("-" * 60)
    loc_str = user_data.location or "N/A"
    print_fn(f"Name: {user_data.full_name} | Email: {user_data.email} | Location: {loc_str}")
    print_fn(f"Total Entries Collected: {len(entries)}")
    for idx, e in enumerate(entries, 1):
        org_str = f" @ {e.organization}" if e.organization else ""
        print_fn(f"  [{idx}] [{e.category.value}] {e.title}{org_str}")

    confirm = _input(
        "\nDo you verify and approve saving these entries to your profile? (y/n)",
        default="y",
        input_fn=input_fn,
    ).lower()
    if confirm not in ("y", "yes"):
        print_fn("Profile creation cancelled by user. No data saved.")
        return None

    # Mark as verified per explicit confirmation
    for e in entries:
        e.is_verified = True

    created_profile = profile_service.create_profile(user_data, entries)
    print_fn(f"\n[SUCCESS] Profile created and verified successfully! ID: {created_profile.id}")
    return created_profile


def handle_synthesize_title(
    profile_service: ProfileService,
    profile_id: Optional[str] = None,
    print_fn: Callable[..., None] = print,
) -> None:
    """Trigger title synthesis for a profile."""
    if not profile_id:
        profiles = profile_service.list_profiles()
        if not profiles:
            print_fn("No profiles found. Create a profile first via 'findrr profile create'.")
            return
        profile_id = profiles[0].id

    try:
        title = profile_service.synthesize_generalized_title(profile_id)
        print_fn("\n" + "=" * 60)
        print_fn("   Synthesized Generalized Job Title (US-002)")
        print_fn("=" * 60)
        print_fn(f"Primary Title:      {title.primary_title}")
        print_fn(f"Rationale:          {title.rationale}")
        skills_str = ", ".join(title.supporting_skills) if title.supporting_skills else "None"
        print_fn(f"Supporting Skills:  {skills_str}")
        print_fn(f"Active Status:      {'Active' if title.is_active else 'Inactive'}")
    except InsufficientProfileDataError as err:
        print_fn(f"\n[CANNOT SYNTHESIZE] {err}")
    except Exception as exc:
        print_fn(f"\n[ERROR] Failed to synthesize title: {exc}")
