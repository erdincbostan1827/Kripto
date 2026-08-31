from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision='0002_identity_recovery'
down_revision='0001_core_schema'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table(
        'password_reset_tokens',
        sa.Column('id',sa.String(32),primary_key=True),
        sa.Column('user_id',sa.String(32),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('token_hash',sa.String(64),nullable=False,unique=True),
        sa.Column('expires_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('used_at',sa.DateTime(timezone=True),nullable=True),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
    )
    op.create_index('ix_password_reset_tokens_user_id','password_reset_tokens',['user_id'])

def downgrade():
    raise RuntimeError('Destructive downgrade blocked for identity recovery evidence; restore or forward migration required')
