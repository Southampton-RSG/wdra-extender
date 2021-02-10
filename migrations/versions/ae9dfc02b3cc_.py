"""empty message

Revision ID: ae9dfc02b3cc
Revises: fd5e6804fad3
Create Date: 2021-02-09 15:58:08.577407

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae9dfc02b3cc'
down_revision = 'fd5e6804fad3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('user_email', sa.String(length=254), nullable=False),
    sa.Column('id', sa.Unicode(length=16), nullable=False),
    sa.Column('id_set', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=True)
    op.create_index(op.f('ix_user_user_email'), 'user', ['user_email'], unique=True)
    op.add_column('extract', sa.Column('user_id', sa.Unicode(length=16), nullable=True))
    op.add_column('extract', sa.Column('validate_on_email', sa.Boolean(), nullable=True))
    op.create_index(op.f('ix_extract_user_id'), 'extract', ['user_id'], unique=False)
    op.drop_index('ix_extract_email', table_name='extract')
    op.drop_index('ix_extract_extract_method', table_name='extract')
    op.drop_column('extract', 'email')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('extract', sa.Column('email', sa.VARCHAR(length=254), nullable=False))
    op.create_index('ix_extract_extract_method', 'extract', ['extract_method'], unique=False)
    op.create_index('ix_extract_email', 'extract', ['email'], unique=False)
    op.drop_index(op.f('ix_extract_user_id'), table_name='extract')
    op.drop_column('extract', 'validate_on_email')
    op.drop_column('extract', 'user_id')
    op.drop_index(op.f('ix_user_user_email'), table_name='user')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###
