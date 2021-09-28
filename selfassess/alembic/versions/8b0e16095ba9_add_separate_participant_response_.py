"""add separate participant response language table

Revision ID: 8b0e16095ba9
Revises: 942d25b6277b
Create Date: 2021-09-28 17:19:11.066476

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b0e16095ba9'
down_revision = '942d25b6277b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('participant_response_language',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('participant_id', sa.Integer(), nullable=False),
    sa.Column('language', sa.String(), nullable=False),
    sa.Column('level', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['participant_id'], ['participant.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('participant_language', schema=None) as batch_op:
        batch_op.alter_column('level',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('participant_language', schema=None) as batch_op:
        batch_op.alter_column('level',
               existing_type=sa.INTEGER(),
               nullable=False)

    op.drop_table('participant_response_language')
    # ### end Alembic commands ###