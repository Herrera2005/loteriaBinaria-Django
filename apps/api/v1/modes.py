from __future__ import annotations

from dataclasses import dataclass

from apps.accounts.policies import assigned_role_codes
from apps.accounts.roles import (
    ADMINISTRATOR,
    CLIENT,
    ROLE_CODES,
    VENDOR,
)


ACTIVE_MODE_HEADER = "X-Active-Mode"


@dataclass(frozen=True)
class ActiveModeResolution:
    requested_mode: str | None
    active_mode: str | None
    available_modes: tuple[str, ...]


def normalize_active_mode(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().upper()

    if not normalized:
        return None

    return normalized


def available_modes_for_user(user) -> tuple[str, ...]:
    return tuple(
        assigned_role_codes(user)
    )


def is_valid_mode(mode: str | None) -> bool:
    return bool(
        mode
        and mode in ROLE_CODES
    )


def user_can_operate_as(user, mode: str | None) -> bool:
    if not is_valid_mode(mode):
        return False

    return mode in available_modes_for_user(user)


def resolve_active_mode(
    user,
    requested_mode: str | None,
) -> ActiveModeResolution:
    normalized_mode = normalize_active_mode(
        requested_mode
    )

    available_modes = available_modes_for_user(
        user
    )

    active_mode = None

    if (
        normalized_mode is not None
        and normalized_mode in available_modes
    ):
        active_mode = normalized_mode

    return ActiveModeResolution(
        requested_mode=normalized_mode,
        active_mode=active_mode,
        available_modes=available_modes,
    )