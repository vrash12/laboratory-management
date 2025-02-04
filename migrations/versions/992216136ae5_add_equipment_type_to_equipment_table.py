"""Add equipment_type to equipment table

Revision ID: 992216136ae5
Revises: 2375e7d7f675
Create Date: 2024-10-17 03:58:49.819021

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '992216136ae5'
down_revision = '2375e7d7f675'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('equipment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('equipment_type', sa.Enum('PC', 'Laptop', name='equipmenttype'), nullable=False))
        batch_op.alter_column('room_id',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('equipment', schema=None) as batch_op:
        batch_op.alter_column('room_id',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=False)
        batch_op.drop_column('equipment_type')

    # ### end Alembic commands ###
