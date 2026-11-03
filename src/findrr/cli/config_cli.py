"""Interactive CLI prompts and handlers for search configuration."""

from typing import Callable, Optional

from findrr.models.search_config import (
    RemotePreference,
    SearchConfiguration,
    SearchConfigurationCreate,
    SeniorityLevel,
)
from findrr.services.search_config_service import SearchConfigService


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


def run_search_config_prompt(
    config_service: SearchConfigService,
    profile_id: str,
    input_fn: Optional[Callable[[str], str]] = None,
    print_fn: Optional[Callable[..., None]] = None,
) -> Optional[SearchConfiguration]:
    """Run interactive prompt to setup search preferences and bounds."""
    if input_fn is None:
        input_fn = input
    if print_fn is None:
        print_fn = print
    print_fn("\n" + "=" * 60)
    print_fn("   Findrr: Search Configuration Setup (US-003)")
    print_fn("=" * 60)

    locs_raw = _input(
        "Target Locations (comma-separated, e.g. London, Remote, Cape Town)",
        default="Remote",
        input_fn=input_fn,
    )
    locations = [loc.strip() for loc in locs_raw.split(",") if loc.strip()]

    print_fn("Remote Preferences: 1: ANY, 2: REMOTE, 3: HYBRID, 4: ON_SITE")
    pref_choice = _input("Select preference", default="1", input_fn=input_fn)
    pref_map = {
        "1": RemotePreference.ANY,
        "2": RemotePreference.REMOTE,
        "3": RemotePreference.HYBRID,
        "4": RemotePreference.ON_SITE,
    }
    remote_pref = pref_map.get(pref_choice, RemotePreference.ANY)

    print_fn("Seniority Level: 1: ANY, 2: ENTRY, 3: MID, 4: SENIOR, 5: LEAD")
    sen_choice = _input("Select seniority level", default="1", input_fn=input_fn)
    sen_map = {
        "2": SeniorityLevel.ENTRY,
        "3": SeniorityLevel.MID,
        "4": SeniorityLevel.SENIOR,
        "5": SeniorityLevel.LEAD,
    }
    seniority = sen_map.get(sen_choice, None)

    min_comp_str = _input(
        "Minimum Desired Annual Compensation (numeric, or press Enter to skip)",
        default="",
        input_fn=input_fn,
    )
    min_comp = float(min_comp_str) if min_comp_str else None
    currency = _input("Currency", default="USD", input_fn=input_fn).upper()

    print_fn("\nSearch Limit Bounds (strictly between 2 and 10 results per title):")
    while True:
        min_res_str = _input("Minimum results per title (2 to 10)", default="2", input_fn=input_fn)
        max_res_str = _input("Maximum results per title (2 to 10)", default="10", input_fn=input_fn)
        try:
            min_res = int(min_res_str)
            max_res = int(max_res_str)
            if not (2 <= min_res <= 10 and 2 <= max_res <= 10):
                print_fn("Both limits must be within 2 and 10.")
                continue
            if min_res > max_res:
                print_fn("Minimum results cannot exceed maximum results.")
                continue
            break
        except ValueError:
            print_fn("Please enter valid integers between 2 and 10.")

    config_create = SearchConfigurationCreate(
        profile_id=profile_id,
        target_locations=locations,
        remote_preference=remote_pref,
        seniority_level=seniority,
        min_compensation=min_comp,
        currency=currency,
        min_results_per_title=min_res,
        max_results_per_title=max_res,
    )

    saved = config_service.save_configuration(config_create)
    print_fn(f"\n[SUCCESS] Search configuration saved! Profile ID: {saved.profile_id}")
    return saved


def display_search_config(
    config_service: SearchConfigService,
    profile_id: str,
    print_fn: Callable[..., None] = print,
) -> None:
    """Display active search configuration."""
    cfg = config_service.get_configuration(profile_id)
    if not cfg:
        print_fn(f"No search configuration found for profile {profile_id}.")
        return

    print_fn("\n" + "=" * 60)
    print_fn("   Search Configuration")
    print_fn("=" * 60)
    print_fn(f"Profile ID:             {cfg.profile_id}")
    locs_str = ", ".join(cfg.target_locations) if cfg.target_locations else "None"
    print_fn(f"Target Locations:       {locs_str}")
    print_fn(f"Remote Preference:      {cfg.remote_preference.value}")
    sen_str = cfg.seniority_level.value if cfg.seniority_level else "Any"
    print_fn(f"Seniority Level:        {sen_str}")
    print_fn(
        f"Min Compensation:       {cfg.min_compensation} {cfg.currency}"
        if cfg.min_compensation
        else "Not specified"
    )
    bounds_str = f"{cfg.min_results_per_title} to {cfg.max_results_per_title} postings"
    print_fn(f"Search Bounds per Title: {bounds_str}")
