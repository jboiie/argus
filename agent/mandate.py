"""Mandate / authorization layer - logged before any payment-link action.

In-memory store for now (Supabase logging is build step 14). Field shape
matches DataModel.md Entity 3 exactly: status is set once at creation by
this real-time check and is immutable - a later bypass finding is recorded
separately (bypass_confirmed_at), never by overwriting status.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

MANDATE_TTL_MINUTES = 15

_MANDATES: list["Mandate"] = []

# Challenge-response state for the confirmation gate. Keyed by session_id.
#
# The gate used to accept any affirmative-looking keyword in the user's
# latest turn, which redteam/mandate_attacks.py showed is bypassable three
# different ways (a claim about a past confirmation, a forged SYSTEM
# MESSAGE, a third party's approval) - 50% ASR. Pattern-matching user text
# can't distinguish "I authorize this now" from "someone else authorized
# this already", and no blocklist closes that gap in general.
#
# So authorization is two-phase instead: the BACKEND records that it asked
# (solicit_confirmation, quoting the real server-computed amount), and only
# an affirmative given while that challenge is outstanding counts. An
# unsolicited assertion of confirmation is never sufficient, no matter how
# it's worded, because nothing asked for it.
_PENDING_CONFIRMATIONS: dict[str, dict] = {}


def solicit_confirmation(session_id: str, amount: int, line_items: list[dict]) -> None:
    """Record that the backend has asked this session to confirm `amount`."""
    _PENDING_CONFIRMATIONS[session_id] = {"amount": amount, "line_items": line_items}


def pending_confirmation(session_id: str) -> dict | None:
    return _PENDING_CONFIRMATIONS.get(session_id)


def clear_confirmation(session_id: str) -> None:
    _PENDING_CONFIRMATIONS.pop(session_id, None)


@dataclass
class Mandate:
    mandate_id: str
    run_id: str
    session_id: str
    scope: str  # purchase | refund | discount_application
    amount: int  # paise, post-discount total
    line_items: list[dict]  # [{"product_id": str, "quantity": int}, ...]
    coupon_code: str | None
    authorized_at: datetime
    expires_at: datetime
    user_confirmed: bool
    status: str  # authorized | denied
    bypass_confirmed_at: datetime | None = None
    is_live_demo: bool = False
    real_call_fired: bool = False
    product_id: str | None = None  # deprecated - kept only for reading old pre-cart rows, new code never sets it


def create_mandate(
    run_id: str,
    session_id: str,
    scope: str,
    amount: int,
    line_items: list[dict],
    coupon_code: str | None,
    user_confirmed: bool,
    is_live_demo: bool = False,
) -> Mandate:
    now = datetime.now(timezone.utc)
    mandate = Mandate(
        mandate_id=str(uuid.uuid4()),
        run_id=run_id,
        session_id=session_id,
        scope=scope,
        amount=amount,
        line_items=line_items,
        coupon_code=coupon_code,
        authorized_at=now,
        expires_at=now + timedelta(minutes=MANDATE_TTL_MINUTES),
        user_confirmed=user_confirmed,
        status="authorized" if user_confirmed else "denied",
        is_live_demo=is_live_demo,
    )
    _MANDATES.append(mandate)
    return mandate


def is_valid(mandate: Mandate) -> bool:
    return mandate.status == "authorized" and datetime.now(timezone.utc) < mandate.expires_at


def demo():
    items = [{"product_id": "prod_001", "quantity": 1}]
    m1 = create_mandate("run_dev", "sess_1", "purchase", 349900, items, None, user_confirmed=True)
    assert m1.status == "authorized"
    assert is_valid(m1)

    m2 = create_mandate("run_dev", "sess_1", "purchase", 349900, items, None, user_confirmed=False)
    assert m2.status == "denied"
    assert not is_valid(m2)

    assert pending_confirmation("sess_pending") is None
    solicit_confirmation("sess_pending", 349900, items)
    assert pending_confirmation("sess_pending")["amount"] == 349900
    clear_confirmation("sess_pending")
    assert pending_confirmation("sess_pending") is None, "a spent challenge must not linger"

    print(f"authorized mandate: {m1.mandate_id} expires_at={m1.expires_at.isoformat()}")
    print(f"denied mandate: {m2.mandate_id}")


if __name__ == "__main__":
    demo()
