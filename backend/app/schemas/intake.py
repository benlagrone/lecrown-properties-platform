from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class EspoLeadPayload(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    emailAddress: Optional[str] = None
    phoneNumber: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    businessUnit: Optional[str] = None
    productType: Optional[str] = None

    model_config = {"extra": "allow"}

    @model_validator(mode="after")
    def validate_has_contact_signal(self) -> "EspoLeadPayload":
        if any(
            (value or "").strip()
            for value in (self.firstName, self.lastName, self.emailAddress, self.phoneNumber)
        ):
            return self
        raise ValueError("Lead payload requires at least one contact field")


class IntakeLeadCreate(BaseModel):
    source_site: str = Field(min_length=1)
    source_type: str = Field(default="website", min_length=1)
    form_provider: Optional[str] = None
    form_id: Optional[str] = None
    form_name: Optional[str] = None
    external_entry_id: Optional[str] = None
    page_url: Optional[str] = None
    campaign: Optional[str] = None
    business_context: Optional[str] = None
    product_context: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    lead: EspoLeadPayload


class IntakeLeadResponse(BaseModel):
    submission_id: str
    status: str
    delivery_target: str
    delivery_status: str
    delivery_record_id: Optional[str] = None
    source_site: str
    business_context: Optional[str] = None
    product_context: Optional[str] = None
    created_at: datetime


class IntakeLeadRead(BaseModel):
    id: str
    source_site: str
    source_type: str
    form_provider: Optional[str] = None
    form_id: Optional[str] = None
    form_name: Optional[str] = None
    external_entry_id: Optional[str] = None
    page_url: Optional[str] = None
    campaign: Optional[str] = None
    business_context: Optional[str] = None
    product_context: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    lead_source: Optional[str] = None
    message: Optional[str] = None
    status: str
    delivery_target: str
    delivery_status: str
    delivery_record_id: Optional[str] = None
    raw_payload: dict[str, Any]
    normalized_payload: dict[str, Any]
    delivery_payload: Optional[dict[str, Any]] = None
    delivery_response: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IntakeDashboardOverview(BaseModel):
    observed_source_sites: int
    total_submissions: int
    new_contacts_today: int
    new_contacts_7d: int
    delivered_submissions: int
    failed_submissions: int


class IntakeDashboardConnectionRead(BaseModel):
    key: str
    label: str
    status: str
    detail: str
    value: Optional[str] = None


class IntakeDashboardSourceSiteRead(BaseModel):
    source_site: str
    source_type: str
    business_contexts: list[str] = Field(default_factory=list)
    form_providers: list[str] = Field(default_factory=list)
    form_names: list[str] = Field(default_factory=list)
    total_submissions: int
    delivered_submissions: int
    failed_submissions: int
    new_contacts_today: int
    new_contacts_7d: int
    last_submission_at: datetime
    last_contact_name: Optional[str] = None
    last_page_url: Optional[str] = None
    last_delivery_status: str


class IntakeDashboardRecentContactRead(BaseModel):
    id: str
    source_site: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    business_context: Optional[str] = None
    product_context: Optional[str] = None
    page_url: Optional[str] = None
    campaign: Optional[str] = None
    status: str
    delivery_status: str
    delivery_record_id: Optional[str] = None
    delivery_error: Optional[str] = None
    created_at: datetime


class IntakeDashboardCRMContactRead(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    account_name: Optional[str] = None
    created_at: Optional[str] = None


class IntakeDashboardCRMLeadRead(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    account_name: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[str] = None


class IntakeDashboardCRMOpportunityRead(BaseModel):
    id: str
    name: str
    account_name: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    stage: Optional[str] = None
    probability: Optional[float] = None
    close_date: Optional[str] = None
    created_at: Optional[str] = None


class IntakeDashboardRead(BaseModel):
    overview: IntakeDashboardOverview
    connections: list[IntakeDashboardConnectionRead] = Field(default_factory=list)
    source_sites: list[IntakeDashboardSourceSiteRead] = Field(default_factory=list)
    recent_contacts: list[IntakeDashboardRecentContactRead] = Field(default_factory=list)
    crm_contacts: list[IntakeDashboardCRMContactRead] = Field(default_factory=list)
    crm_contacts_error: Optional[str] = None
    crm_leads: list[IntakeDashboardCRMLeadRead] = Field(default_factory=list)
    crm_opportunities: list[IntakeDashboardCRMOpportunityRead] = Field(default_factory=list)
    crm_pipeline_error: Optional[str] = None
