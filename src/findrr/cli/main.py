"""Main entrypoint for Findrr CLI."""

import argparse
import sys
from typing import List, Optional

from findrr.cli.app_cli import handle_app_cli, register_app_subparsers
from findrr.cli.config_cli import display_search_config, run_search_config_prompt
from findrr.cli.profile_cli import handle_synthesize_title, run_interactive_questionnaire
from findrr.cli.search_cli import handle_search_cli, register_search_subparsers
from findrr.db.connection import get_connection, init_db
from findrr.db.repository import (
    ApplicationRepository,
    PostingRepository,
    ProfileRepository,
    SearchConfigRepository,
    TitleRepository,
)
from findrr.ml.registry import ModelRegistry
from findrr.services.inference_service import InferenceService
from findrr.services.profile_service import ProfileService
from findrr.services.search_config_service import SearchConfigService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="findrr",
        description="Findrr: Employment Search & Application Preparation Assistant",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Custom path to SQLite database file (default: data/findrr.db or $FINDRR_DB_PATH)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: init-db
    subparsers.add_parser("init-db", help="Initialize the SQLite database schema")

    # Command: onboard
    subparsers.add_parser(
        "onboard", help="Run full onboarding wizard (profile -> title synthesis -> search config)"
    )

    # Subparser: profile
    profile_parser = subparsers.add_parser("profile", help="Manage user profiles")
    profile_sub = profile_parser.add_subparsers(dest="profile_action", help="Profile actions")

    profile_sub.add_parser("create", help="Interactive profile questionnaire (US-001)")
    profile_sub.add_parser("list", help="List all registered profiles")

    show_parser = profile_sub.add_parser("show", help="Display details of a profile")
    show_parser.add_argument(
        "profile_id",
        nargs="?",
        default=None,
        help="Profile ID (optional if only one profile exists)",
    )

    synth_parser = profile_sub.add_parser(
        "synthesize", help="Synthesize generalized job title (US-002)"
    )
    synth_parser.add_argument(
        "profile_id",
        nargs="?",
        default=None,
        help="Profile ID (optional if only one profile exists)",
    )

    verify_parser = profile_sub.add_parser("verify", help="Verify a profile entry (FR-004)")
    verify_parser.add_argument("entry_id", help="Profile Entry UUID to verify")

    # Subparser: config
    config_parser = subparsers.add_parser("config", help="Manage search preferences and bounds")
    config_sub = config_parser.add_subparsers(dest="config_action", help="Config actions")

    set_config_parser = config_sub.add_parser(
        "set", help="Interactive search configuration setup (US-003)"
    )
    set_config_parser.add_argument(
        "profile_id", nargs="?", default=None, help="Profile ID (optional if only one exists)"
    )

    show_config_parser = config_sub.add_parser("show", help="Display active search configuration")
    show_config_parser.add_argument(
        "profile_id", nargs="?", default=None, help="Profile ID (optional if only one exists)"
    )

    # Subparser: model
    model_parser = subparsers.add_parser("model", help="Manage and inspect ML models (Module 9)")
    model_sub = model_parser.add_subparsers(dest="model_action", help="Model actions")

    model_sub.add_parser("list", help="List registered ML models and integrity status")

    inspect_parser = model_sub.add_parser("inspect", help="Inspect model artifacts and checksums")
    inspect_parser.add_argument("model_id", help="Model ID (e.g. ML-001, ML-002)")

    expand_parser = model_sub.add_parser("expand", help="Test title expansion inference")
    expand_parser.add_argument("title", help="Generalized job title to expand")
    expand_parser.add_argument("--skills", default="", help="Comma-separated skills")
    expand_parser.add_argument("--seniority", default=None, help="Seniority level")

    compare_parser = model_sub.add_parser("compare", help="Test semantic similarity scoring")
    compare_parser.add_argument("text_a", help="First title or text")
    compare_parser.add_argument("text_b", help="Second title or text")

    # Subparser: search (Module 4)
    register_search_subparsers(subparsers)

    # Subparser: apply (Module 5)
    register_app_subparsers(subparsers)

    return parser


