"""Active profile selection for multi-profile support (US-017, FR-001 enhancement).

Commands that are not given an explicit profile ID act on the *active* profile. With a
single profile it is used automatically. With several profiles and none marked active,
commands stop and ask the user to choose, instead of silently picking one.
"""

import sqlite3
from typing import Optional

from findrr.db.repository import ProfileRepository

ACTIVE_PROFILE_KEY = "active_profile_id"


class ProfileSelectionError(ValueError):
    """Raised when no profile can be selected unambiguously."""


class ActiveProfileStore:
    """Persists the active profile ID in the `app_settings` table."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get(self) -> Optional[str]:
        row = self.conn.execute(
            "SELECT value FROM app_settings WHERE key = ?", (ACTIVE_PROFILE_KEY,)
        ).fetchone()
        return row[0] if row else None

    def set(self, profile_id: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO app_settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (ACTIVE_PROFILE_KEY, profile_id),
            )

    def clear(self) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM app_settings WHERE key = ?", (ACTIVE_PROFILE_KEY,))


def resolve_profile_id(profile_repo: ProfileRepository, explicit: Optional[str] = None) -> str:
    """Return the profile to act on: the explicit ID, else the active one, else the only one."""
    if explicit:
        if not profile_repo.get_profile(explicit):
            raise ProfileSelectionError(f"Profile {explicit} not found.")
        return explicit

    store = ActiveProfileStore(profile_repo.conn)
    active = store.get()
    if active and profile_repo.get_profile(active):
        return active

    profiles = profile_repo.list_profiles()
    if not profiles:
        raise ProfileSelectionError("No profiles found. Run 'findrr onboard' first.")
    if len(profiles) == 1:
        return profiles[0].id
    raise ProfileSelectionError(
        f"{len(profiles)} profiles exist and none is active. "
        "Run 'findrr profile list', then 'findrr profile use <profile_id>', "
        "or pass the profile ID explicitly."
    )


def remember_active_after_create(profile_repo: ProfileRepository, new_profile_id: str) -> str:
    """Keep the user's current profile active when another profile is created.

    - First profile ever: it becomes active.
    - One existing profile with no stored choice: that profile was implicitly active, so it
      is stored as active (creating a second profile never silently switches commands).
    Returns the active profile ID afterwards (may be empty if the choice is ambiguous).
    """
    store = ActiveProfileStore(profile_repo.conn)
    current = store.get()
    if current and profile_repo.get_profile(current):
        return current
    others = [p.id for p in profile_repo.list_profiles() if p.id != new_profile_id]
    if not others:
        store.set(new_profile_id)
        return new_profile_id
    if len(others) == 1:
        store.set(others[0])
        return others[0]
    return ""
