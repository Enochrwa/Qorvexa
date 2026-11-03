"""The asset state machine as pure functions. Providers deliver events at-least-once and out of
order, so applying a status must be idempotent and must never move an asset backwards."""

from enum import StrEnum


class Status(StrEnum):
    CREATED = "created"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class Outcome(StrEnum):
    APPLIED = "applied"
    IGNORED = "ignored"  # duplicate or stale: nothing changes, and that is not an error


class InvalidTransition(Exception):
    """A change that must never happen (for example a ready asset failing)."""


# The happy path. A provider may skip steps (some report only "ready"), never go backwards.
_FORWARD = (Status.CREATED, Status.UPLOADING, Status.UPLOADED, Status.PROCESSING, Status.READY)
_RANK = {status: i for i, status in enumerate(_FORWARD)}
IN_FLIGHT = frozenset(_FORWARD[:-1])  # not finished: created, uploading, uploaded, processing


def decide(current: Status, target: Status) -> Outcome:
    """What applying `target` to an asset that is `current` means.

    - the same status again, or an older one arriving late: ignored
    - `deleted` is terminal: nothing resurrects it, and anything can end in it
    - `failed` is reachable from any in-flight state, not from `ready` (delete it instead)
    - a `failed` asset recovers only if the provider later says `ready` (provider truth wins,
      for example after a reconciliation timeout marked it failed too early)
    """
    if current == target or current == Status.DELETED:
        return Outcome.IGNORED
    if target == Status.DELETED:
        return Outcome.APPLIED
    if target == Status.FAILED:
        if current in IN_FLIGHT:
            return Outcome.APPLIED
        if current == Status.READY:
            raise InvalidTransition("a ready asset cannot fail; delete it instead")
        return Outcome.IGNORED  # already failed
    if current == Status.FAILED:
        return Outcome.APPLIED if target == Status.READY else Outcome.IGNORED
    return Outcome.APPLIED if _RANK[target] > _RANK[current] else Outcome.IGNORED


def can_retry(current: Status) -> bool:
    """An admin may restart only a failed asset (back to `created`, with a new upload)."""
    return current == Status.FAILED
