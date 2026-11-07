"""CLI commands for job search and posting discovery (Module 4)."""

import argparse
import sys
from typing import Optional

from findrr.db.repository import (
    PostingRepository,
    ProfileRepository,
    SearchConfigRepository,
    TitleRepository,
)
from findrr.search.engine import JobDiscoveryEngine
from findrr.services.posting_service import PostingService


def register_search_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Register search command line subcommands."""
    search_parser = subparsers.add_parser("search", help="Automated job discovery commands")
    search_sub = search_parser.add_subparsers(dest="search_cmd", required=True)

    # findrr search run
    run_parser = search_sub.add_parser("run", help="Run automated job search discovery")
    run_parser.add_argument(
        "--profile-id", help="Profile ID to search for (defaults to active profile)"
    )
    run_parser.add_argument(
        "--title", help="Explicit job title to search (overrides active profile title)"
    )
    run_parser.add_argument("--min", type=int, default=2, help="Minimum results to extract [2, 10]")
    run_parser.add_argument(
        "--max", type=int, default=10, help="Maximum results to extract [2, 10]"
    )
    run_parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode (default: headful/visible GUI)",
    )

    # findrr search list
    list_parser = search_sub.add_parser("list", help="List discovered job postings")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum postings to display")

    # findrr search inspect
    inspect_parser = search_sub.add_parser("inspect", help="Inspect a specific job posting")
    inspect_parser.add_argument("posting_id", help="UUID of the job posting")


def handle_search_cli(
    args: argparse.Namespace,
    posting_repo: PostingRepository,
    profile_repo: ProfileRepository,
    title_repo: TitleRepository,
    config_repo: SearchConfigRepository,
    discovery_engine: Optional[any] = None,
) -> int:
    """Dispatch and execute search CLI subcommands."""
    engine = discovery_engine or JobDiscoveryEngine(headless=getattr(args, "headless", False))
    service = PostingService(
        posting_repo=posting_repo,
        profile_repo=profile_repo,
        title_repo=title_repo,
        config_repo=config_repo,
        discovery_engine=engine,
    )

    cmd = args.search_cmd

    if cmd == "run":
        return _run_search(args, service, profile_repo, title_repo)
    elif cmd == "list":
        return _list_postings(args, service)
    elif cmd == "inspect":
        return _inspect_posting(args, posting_repo)
    else:
        print(f"Unknown search subcommand: {cmd}", file=sys.stderr)
        return 1


def _run_search(
    args: argparse.Namespace,
    service: PostingService,
    profile_repo: ProfileRepository,
    title_repo: TitleRepository,
) -> int:
    profile_id = args.profile_id
    if not profile_id:
        profiles = profile_repo.list_profiles()
        if not profiles:
            print(
                "No profiles found. Run 'findrr onboard' or 'findrr profile create' first.",
                file=sys.stderr,
            )
            return 1
        profile_id = profiles[0].id

    print("================================================================================")
    print("                     Findrr Job Discovery Workflow (Module 4)                    ")
    print("================================================================================")

    if args.title:
        print(f"Searching explicitly for: {args.title}")
        res = service.discover_postings_for_title(
            title=args.title,
            min_results=args.min,
            max_results=args.max,
        )
    else:
        active_title = title_repo.get_active_title(profile_id)
        if not active_title:
            print(
                f"No active job title for profile {profile_id}. Synthesize one first.",
                file=sys.stderr,
            )
            return 1
        print(f"Searching for active profile title: {active_title.primary_title}")
        res = service.discover_for_profile(
            profile_id=profile_id,
            custom_min=args.min,
            custom_max=args.max,
        )

    metrics = res["metrics"]
    postings = res["postings"]

    print("\n------------------------- Discovery Session Metrics -------------------------")
    print(f"Search Query:            {metrics.query}")
    print(f"Results Retrieved:       {metrics.results_retrieved}")
    print(f"Postings Extracted:      {metrics.postings_extracted}")
    print(f"Duplicates Detected:     {metrics.duplicates_detected}")
    print(f"Unique Postings Retained:{metrics.unique_postings_retained}")
    print("-----------------------------------------------------------------------------")

    if not postings:
        print(
            "\nNo postings were retained for this query. "
            "(Zero synthetic results fabricated per FR-017)"
        )
        return 0

    print(f"\nRetained Opportunities ({len(postings)}):")
    for idx, p in enumerate(postings, 1):
        print(f"\n[{idx}] {p.title} at {p.company}")
        if p.location:
            print(f"    Location:   {p.location}")
        print(f"    Status:     {p.status.value}")
        print(f"    Apply URL:  {p.direct_apply_url or p.source_url}")
        if p.requirements_extracted:
            print(f"    Skills:     {', '.join(p.requirements_extracted[:6])}")
        print(f"    Posting ID: {p.id}")

    return 0


def _list_postings(args: argparse.Namespace, service: PostingService) -> int:
    postings = service.list_postings(limit=args.limit)
    print("================================================================================")
    print(f"                       Discovered Job Postings ({len(postings)})                     ")
    print("================================================================================")

    if not postings:
        print(
            "No job postings found in database. Run 'findrr search run' to discover opportunities."
        )
        return 0

    for idx, p in enumerate(postings, 1):
        loc = f" | {p.location}" if p.location else ""
        print(f"[{idx:2d}] {p.title} @ {p.company}{loc} [{p.status.value}]")
        print(f"     Apply: {p.direct_apply_url or p.source_url}")
        print(f"     ID:    {p.id}")
    return 0


def _inspect_posting(args: argparse.Namespace, posting_repo: PostingRepository) -> int:
    p = posting_repo.get_posting(args.posting_id)
    if not p:
        print(f"Error: Posting '{args.posting_id}' not found.", file=sys.stderr)
        return 1

    print("================================================================================")
    print(f"Job Posting: {p.title}")
    print("================================================================================")
    print(f"Company:      {p.company}")
    print(f"Location:     {p.location or 'Not specified'}")
    print(f"Status:       {p.status.value}")
    print(f"Posted:       {p.posting_date or 'Unknown'}")
    print(f"Discovered:   {p.discovered_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Apply URL:    {p.direct_apply_url or 'N/A'}")
    print(f"Source URL:   {p.source_url}")
    print(f"Content Hash: {p.content_hash}")
    if p.requirements_extracted:
        print(f"Extracted Skills: {', '.join(p.requirements_extracted)}")
    print("\n--- Description ---")
    print(p.description[:2000] + ("..." if len(p.description) > 2000 else ""))
    return 0
