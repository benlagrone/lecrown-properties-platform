from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class BrokerageCreate(BaseModel):
    legal_name: str = Field(min_length=1, max_length=240)
    license_number: str | None = Field(default=None, max_length=120)
    designated_broker_user_id: str | None = None


class BrokerageRead(BaseModel):
    id: str
    legal_name: str
    license_number: str | None
    status: str
    designated_broker_user_id: str | None
    policy_version: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleGrant(BaseModel):
    user_id: str
    role: str


class RoleAssignmentRead(BaseModel):
    id: str
    brokerage_id: str
    user_id: str
    role: str
    starts_at: datetime | None
    ends_at: datetime | None
    revoked_at: datetime | None

    model_config = {"from_attributes": True}


class AgentProfileCreate(BaseModel):
    user_id: str
    license_number: str | None = Field(default=None, max_length=120)


class AgentProfileRead(BaseModel):
    id: str
    brokerage_id: str
    user_id: str
    license_number: str | None
    sponsorship_status: str
    authority_status: str
    verified_at: datetime | None

    model_config = {"from_attributes": True}


class RepresentationCreate(BaseModel):
    client_name: str = Field(min_length=1, max_length=240)
    client_crm_reference: str | None = Field(default=None, max_length=240)
    representation_type: str
    responsible_agent_user_id: str


class RepresentationRead(BaseModel):
    id: str
    brokerage_id: str
    client_name: str
    client_crm_reference: str | None
    representation_type: str
    responsible_agent_user_id: str
    supervising_user_id: str | None
    status: str
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    representation_id: str
    property_reference: str | None = Field(default=None, max_length=300)
    transaction_type: str
    responsible_agent_user_id: str


class TransactionRead(BaseModel):
    id: str
    brokerage_id: str
    representation_id: str
    property_reference: str | None
    transaction_type: str
    responsible_agent_user_id: str
    supervising_user_id: str | None
    status: str
    confidentiality: str
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}


ContractFactSource = Literal["conversation", "repliers", "espocrm", "document", "user", "system"]
ContractFactConfirmation = Literal["unconfirmed", "confirmed"]


class ContractFactInput(BaseModel):
    key: str = Field(min_length=1, max_length=80, pattern=r"^[a-z][a-z0-9_]*$")
    value: Any
    source_type: ContractFactSource
    source_reference: str | None = Field(default=None, max_length=500)
    confirmation_status: ContractFactConfirmation = "unconfirmed"


class ContractDraftCreate(BaseModel):
    transaction_id: str
    selected_form_id: str | None = Field(default=None, max_length=80)
    selected_form_name: str | None = Field(default=None, max_length=300)
    selected_form_effective_date: date | None = None
    facts: list[ContractFactInput] = Field(default_factory=list, max_length=100)

    @field_validator("facts")
    @classmethod
    def require_unique_fact_keys(cls, facts: list[ContractFactInput]) -> list[ContractFactInput]:
        keys = [fact.key for fact in facts]
        if len(keys) != len(set(keys)):
            raise ValueError("Fact keys must be unique within a request")
        return facts


class ContractDraftUpdate(BaseModel):
    selected_form_id: str | None = Field(default=None, max_length=80)
    selected_form_name: str | None = Field(default=None, max_length=300)
    selected_form_effective_date: date | None = None
    facts: list[ContractFactInput] = Field(default_factory=list, max_length=100)

    @field_validator("facts")
    @classmethod
    def require_unique_fact_keys(cls, facts: list[ContractFactInput]) -> list[ContractFactInput]:
        return ContractDraftCreate.require_unique_fact_keys(facts)


class ContractFactRead(BaseModel):
    key: str
    value: Any
    source_type: ContractFactSource
    source_reference: str | None
    confirmation_status: ContractFactConfirmation
    confirmed_by_user_id: str | None


class ContractDraftRead(BaseModel):
    id: str
    brokerage_id: str
    transaction_id: str
    selected_form_id: str | None
    selected_form_name: str | None
    selected_form_effective_date: date | None
    status: Literal["collecting", "review_required", "review_ready"]
    version: int
    facts: list[ContractFactRead]
    missing_fields: list[str]
    questions: list[str]
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime


class DocumentVersionRead(BaseModel):
    id: str
    document_id: str
    version_number: int
    sha256: str
    media_type: str
    size_bytes: int
    scan_status: str
    render_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadRead(BaseModel):
    document_id: str
    brokerage_id: str
    transaction_id: str | None
    name: str
    classification: str
    retention_policy: str
    version: DocumentVersionRead
