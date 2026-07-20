"""products.canonical_key NOT NULL (found live: "Test Product AUTH003P2"
was created with canonical_key=None via POST /products/, which ProductCreate
allowed since canonical_key was optional -- broke watchlist/matching for
that product with a 422. ProductCreate.canonical_key is now a required
field; this migration closes the same gap at the DB level.)

Revision ID: 0021_products_canonical_key_not_null
Revises: 0020_subscriptions
Create Date: 2026-07-20
"""

from alembic import op


revision = "0021_products_canonical_key_not_null"
down_revision = "0020_subscriptions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Repair the one known bad row with the exact value
    # ProductNormalizationService.normalize() derives for its title
    # ("Test Product AUTH003P2") + the default country ("DE") -- computed
    # once via the real normalizer and hardcoded here, since Alembic
    # migrations in this project never import app code (kept consistent
    # with every prior migration).
    op.execute(
        "UPDATE products SET canonical_key = 'auth003p2::de' "
        "WHERE id = 'ed518260-62ef-47a7-8a9d-ef24ba7533bb' AND canonical_key IS NULL"
    )
    # Defensive: any OTHER null row (none known to exist, but a NOT NULL
    # constraint must not fail on unknown data) gets a unique hash-based
    # fallback -- same shape as build_canonical_key()'s own fallback branch
    # (CONNECT-005) for products with no detectable identity.
    op.execute(
        "UPDATE products SET canonical_key = 'unrecognized::' || substr(md5(id::text), 1, 16) "
        "WHERE canonical_key IS NULL"
    )
    op.alter_column("products", "canonical_key", nullable=False)


def downgrade() -> None:
    op.alter_column("products", "canonical_key", nullable=True)
