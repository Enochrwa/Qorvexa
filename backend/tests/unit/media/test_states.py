import random

import pytest

from app.modules.media.states import (
    IN_FLIGHT,
    InvalidTransition,
    Outcome,
    Status,
    can_retry,
    decide,
)

C, U, UP, P, R, F, D = (
    Status.CREATED,
    Status.UPLOADING,
    Status.UPLOADED,
    Status.PROCESSING,
    Status.READY,
    Status.FAILED,
    Status.DELETED,
)
A, NOP, X = Outcome.APPLIED, Outcome.IGNORED, "invalid"

# The specification, written out. Rows: current status. Columns: the status being applied.
#            created uploading uploaded processing ready failed deleted
TABLE = {
    C: [NOP, A, A, A, A, A, A],
    U: [NOP, NOP, A, A, A, A, A],
    UP: [NOP, NOP, NOP, A, A, A, A],
    P: [NOP, NOP, NOP, NOP, A, A, A],
    R: [NOP, NOP, NOP, NOP, NOP, X, A],  # a ready asset cannot fail
    F: [NOP, NOP, NOP, NOP, A, NOP, A],  # a failed asset recovers only if the provider says ready
    D: [NOP, NOP, NOP, NOP, NOP, NOP, NOP],  # deleted is terminal
}
COLUMNS = [C, U, UP, P, R, F, D]


@pytest.mark.parametrize("current", list(TABLE))
@pytest.mark.parametrize("index", range(len(COLUMNS)))
def test_transition_table(current: Status, index: int) -> None:
    target, expected = COLUMNS[index], TABLE[current][index]
    if expected == X:
        with pytest.raises(InvalidTransition):
            decide(current, target)
    else:
        assert decide(current, target) is expected


def test_the_same_status_twice_is_always_a_no_op() -> None:
    for status in Status:
        assert decide(status, status) is Outcome.IGNORED


def test_providers_may_skip_steps_but_never_go_back() -> None:
    assert decide(C, R) is Outcome.APPLIED  # some vendors only ever report "ready"
    assert decide(R, P) is Outcome.IGNORED  # a late "processing" after "ready"
    assert decide(UP, U) is Outcome.IGNORED


def test_only_failed_can_be_retried() -> None:
    assert [s for s in Status if can_retry(s)] == [F]


def test_in_flight_is_everything_that_can_still_fail() -> None:
    assert {C, U, UP, P} == IN_FLIGHT
    for status in IN_FLIGHT:
        assert decide(status, F) is Outcome.APPLIED


def _replay(events: list[Status]) -> Status:
    current = C
    for target in events:
        try:
            if decide(current, target) is Outcome.APPLIED:
                current = target
        except InvalidTransition:
            pass
    return current


def test_random_event_streams_keep_the_invariants() -> None:
    rng = random.Random(20261023)  # noqa: S311 - reproducible test data, not security
    forward = [C, U, UP, P, R]
    for _ in range(2000):
        events = [rng.choice(list(Status)) for _ in range(rng.randint(1, 12))]
        current, seen_deleted = C, False
        for target in events:
            try:
                outcome = decide(current, target)
            except InvalidTransition:
                continue
            if outcome is Outcome.APPLIED:
                before, current = current, target
                # never backwards, except failed -> ready
                if before in forward and current in forward:
                    assert forward.index(current) > forward.index(before)
                assert before is not D
            if current is D:
                seen_deleted = True
            if seen_deleted:
                assert current is D  # terminal: nothing resurrects it
        # replaying the whole stream a second time changes nothing
        assert _replay(events + events) == _replay(events)
