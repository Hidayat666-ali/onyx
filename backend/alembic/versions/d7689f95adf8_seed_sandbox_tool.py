"""seed sandbox tool

Revision ID: d7689f95adf8
Revises: 7c00f53ab75f
Create Date: 2026-11-15 10:06:06.789553

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d7689f95adf8"
down_revision = "7c00f53ab75f"
branch_labels = None
depends_on = None

# One row builds exec_command, write_stdin and apply_patch.
SANDBOX_TOOL = {
    "name": "exec_command",
    "display_name": "Sandbox",
    "description": "Run shell commands and edit files in a private Linux sandbox.",
    "in_code_tool_id": "ExecCommandTool",
    "enabled": True,
}


def upgrade() -> None:
    conn = op.get_bind()

    existing = conn.execute(
        sa.text("SELECT id FROM tool WHERE in_code_tool_id = :in_code_tool_id"),
        {"in_code_tool_id": SANDBOX_TOOL["in_code_tool_id"]},
    ).fetchone()

    if existing:
        conn.execute(
            sa.text("""
                UPDATE tool
                SET name = :name,
                    display_name = :display_name,
                    description = :description
                WHERE in_code_tool_id = :in_code_tool_id
                """),
            SANDBOX_TOOL,
        )
        tool_id = existing[0]
    else:
        tool_id = conn.execute(
            sa.text("""
                INSERT INTO tool (name, display_name, description, in_code_tool_id, enabled)
                VALUES (:name, :display_name, :description, :in_code_tool_id, :enabled)
                RETURNING id
                """),
            SANDBOX_TOOL,
        ).scalar_one()

    # Attach to the default persona (id=0) if not already attached.
    conn.execute(
        sa.text("""
            INSERT INTO persona__tool (persona_id, tool_id)
            VALUES (0, :tool_id)
            ON CONFLICT DO NOTHING
            """),
        {"tool_id": tool_id},
    )


def downgrade() -> None:
    conn = op.get_bind()
    in_code_tool_id = SANDBOX_TOOL["in_code_tool_id"]

    conn.execute(
        sa.text("""
            DELETE FROM persona__tool
            WHERE tool_id IN (
                SELECT id FROM tool WHERE in_code_tool_id = :in_code_tool_id
            )
            """),
        {"in_code_tool_id": in_code_tool_id},
    )
    conn.execute(
        sa.text("DELETE FROM tool WHERE in_code_tool_id = :in_code_tool_id"),
        {"in_code_tool_id": in_code_tool_id},
    )