def main(args: Optional[List[str]] = None) -> int:
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 0

    conn = get_connection(parsed_args.db_path)
    init_db(conn)

    profile_repo = ProfileRepository(conn)
    title_repo = TitleRepository(conn)
    config_repo = SearchConfigRepository(conn)
    posting_repo = PostingRepository(conn)
    app_repo = ApplicationRepository(conn)

    profile_service = ProfileService(profile_repo, title_repo)
    config_service = SearchConfigService(config_repo, profile_repo)

    if parsed_args.command == "init-db":
        print("Database schema successfully initialized.")
        return 0

    elif parsed_args.command == "onboard":
        print("\n=== Welcome to Findrr CLI Onboarding Wizard ===")
        profile = run_interactive_questionnaire(profile_service)
        if not profile:
            print("Onboarding aborted.")
            return 1
        handle_synthesize_title(profile_service, profile.id)
        run_search_config_prompt(config_service, profile.id)
        print("\n=== Onboarding Complete! You are ready for job discovery. ===")
        return 0

    elif parsed_args.command == "profile":
        action = parsed_args.profile_action
        if action == "create":
            run_interactive_questionnaire(profile_service)
            return 0
        elif action == "list":
            profiles = profile_service.list_profiles()
            if not profiles:
                print("No profiles found.")
                return 0
            print("\nRegistered Profiles:")
            for p in profiles:
                info_line = (
                    f"  ID: {p.id} | Name: {p.full_name} | "
                    f"Email: {p.email} | Entries: {len(p.entries)}"
                )
                print(info_line)
            return 0
        elif action == "show":
            pid = parsed_args.profile_id
            if not pid:
                profiles = profile_service.list_profiles()
                if not profiles:
                    print("No profiles found.")
                    return 0
                pid = profiles[0].id
            p = profile_service.get_profile(pid)
            if not p:
                print(f"Profile {pid} not found.")
                return 1
            print(f"\nProfile: {p.full_name} ({p.id})")
            print(f"Email: {p.email} | Phone: {p.phone or 'N/A'} | Location: {p.location or 'N/A'}")
            print(f"Summary: {p.professional_summary or 'N/A'}")
            print(f"\nEntries ({len(p.entries)}):")
            for e in p.entries:
                ver_status = "[VERIFIED]" if e.is_verified else "[UNVERIFIED]"
                org_str = f" @ {e.organization}" if e.organization else ""
                print(f"  - {ver_status} [{e.category.value}] {e.title}{org_str} (ID: {e.id})")
            return 0
        elif action == "synthesize":
            handle_synthesize_title(profile_service, parsed_args.profile_id)
            return 0
        elif action == "verify":
            ok = profile_service.verify_entry(parsed_args.entry_id, True)
            if ok:
                print(f"Entry {parsed_args.entry_id} marked as verified.")
                return 0
            else:
                print(f"Entry {parsed_args.entry_id} not found.")
                return 1
        else:
            parser.parse_args(["profile", "--help"])
            return 0

    elif parsed_args.command == "config":
        action = parsed_args.config_action
        if action == "set":
            pid = parsed_args.profile_id
            if not pid:
                profiles = profile_service.list_profiles()
                if not profiles:
                    print("No profiles found. Create a profile first.")
                    return 1
                pid = profiles[0].id
            run_search_config_prompt(config_service, pid)
            return 0
        elif action == "show":
            pid = parsed_args.profile_id
            if not pid:
                profiles = profile_service.list_profiles()
                if not profiles:
                    print("No profiles found.")
                    return 1
                pid = profiles[0].id
            display_search_config(config_service, pid)
            return 0
        else:
            parser.parse_args(["config", "--help"])
            return 0

    elif parsed_args.command == "model":
        ml_registry = ModelRegistry()
        inf_service = InferenceService(registry=ml_registry)
        action = parsed_args.model_action

        if action == "list":
            print("\nRegistered Machine Learning Models (Module 9 Catalog):")
            print("-" * 75)
            for reg in ml_registry.list_registrations():
                status = ml_registry.inspect_model_status(reg.model_id)
                tag = "[VERIFIED ARTIFACTS]" if status["integrity_verified"] else "[MOCK / PENDING]"
                print(f"  {reg.model_id:<8} {reg.name:<24} v{reg.active_version:<6} {tag}")
                print(f"           Architecture: {reg.architecture}")
                print(f"           Purpose:      {reg.purpose}")
            print("-" * 75)
            return 0

        elif action == "inspect":
            mid = parsed_args.model_id
            try:
                status = ml_registry.inspect_model_status(mid)
                print(f"\nModel Inspection: {status['model_id']} ({status['name']})")
                print(f"Version:            {status['version']}")
                print(f"Artifact Path:      {status['path']}")
                print(f"Manifest Exists:    {'Yes' if status['manifest_exists'] else 'No'}")
                print(f"Artifacts Present:  {'Yes' if status['artifacts_present'] else 'No'}")
                print(f"Integrity Verified: {'Yes' if status['integrity_verified'] else 'No'}")
                if status.get("evaluation_summary"):
                    print(f"Evaluation Summary: {status['evaluation_summary']}")
                if status.get("error"):
                    print(f"Status Note:        {status['error']}")
                return 0
            except Exception as exc:
                print(f"Error inspecting model: {exc}")
                return 1

        elif action == "expand":
            skills = [s.strip() for s in parsed_args.skills.split(",") if s.strip()]
            res = inf_service.expand_titles(
                generalized_title=parsed_args.title,
                skills=skills,
                seniority=parsed_args.seniority,
            )
            mode_tag = "[MOCK INFERENCE]" if res.is_mock else "[VERIFIED MODEL]"
            print(f"\n{mode_tag} Title Expansion for: {res.generalized_title}")
            print(f"Model ID / Version: {res.model_id} v{res.model_version}")
            print("Candidate Titles:")
            for cand in res.expanded_titles:
                print(f"  - {cand}")
            return 0

        elif action == "compare":
            res = inf_service.evaluate_similarity(parsed_args.text_a, parsed_args.text_b)
            mode_tag = "[MOCK INFERENCE]" if res.is_mock else "[VERIFIED MODEL]"
            print(f"\n{mode_tag} Semantic Similarity")
            print(f"Model ID / Version: {res.model_id} v{res.model_version}")
            print(f"Text A: {res.text_a!r}")
            print(f"Text B: {res.text_b!r}")
            print(f"Similarity Score: {res.similarity_score:.4f}")
            return 0

        else:
            parser.parse_args(["model", "--help"])
            return 0

    elif parsed_args.command == "search":
        return handle_search_cli(
            args=parsed_args,
            posting_repo=posting_repo,
            profile_repo=profile_repo,
            title_repo=title_repo,
            config_repo=config_repo,
        )

    elif parsed_args.command == "apply":
        return handle_app_cli(
            args=parsed_args,
            app_repo=app_repo,
            posting_repo=posting_repo,
            profile_repo=profile_repo,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
