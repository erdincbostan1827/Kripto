from alembic import op
import sqlalchemy as sa
revision='0003_dead_letter_forensics'
down_revision='0002_identity_recovery'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('dead_letters',sa.Column('consumer_version',sa.String(length=40),nullable=False,server_default='unknown'))
    op.add_column('dead_letters',sa.Column('first_failed_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()))
    op.add_column('dead_letters',sa.Column('last_failed_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()))

def downgrade():
    op.drop_column('dead_letters','last_failed_at'); op.drop_column('dead_letters','first_failed_at'); op.drop_column('dead_letters','consumer_version')
