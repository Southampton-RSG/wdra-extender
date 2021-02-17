"""empty message

Revision ID: 370a1a9bfdaf
Revises: 986e6e375d70
Create Date: 2021-02-12 12:15:45.104706

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '370a1a9bfdaf'
down_revision = '986e6e375d70'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('twitter_keys_set', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'twitter_keys_set')
    # ### end Alembic commands ###