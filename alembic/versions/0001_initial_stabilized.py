"""initial stabilized schema

Revision ID: 0001_initial_stabilized
Revises:
Create Date: 2026-07-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_stabilized"
down_revision = None
branch_labels = None
depends_on = None


def uuid_pk():
    return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()"))


def timestamps():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    ]


def jsonb_col(name):
    return sa.Column(name, postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False)


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    op.create_table(
        "users",
        uuid_pk(),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("username", sa.String(80)),
        sa.Column("display_name", sa.String(160)),
        sa.Column("password_hash", sa.Text()),
        sa.Column("status", sa.String(50), server_default="ACTIVE", nullable=False),
        sa.Column("preferred_language", sa.String(10), server_default="en", nullable=False),
        sa.Column("preferred_currency", sa.String(3), server_default="EUR", nullable=False),
        sa.Column("preferred_country", sa.String(2), server_default="DE", nullable=False),
        *timestamps(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table("brands", uuid_pk(), sa.Column("name", sa.String(200), nullable=False), sa.Column("slug", sa.String(220), nullable=False), sa.Column("website", sa.Text()), sa.Column("country", sa.String(2)), sa.Column("trust_score", sa.Numeric(5, 2)), jsonb_col("metadata"), *timestamps())
    op.create_index("ix_brands_slug", "brands", ["slug"], unique=True)

    op.create_table("categories", uuid_pk(), sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id")), sa.Column("name", sa.String(200), nullable=False), sa.Column("slug", sa.String(220), nullable=False), sa.Column("description", sa.Text()), jsonb_col("metadata"), *timestamps())
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)

    op.create_table("products", uuid_pk(), sa.Column("brand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("brands.id")), sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id")), sa.Column("title", sa.Text(), nullable=False), sa.Column("slug", sa.String(300)), sa.Column("model_number", sa.String(200)), sa.Column("gtin", sa.String(32)), sa.Column("manufacturer_sku", sa.String(200)), sa.Column("canonical_key", sa.String(300)), sa.Column("description", sa.Text()), jsonb_col("metadata"), *timestamps())
    op.create_index("ix_products_canonical_key", "products", ["canonical_key"])

    op.create_table("product_variants", uuid_pk(), sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False), sa.Column("variant_name", sa.String(240), nullable=False), sa.Column("attributes", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False), sa.Column("gtin", sa.String(32)), sa.Column("manufacturer_sku", sa.String(200)), jsonb_col("metadata"), *timestamps())

    op.create_table("specifications", uuid_pk(), sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False), sa.Column("variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_variants.id")), sa.Column("spec_data", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False), sa.Column("source", sa.String(200)), sa.Column("confidence", sa.Numeric(5, 2)), *timestamps())

    op.create_table("stores", uuid_pk(), sa.Column("name", sa.String(200), nullable=False), sa.Column("slug", sa.String(220), nullable=False), sa.Column("website", sa.Text()), sa.Column("country", sa.String(2), server_default="DE", nullable=False), sa.Column("affiliate_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False), sa.Column("affiliate_network", sa.String(120)), sa.Column("trust_score", sa.Numeric(5, 2)), jsonb_col("metadata"), *timestamps())
    op.create_index("ix_stores_slug", "stores", ["slug"], unique=True)

    op.create_table("offers", uuid_pk(), sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False), sa.Column("variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_variants.id")), sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id"), nullable=False), sa.Column("url", sa.Text(), nullable=False), sa.Column("store_sku", sa.String(200)), sa.Column("title_on_store", sa.Text()), sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False), jsonb_col("metadata"), *timestamps())
    op.create_index("ix_offers_product_id", "offers", ["product_id"])
    op.create_index("ix_offers_store_id", "offers", ["store_id"])

    op.create_table("prices", uuid_pk(), sa.Column("offer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("offers.id"), nullable=False), sa.Column("amount", sa.Numeric(12, 2), nullable=False), sa.Column("currency", sa.String(3), server_default="EUR", nullable=False), sa.Column("original_amount", sa.Numeric(12, 2)), sa.Column("shipping_amount", sa.Numeric(12, 2)), sa.Column("stock_status", sa.String(80)), jsonb_col("metadata"), *timestamps())
    op.create_index("ix_prices_offer_created", "prices", ["offer_id", "created_at"])

    op.create_table("recommendation_sessions", uuid_pk(), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")), sa.Column("query_text", sa.Text()), sa.Column("input_url", sa.Text()), sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id")), sa.Column("status", sa.String(80), server_default="CREATED", nullable=False), sa.Column("locale", sa.String(10), server_default="en"), sa.Column("currency", sa.String(3), server_default="EUR"), sa.Column("country", sa.String(2), server_default="DE"), jsonb_col("metadata"), *timestamps())

    op.create_table("recommendations", uuid_pk(), sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recommendation_sessions.id"), nullable=False), sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id")), sa.Column("decision", sa.String(50), nullable=False), sa.Column("confidence", sa.Numeric(5, 2), nullable=False), sa.Column("summary", sa.Text(), nullable=False), sa.Column("recommendation_payload", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False), *timestamps())


def downgrade():
    for table in ["recommendations", "recommendation_sessions", "prices", "offers", "stores", "specifications", "product_variants", "products", "categories", "brands", "users"]:
        op.drop_table(table)
