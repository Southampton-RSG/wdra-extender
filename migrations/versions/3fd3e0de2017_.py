"""empty message

Revision ID: 3fd3e0de2017
Revises: 254eecd02877
Create Date: 2021-04-01 17:57:22.505755

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3fd3e0de2017'
down_revision = '254eecd02877'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('extracts', sa.Column('queuing', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('extracts', 'queuing')
    # ### end Alembic commands ###
