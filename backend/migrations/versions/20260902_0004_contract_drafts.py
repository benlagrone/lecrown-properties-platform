"""Add source-aware contract draft intake records."""

from alembic import op
import sqlalchemy as sa

revision = "20260902_0004"
down_revision = "20260830_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contract_drafts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("brokerage_id", sa.String(), nullable=False),
        sa.Column("transaction_id", sa.String(), nullable=False),
        sa.Column("selected_form_id", sa.String(), nullable=True),
        sa.Column("selected_form_name", sa.String(), nullable=True),
        sa.Column("selected_form_effective_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "brokerage_id",
        "transaction_id",
        "selected_form_id",
        "status",
        "created_by_user_id",
    ):
        op.create_index(f"ix_contract_drafts_{column}", "contract_drafts", [column])

    op.create_table(
        "contract_draft_facts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("contract_draft_id", sa.String(), nullable=False),
        sa.Column("fact_key", sa.String(), nullable=False),
        sa.Column("value_json", sa.JSON(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_reference", sa.String(), nullable=True),
        sa.Column("confirmation_status", sa.String(), nullable=False),
        sa.Column("entered_by_user_id", sa.String(), nullable=False),
        sa.Column("confirmed_by_user_id", sa.String(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "contract_draft_id", "fact_key", name="uq_contract_draft_fact_key"
        ),
    )
    for column in (
        "contract_draft_id",
        "fact_key",
        "source_type",
        "confirmation_status",
        "entered_by_user_id",
        "confirmed_by_user_id",
    ):
        op.create_index(f"ix_contract_draft_facts_{column}", "contract_draft_facts", [column])


def downgrade() -> None:
    op.drop_table("contract_draft_facts")
    op.drop_table("contract_drafts")
