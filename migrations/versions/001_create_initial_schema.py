"""
Alembic migration script template.
"""

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    """Create initial schema."""
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])

    # URLs table
    op.create_table(
        'urls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('short_code', sa.String(12), nullable=False),
        sa.Column('long_url', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('short_code'),
    )
    op.create_index('idx_urls_short_code', 'urls', ['short_code'])
    op.create_index('idx_urls_user_id', 'urls', ['user_id'])
    op.create_index('idx_urls_created_at', 'urls', ['created_at'])
    op.create_index('idx_urls_expires_at', 'urls', ['expires_at'])
    op.create_index('idx_urls_long_url', 'urls', ['long_url'])

    # Click events table (append-only)
    op.create_table(
        'click_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shortened_url_id', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('referrer', sa.String(500), nullable=True),
        sa.Column('country', sa.String(2), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['shortened_url_id'], ['urls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_click_events_shortened_url_id', 'click_events', ['shortened_url_id'])
    op.create_index('idx_click_events_timestamp', 'click_events', ['timestamp'])
    op.create_index('idx_click_events_ip_address', 'click_events', ['ip_address'])
    op.create_index('idx_click_events_url_timestamp', 'click_events', ['shortened_url_id', 'timestamp'])
    op.create_index('idx_click_events_url_ts_country', 'click_events', ['shortened_url_id', 'timestamp', 'country'])


def downgrade() -> None:
    """Drop initial schema."""
    op.drop_index('idx_click_events_url_ts_country', table_name='click_events')
    op.drop_index('idx_click_events_url_timestamp', table_name='click_events')
    op.drop_index('idx_click_events_ip_address', table_name='click_events')
    op.drop_index('idx_click_events_timestamp', table_name='click_events')
    op.drop_index('idx_click_events_shortened_url_id', table_name='click_events')
    op.drop_table('click_events')

    op.drop_index('idx_urls_long_url', table_name='urls')
    op.drop_index('idx_urls_expires_at', table_name='urls')
    op.drop_index('idx_urls_created_at', table_name='urls')
    op.drop_index('idx_urls_user_id', table_name='urls')
    op.drop_index('idx_urls_short_code', table_name='urls')
    op.drop_table('urls')

    op.drop_index('idx_users_username', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
