"""CLI commands for search term generation and validation (Module 3)."""

import argparse
import sys
from typing import Optional

from findrr.db.repository import (
    ProfileRepository,
    SearchConfigRepository,
    SearchTermRepository,
    TitleRepository,
)
from findrr.ml.registry import ModelRegistry
from findrr.services.inference_service import InferenceService
from findrr.services.search_term_service import (
    MockInferenceNotAllowedError,
    SearchTermService,
)


def register_terms_subparsers(subparsers: argparse._SubParsersAction) -> None:
    terms_parser = subparsers.add_parser(
        "terms", help="Generate and review alternative search terms (Module 3)"
    )
    terms_sub = terms_parser.add_subparsers(dest="terms_cmd", required=True)

    gen = terms_sub.add_parser(
        "generate", help="Expand the active title (Model 1) and validate terms (Model 2)"
    )
    gen.add_argument("--profile-id", help="Profile ID (defaults to the first profile)")
    gen.add_argument(
        "--allow-mock",
        action="store_true",
        default=False,
        help="Allow labelled MOCK inference when artifacts are missing (testing only; "
        "MOCK terms are never used for live searches)",
    )

    lst = terms_sub.add_parser("list", help="List generated terms and validation outcomes")
    lst.add_argument("--profile-id", help="Profile ID (defaults to the first profile)")


def handle_terms_cli(
    args: argparse.Namespace,
    profile_repo: ProfileRepository,
    title_repo: TitleRepository,
    config_repo: SearchConfigRepository,
    inference: Optional[InferenceService] = None,
) -> int:
    profile_id = args.profile_id
    if not profile_id:
        profiles = profile_repo.list_profiles()
        if not profiles:
            print("No profiles found. Run 'findrr onboard' first.", file=sys.stderr)
            return 1
        profile_id = profiles[0].id

    service = SearchTermService(
        inference=inference or InferenceService(registry=ModelRegistry()),
        profile_repo=profile_repo,
        title_repo=title_repo,
        term_repo=SearchTermRepository(profile_repo.conn),
        config_repo=config_repo,
    )

    if args.terms_cmd == "generate":
        try:
            result = service.generate_for_profile(profile_id, allow_mock=args.allow_mock)
        except MockInferenceNotAllowedError as err:
            print(f"[MODEL ARTIFACTS UNAVAILABLE] {err}", file=sys.stderr)
            return 1
        except ValueError as err:
            print(f"Error: {err}", file=sys.stderr)
            return 1
        tag = "[MOCK INFERENCE - NOT USED FOR LIVE SEARCH]" if result.is_mock else "[VERIFIED]"
        print(f"\n{tag} Search terms for: {result.primary_title}")
        _print_terms(result.terms)
        print(f"\nAccepted: {len(result.accepted)} of {len(result.terms)} candidates")
        for note in result.diagnostics:
            print(f"Note: {note}")
        return 0

    if args.terms_cmd == "list":
        terms = service.list_for_profile(profile_id)
        if not terms:
            print("No search terms yet. Run 'findrr terms generate'.")
            return 0
        _print_terms(terms)
        return 0

    print(f"Unknown terms command: {args.terms_cmd}", file=sys.stderr)
    return 1


def _print_terms(terms) -> None:
    for t in terms:
        mock = " MOCK" if t.is_mock else ""
        print(
            f"  [{t.validation_status.value:<18}] {t.generated_term:<35} "
            f"score={t.similarity_score:.3f} search={t.search_status.value}{mock}"
        )
