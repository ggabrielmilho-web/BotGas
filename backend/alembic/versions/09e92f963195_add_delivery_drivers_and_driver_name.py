"""add delivery drivers and driver name

Revision ID: 09e92f963195
Revises: 08e81d852184
Create Date: 2025-11-04 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '09e92f963195'
down_revision: Union[str, None] = '08e81d852184'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create delivery_drivers table
    op.create_table('delivery_drivers',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('total_deliveries', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    # Add driver_name column to orders table
    op.add_column('orders', sa.Column('driver_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove driver_name column from orders
    op.drop_column('orders', 'driver_name')

    # Drop delivery_drivers table
    op.drop_table('delivery_drivers')
