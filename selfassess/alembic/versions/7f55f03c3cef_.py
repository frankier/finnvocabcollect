"""empty message

Revision ID: 7f55f03c3cef
Revises: cc4a47150e62
Create Date: 2021-10-31 18:29:24.337694

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f55f03c3cef'
down_revision = 'cc4a47150e62'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('participant', schema=None) as batch_op:
        batch_op.add_column(sa.Column('miniexam_fixup_date', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('participant', schema=None) as batch_op:
        batch_op.drop_column('miniexam_fixup_date')

    # ### end Alembic commands ###
