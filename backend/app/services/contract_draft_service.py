from __future__ import annotations

import json
import re
from collections.abc import Iterable
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.backoffice import ContractDraft, ContractDraftFact, Transaction
from app.models.user import User
from app.services import audit_service, authorization_service
from app.utils.helpers import new_uuid


REQUIRED_FACTS_BY_TRANSACTION_TYPE = {
    "purchase": (
        "buyer_names",
        "seller_names",
        "property_address",
        "sales_price",
        "earnest_money",
        "option_fee",
        "option_period_days",
        "closing_date",
        "financing_type",
    ),
    "sale": (
        "buyer_names",
        "seller_names",
        "property_address",
        "sales_price",
        "closing_date",
    ),
    "lease": (
        "landlord_names",
        "tenant_names",
        "property_address",
        "lease_start_date",
        "lease_end_date",
        "monthly_rent",
    ),
    "management": (
        "owner_names",
        "property_address",
        "management_start_date",
        "management_fee",
    ),
}

QUESTION_BY_FACT = {
    "buyer_names": "Who are the buyers exactly as they should appear on the contract?",
    "seller_names": "Who are the sellers exactly as they should appear on the contract?",
    "landlord_names": "Who are the landlords exactly as they should appear on the agreement?",
    "tenant_names": "Who are the tenants exactly as they should appear on the agreement?",
    "owner_names": "Who are the property owners exactly as they should appear on the agreement?",
    "property_address": "What is the exact subject-property address?",
    "sales_price": "What is the proposed sales price?",
    "earnest_money": "What earnest-money amount should the draft use?",
    "option_fee": "What option fee should the draft use?",
    "option_period_days": "How many days should the option period run?",
    "closing_date": "What closing date should the draft use?",
    "financing_type": "What financing type applies?",
    "lease_start_date": "When should the lease begin?",
    "lease_end_date": "When should the lease end?",
    "monthly_rent": "What monthly rent should the draft use?",
    "management_start_date": "When should property management begin?",
    "management_fee": "What management fee should the draft use?",
}

ALLOWED_SOURCE_TYPES = {"conversation", "repliers", "espocrm", "document", "user", "system"}
ALLOWED_CONFIRMATION_STATUSES = {"unconfirmed", "confirmed"}
FACT_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
MAX_FACT_VALUE_BYTES = 16_384


def _require_transaction(db: Session, *, brokerage_id: str, transaction_id: str) -> Transaction:
    transaction = db.get(Transaction, transaction_id)
    if transaction is None or transaction.brokerage_id != brokerage_id:
        raise LookupError("Transaction not found in brokerage")
    return transaction


def _fact_has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _validate_fact(
    *,
    key: str,
    value: Any,
    source_type: str,
    source_reference: str | None,
    confirmation_status: str,
) -> None:
    if not FACT_KEY_PATTERN.fullmatch(key) or len(key) > 80:
        raise ValueError("Fact key must use lowercase snake case and not exceed 80 characters")
    if source_type not in ALLOWED_SOURCE_TYPES:
        raise ValueError("Unsupported contract fact source")
    if confirmation_status not in ALLOWED_CONFIRMATION_STATUSES:
        raise ValueError("Unsupported contract fact confirmation status")
    if source_type in {"repliers", "document"} and not (source_reference or "").strip():
        raise ValueError(f"{source_type.title()} facts require a source reference")
    if source_reference and len(source_reference) > 500:
        raise ValueError("Contract fact source reference must not exceed 500 characters")
    if not _fact_has_value(value):
        raise ValueError(f"Contract fact {key} must have a value")
    try:
        encoded_value = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Contract fact {key} must be valid JSON") from exc
    if len(encoded_value) > MAX_FACT_VALUE_BYTES:
        raise ValueError(f"Contract fact {key} exceeds the maximum stored value size")


def _upsert_facts(
    db: Session,
    *,
    draft: ContractDraft,
    actor: User,
    facts: Iterable[dict[str, Any]],
) -> int:
    updated = 0
    for payload in facts:
        key = payload["key"]
        source_reference = (payload.get("source_reference") or "").strip() or None
        _validate_fact(
            key=key,
            value=payload["value"],
            source_type=payload["source_type"],
            source_reference=source_reference,
            confirmation_status=payload["confirmation_status"],
        )
        fact = db.scalars(
            select(ContractDraftFact).where(
                ContractDraftFact.contract_draft_id == draft.id,
                ContractDraftFact.fact_key == key,
            )
        ).first()
        if fact is None:
            fact = ContractDraftFact(
                id=new_uuid(),
                contract_draft_id=draft.id,
                fact_key=key,
                entered_by_user_id=actor.id,
            )
        fact.value_json = payload["value"]
        fact.source_type = payload["source_type"]
        fact.source_reference = source_reference
        fact.confirmation_status = payload["confirmation_status"]
        fact.entered_by_user_id = actor.id
        fact.confirmed_by_user_id = actor.id if fact.confirmation_status == "confirmed" else None
        db.add(fact)
        updated += 1
    return updated


