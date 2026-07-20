from app.domains.identity.models import User  # noqa: F401
from app.domains.market.models import Offer, Price, Store  # noqa: F401
from app.domains.products.models import Brand, Category, Product, ProductVariant, Specification  # noqa: F401
from app.domains.recommendations.models import Recommendation, RecommendationSession  # noqa: F401
from app.domains.deal_notifications.db_models import NotificationPreferenceModel  # noqa: F401
from app.domains.watchlist.db_models import WatchlistItemModel  # noqa: F401
from app.domains.billing.db_models import SubscriptionModel  # noqa: F401
