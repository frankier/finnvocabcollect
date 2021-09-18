"""add deadline columns to participant

Revision ID: 8bdb3878ea0a
Revises: df60f067baca
Create Date: 2021-09-18 13:30:54.425388

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8bdb3878ea0a'
down_revision = 'df60f067baca'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('participant', schema=None) as batch_op:
        batch_op.add_column(sa.Column('accept_deadline', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('complete_deadline', sa.Date(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('participant', schema=None) as batch_op:
        batch_op.drop_column('complete_deadline')
        batch_op.drop_column('accept_deadline')

    # ### end Alembic commands ###