def _facts_for_draft(db: Session, draft_id: str) -> list[ContractDraftFact]:
    return list(
        db.scalars(
            select(ContractDraftFact)
            .where(ContractDraftFact.contract_draft_id == draft_id)
            .order_by(ContractDraftFact.fact_key)
        ).all()
    )


def review_state(
    db: Session, *, draft: ContractDraft, transaction: Transaction | None = None
) -> tuple[str, list[str], list[str]]:
    transaction = transaction or db.get(Transaction, draft.transaction_id)
    if transaction is None:
        raise LookupError("Contract draft transaction not found")
    facts = _facts_for_draft(db, draft.id)
    fact_by_key = {fact.fact_key: fact for fact in facts}
    missing_fields: list[str] = []
    questions: list[str] = []
    if not draft.selected_form_id:
        missing_fields.append("selected_form_id")
        questions.append("Which broker-approved contract form applies to this transaction?")
    for key in REQUIRED_FACTS_BY_TRANSACTION_TYPE[transaction.transaction_type]:
        fact = fact_by_key.get(key)
        if fact is None or not _fact_has_value(fact.value_json):
            missing_fields.append(key)
            questions.append(QUESTION_BY_FACT[key])
    if missing_fields:
        return "collecting", missing_fields, questions
    if any(fact.confirmation_status != "confirmed" for fact in facts):
        return "review_required", [], [
            "Confirm every sourced fact before marking this draft ready for document preparation."
        ]
    return "review_ready", [], []


def _sync_status(db: Session, *, draft: ContractDraft, transaction: Transaction) -> None:
    status, _, _ = review_state(db, draft=draft, transaction=transaction)
    draft.status = status
    db.add(draft)


def create(
    db: Session,
    *,
    actor: User,
    brokerage_id: str,
    transaction_id: str,
    selected_form_id: str | None,
    selected_form_name: str | None,
    selected_form_effective_date: date | None,
    facts: Iterable[dict[str, Any]],
) -> ContractDraft:
    authorization_service.require_permission(
        db, user=actor, brokerage_id=brokerage_id, permission="documents.prepare"
    )
    transaction = _require_transaction(
        db, brokerage_id=brokerage_id, transaction_id=transaction_id
    )
    draft = ContractDraft(
        id=new_uuid(),
        brokerage_id=brokerage_id,
        transaction_id=transaction_id,
        selected_form_id=(selected_form_id or "").strip() or None,
        selected_form_name=(selected_form_name or "").strip() or None,
        selected_form_effective_date=selected_form_effective_date,
        status="collecting",
        created_by_user_id=actor.id,
    )
    db.add(draft)
    db.flush()
    fact_count = _upsert_facts(db, draft=draft, actor=actor, facts=facts)
    _sync_status(db, draft=draft, transaction=transaction)
    audit_service.record(
        db,
        actor=actor,
        action="contract_draft.created",
        resource_type="contract_draft",
        resource_id=draft.id,
        brokerage_id=brokerage_id,
        next_state=draft.status,
        metadata={"fact_count": fact_count, "selected_form_id": draft.selected_form_id},
    )
    db.commit()
    db.refresh(draft)
    return draft


def update(
    db: Session,
    *,
    actor: User,
    brokerage_id: str,
    draft_id: str,
    selected_form_id: str | None,
    selected_form_name: str | None,
    selected_form_effective_date: date | None,
    facts: Iterable[dict[str, Any]],
) -> ContractDraft:
    authorization_service.require_permission(
        db, user=actor, brokerage_id=brokerage_id, permission="documents.prepare"
    )
    draft = db.get(ContractDraft, draft_id)
    if draft is None or draft.brokerage_id != brokerage_id:
        raise LookupError("Contract draft not found in brokerage")
    transaction = _require_transaction(
        db, brokerage_id=brokerage_id, transaction_id=draft.transaction_id
    )
    previous_state = draft.status
    if selected_form_id is not None:
        draft.selected_form_id = selected_form_id.strip() or None
        draft.selected_form_name = (selected_form_name or "").strip() or None
        draft.selected_form_effective_date = selected_form_effective_date
    fact_count = _upsert_facts(db, draft=draft, actor=actor, facts=facts)
    draft.version += 1
    _sync_status(db, draft=draft, transaction=transaction)
    audit_service.record(
        db,
        actor=actor,
        action="contract_draft.updated",
        resource_type="contract_draft",
        resource_id=draft.id,
        brokerage_id=brokerage_id,
        previous_state=previous_state,
        next_state=draft.status,
        metadata={"fact_count": fact_count, "selected_form_id": draft.selected_form_id},
    )
    db.commit()
    db.refresh(draft)
    return draft


def get(
    db: Session, *, actor: User, brokerage_id: str, draft_id: str
) -> ContractDraft:
    authorization_service.require_permission(
        db, user=actor, brokerage_id=brokerage_id, permission="documents.prepare"
    )
    draft = db.get(ContractDraft, draft_id)
    if draft is None or draft.brokerage_id != brokerage_id:
        raise LookupError("Contract draft not found in brokerage")
    return draft


def facts(db: Session, *, draft_id: str) -> list[ContractDraftFact]:
    return _facts_for_draft(db, draft_id)
