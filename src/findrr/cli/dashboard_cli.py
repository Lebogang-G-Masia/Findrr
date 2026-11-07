"""CLI commands for search and application pipeline dashboard (Module 7, FR-025)."""

import argparse
import sys

from findrr.db.repository import ApplicationRepository, PostingRepository, ProfileRepository
from findrr.services.dashboard_service import DashboardService


def register_dashboard_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Register dashboard subcommands."""
    dash_parser = subparsers.add_parser(
        "dashboard", help="Employment search & application pipeline dashboard (Module 7)"
    )
    dash_parser.add_argument("--profile-id", help="Target profile ID (defaults to active profile)")


def handle_dashboard_cli(
    args: argparse.Namespace,
    app_repo: ApplicationRepository,
    posting_repo: PostingRepository,
    profile_repo: ProfileRepository,
) -> int:
    """Execute dashboard CLI command."""
    service = DashboardService(
        application_repo=app_repo,
        posting_repo=posting_repo,
        profile_repo=profile_repo,
    )

    try:
        metrics = service.get_dashboard_metrics(profile_id=args.profile_id)
    except Exception as err:
        print(f"Error generating dashboard: {err}", file=sys.stderr)
        return 1

    print("================================================================================")
    print("                 Findrr Job Search & Application Dashboard                      ")
    print("================================================================================")

    # 1. Search Discovery
    print("\n[+] Opportunity Discovery & Search Metrics (Module 4):")
    print(f"    Total Postings Tracked:   {metrics.total_postings}")
    print(f"    Active Postings:          {metrics.active_postings}")
    print(f"    Closed Postings:          {metrics.closed_postings}")
    print(f"    Unique Employers:         {metrics.unique_companies}")

    if metrics.top_companies:
        top_str = ", ".join(f"{c['company']} ({c['count']})" for c in metrics.top_companies[:3])
        print(f"    Top Hiring Employers:     {top_str}")

    # 2. Application Pipeline Stages
    pipe = metrics.pipeline_counts
    print("\n[+] Application Pipeline Progression (Module 6 & 7):")
    print(f"    [1] Discovered:           {pipe.get('DISCOVERED', 0)}")
    print(f"    [2] Saved / Prepared:     {pipe.get('SAVED', 0)}")
    print(f"    [3] Submitted (Applied):  {pipe.get('APPLIED', 0)}")
    print(f"    [4] Interviewing:         {pipe.get('INTERVIEWING', 0)}")
    print(f"    [5] Offers Received:      {pipe.get('OFFERED', 0)}")
    print(f"    [6] Rejected:             {pipe.get('REJECTED', 0)}")
    print(f"    [7] Withdrawn:            {pipe.get('WITHDRAWN', 0)}")
    print(f"    Total Tracked Records:    {pipe.get('TOTAL', 0)}")

    # 3. Conversion Rates
    print("\n[+] Pipeline Performance & Conversion Rates:")
    print(f"    Applications Submitted:   {metrics.submitted_count}")
    print(f"    Interview Rate:           {metrics.interview_rate_pct:.1f}%")
    print(f"    Offer Rate:               {metrics.offer_rate_pct:.1f}%")

    # 4. Recent Application Activity
    print("\n[+] Recent Applications:")
    if metrics.recent_activity:
        for idx, act in enumerate(metrics.recent_activity, 1):
            print(
                f"    {idx}. [{act['status']}] {act['title']} at {act['company']} "
                f"(Applied: {act['applied_at']})"
            )
    else:
        print("    (No applications prepared yet. Run 'findrr apply draft <posting_id>')")

    print("================================================================================")
    return 0
