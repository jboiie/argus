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


@dataclass
class Mandate:
    mandate_id: str
    run_id: str
    session_id: str
    scope: str  # purchase | refund | discount_application
    amount: int  # paise
    product_id: str | None
    authorized_at: datetime
    expires_at: datetime
    user_confirmed: bool
    status: str  # authorized | denied
    bypass_confirmed_at: datetime | None = None
    is_live_demo: bool = False
    real_call_fired: bool = False


def create_mandate(
    run_id: str,
    session_id: str,
    scope: str,
    amount: int,
    product_id: str | None,
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
        product_id=product_id,
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
    m1 = create_mandate("run_dev", "sess_1", "purchase", 349900, "prod_001", user_confirmed=True)
    assert m1.status == "authorized"
    assert is_valid(m1)

    m2 = create_mandate("run_dev", "sess_1", "purchase", 349900, "prod_001", user_confirmed=False)
    assert m2.status == "denied"
    assert not is_valid(m2)

    print(f"authorized mandate: {m1.mandate_id} expires_at={m1.expires_at.isoformat()}")
    print(f"denied mandate: {m2.mandate_id}")


if __name__ == "__main__":
    demo()
