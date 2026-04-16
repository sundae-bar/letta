"""add skills and skills_agents tables

Revision ID: 5dedb1849656
Revises: ffb17eb241fc
Create Date: 2026-03-30 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5dedb1849656"
down_revision: Union[str, None] = "39577145c45d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create skills table
    op.create_table(
        "skills",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("_created_by_id", sa.String(), nullable=True),
        sa.Column("_last_updated_by_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_skills_organization_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "organization_id", name="uix_skill_name_organization"),
    )
    op.create_index("ix_skills_organization_id", "skills", ["organization_id"])
    op.create_index("ix_skills_created_at_name", "skills", ["created_at", "name"])

    # Create skills_agents association table
    op.create_table(
        "skills_agents",
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("skill_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], name="fk_skills_agents_agent_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], name="fk_skills_agents_skill_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("agent_id", "skill_id"),
        sa.UniqueConstraint("agent_id", "skill_id", name="unique_agent_skill"),
    )
    op.create_index("ix_skills_agents_skill_id", "skills_agents", ["skill_id"])


def downgrade() -> None:
    op.drop_table("skills_agents")
    op.drop_table("skills")
