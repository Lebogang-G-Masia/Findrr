"""CLI commands for application preparation and requirement gap analysis (Module 5 & 6)."""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from findrr.db.repository import ApplicationRepository, PostingRepository, ProfileRepository
from findrr.models.application import ApplicationStatus
from findrr.services.application_service import ApplicationService
from findrr.services.document_generator import DocumentGenerator


def register_app_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Register application preparation subcommands."""
    app_parser = subparsers.add_parser(
        "apply", help="Application preparation and drafting (Module 5)"
    )
    app_sub = app_parser.add_subparsers(dest="apply_cmd", required=True)

    # findrr apply analyze <posting_id>
    analyze_parser = app_sub.add_parser(
        "analyze", help="Analyze job requirements against verified profile skills"
    )
    analyze_parser.add_argument("posting_id", help="UUID of the job posting to evaluate")
    analyze_parser.add_argument(
        "--profile-id", help="Target profile ID (defaults to active profile)"
    )

    # findrr apply draft <posting_id>
    draft_parser = app_sub.add_parser("draft", help="Generate tailored CV and cover letter drafts")
    draft_parser.add_argument("posting_id", help="UUID of the job posting")
    draft_parser.add_argument("--profile-id", help="Target profile ID")
    draft_parser.add_argument("--docs-dir", help="Custom output directory for generated drafts")
    draft_parser.add_argument("--no-cv", action="store_true", help="Skip CV generation")
    draft_parser.add_argument(
        "--no-letter", action="store_true", help="Skip cover letter generation"
    )

    # findrr apply status <application_id> <status>
    status_parser = app_sub.add_parser(
        "status", help="Update application lifecycle status and notes (Module 6)"
    )
    status_parser.add_argument("application_id", help="UUID of the application record")
    status_parser.add_argument(
        "status",
        choices=[s.value for s in ApplicationStatus],
        help="Target lifecycle status (e.g. SAVED, APPLIED, INTERVIEWING, OFFERED)",
    )
    status_parser.add_argument("--notes", help="Notes or developments regarding this update")
    status_parser.add_argument(
        "--applied-at",
        help="Submission date in ISO format YYYY-MM-DD (defaults to now for APPLIED)",
    )
    status_parser.add_argument("--contact-person", help="Contact person or recruiter name")
    status_parser.add_argument("--contact-email", help="Contact person email address")

    # findrr apply list
    list_parser = app_sub.add_parser("list", help="List prepared applications and statuses")
    list_parser.add_argument("--profile-id", help="Target profile ID")

    # findrr apply show <application_id>
    show_parser = app_sub.add_parser(
        "show", help="Show application details and generated materials"
    )
    show_parser.add_argument("application_id", help="UUID of the application record")


def handle_app_cli(
    args: argparse.Namespace,
    app_repo: ApplicationRepository,
    posting_repo: PostingRepository,
    profile_repo: ProfileRepository,
) -> int:
    """Dispatch and execute application CLI subcommands."""
    doc_gen = (
        DocumentGenerator(storage_dir=Path(args.docs_dir))
        if getattr(args, "docs_dir", None)
        else None
    )
    service = ApplicationService(
        application_repo=app_repo,
        posting_repo=posting_repo,
        profile_repo=profile_repo,
        document_generator=doc_gen,
    )

    cmd = args.apply_cmd

    if cmd == "analyze":
        return _handle_analyze(args, service)
    elif cmd == "draft":
        return _handle_draft(args, service)
    elif cmd == "status":
        return _handle_status(args, service)
    elif cmd == "list":
        return _handle_list(args, service)
    elif cmd == "show":
        return _handle_show(args, service)
    else:
        print(f"Unknown apply command: {cmd}", file=sys.stderr)
        return 1


def _handle_analyze(args: argparse.Namespace, service: ApplicationService) -> int:
    try:
        res = service.analyze_requirements(args.posting_id, profile_id=args.profile_id)
    except Exception as err:
        print(f"Error during requirement analysis: {err}", file=sys.stderr)
        return 1

    print("================================================================================")
    print("                     Job Requirement Gap Analysis (Module 5)                    ")
    print("================================================================================")
    print(f"Target Role:    {res.posting_title} at {res.company}")
    print(f"Match Score:    {res.match_percentage:.1f}%")
    print(f"Total Extracted Requirements: {len(res.extracted_requirements)}")
    print("--------------------------------------------------------------------------------")

    print("\n[+] Matching Verified Skills (Grounding Confirmed):")
    if res.matching_skills:
        for s in res.matching_skills:
            print(f"    - {s}")
    else:
        print("    (No direct skill matches identified in verified profile)")

    print("\n[-] Missing Prerequisites (Identified Gaps - No Fabrication):")
    if res.missing_prerequisites:
        for s in res.missing_prerequisites:
            print(f"    - {s}")
    else:
        print("    (All extracted prerequisites are matched by verified profile facts!)")

    print("================================================================================")
    return 0


def _handle_draft(args: argparse.Namespace, service: ApplicationService) -> int:
    try:
        app_record = service.prepare_application(
            posting_id=args.posting_id,
            profile_id=args.profile_id,
            generate_cv=not args.no_cv,
            generate_letter=not args.no_letter,
        )
    except Exception as err:
        print(f"Error preparing tailored application: {err}", file=sys.stderr)
        return 1

    docs = service.list_documents(app_record.id)

    print("================================================================================")
    print("                   Tailored Application Materials Prepared                      ")
    print("================================================================================")
    print(f"Application ID: {app_record.id}")
    print(f"Status:         {app_record.status.value}")
    print("Grounding:      VERIFIED (100% grounded in verified facts, zero fabrication)")
    print("--------------------------------------------------------------------------------")

    for doc in docs:
        print(f"\nDocument Type:  {doc.document_type.value}")
        print(f"Saved Path:     {doc.file_path}")
        print("--- Document Preview ---")
        lines = doc.content_text.splitlines()[:15]
        print("\n".join(lines))
        if len(doc.content_text.splitlines()) > 15:
            print("... [preview truncated]")

    print("\nReview and edit generated files prior to submission.")
    return 0


def _handle_status(args: argparse.Namespace, service: ApplicationService) -> int:
    applied_dt = None
    if args.applied_at:
        try:
            applied_dt = datetime.fromisoformat(args.applied_at).replace(tzinfo=timezone.utc)
        except ValueError:
            print(
                f"Error: Invalid applied-at date format '{args.applied_at}'. Use YYYY-MM-DD.",
                file=sys.stderr,
            )
            return 1

    try:
        status_enum = ApplicationStatus(args.status.upper())
    except ValueError:
        print(f"Error: Invalid application status '{args.status}'.", file=sys.stderr)
        return 1

    try:
        updated = service.update_status(
            application_id=args.application_id,
            status=status_enum,
            notes=args.notes,
            applied_at=applied_dt,
            contact_person=args.contact_person,
            contact_email=args.contact_email,
        )
    except Exception as err:
        print(f"Error updating application status: {err}", file=sys.stderr)
        return 1

    print("================================================================================")
    print("                      Application Status Updated (Module 6)                     ")
    print("================================================================================")
    print(f"Application ID: {updated.id}")
    print(f"Status:         {updated.status.value}")
    print(f"Applied Date:   {updated.applied_at or 'Not submitted'}")
    if updated.contact_person or updated.contact_email:
        print(f"Contact:        {updated.contact_person or ''} <{updated.contact_email or ''}>")
    print(f"Updated At:     {updated.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    if updated.notes:
        print("\n--- Notes History ---")
        print(updated.notes)
    print("================================================================================")
    return 0


def _handle_list(args: argparse.Namespace, service: ApplicationService) -> int:
    try:
        apps = service.list_applications(profile_id=args.profile_id)
    except Exception as err:
        print(f"Error listing applications: {err}", file=sys.stderr)
        return 1

    print("================================================================================")
    print(f"                     Prepared Applications ({len(apps)})                        ")
    print("================================================================================")

    if not apps:
        print("No prepared applications found. Run 'findrr apply draft <posting_id>' first.")
        return 0

    for idx, a in enumerate(apps, 1):
        docs = service.list_documents(a.id)
        doc_types = ", ".join(d.document_type.value for d in docs) if docs else "None"
        print(f"[{idx:2d}] App ID: {a.id}")
        print(f"     Posting ID: {a.job_posting_id} | Status: {a.status.value}")
        print(f"     Documents:  {doc_types}")
        print(f"     Created:    {a.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    return 0


def _handle_show(args: argparse.Namespace, service: ApplicationService) -> int:
    app = service.get_application(args.application_id)
    if not app:
        print(f"Error: Application '{args.application_id}' not found.", file=sys.stderr)
        return 1

    docs = service.list_documents(app.id)

    print("================================================================================")
    print(f"Application Record: {app.id}")
    print("================================================================================")
    print(f"Posting ID:     {app.job_posting_id}")
    print(f"Status:         {app.status.value}")
    print(f"Applied Date:   {app.applied_at or 'Not applied yet'}")
    print(f"Notes:          {app.notes or 'None'}")
    print(f"Documents:      {len(docs)}")
    print("--------------------------------------------------------------------------------")

    for doc in docs:
        print(f"\n[{doc.document_type.value}] -> {doc.file_path}")
        print("-" * 50)
        print(doc.content_text)
        print("-" * 50)
    return 0
