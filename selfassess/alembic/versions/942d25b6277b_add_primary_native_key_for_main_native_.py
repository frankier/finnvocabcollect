"""add primary_native key for main native language

Revision ID: 942d25b6277b
Revises: cde958d20c94
Create Date: 2021-09-28 14:18:07.080613

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '942d25b6277b'
down_revision = 'cde958d20c94'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('participant_language', schema=None) as batch_op:
        batch_op.add_column(sa.Column('primary_native', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('participant_language', schema=None) as batch_op:
        batch_op.drop_column('primary_native')

    # ### end Alembic commands ###