from dataclasses import dataclass, field
from random import Random


@dataclass
class SyntheticPricePoint:
    amount: float
    currency: str = "EUR"
    day_index: int = 0


@dataclass
class SyntheticOffer:
    store: str
    title: str
    url: str
    sku: str
    price_history: list[SyntheticPricePoint] = field(default_factory=list)
    trust_score: float = 80.0


@dataclass
class SyntheticProduct:
    brand: str
    family: str
    model: str
    memory: str | None
    storage: str | None
    category: str
    canonical_name: str
    aliases: list[str]
    offers: list[SyntheticOffer] = field(default_factory=list)


@dataclass
class SyntheticMarketDataset:
    products: list[SyntheticProduct]

    @property
    def offer_count(self) -> int:
        return sum(len(product.offers) for product in self.products)

    @property
    def price_point_count(self) -> int:
        return sum(
            len(offer.price_history)
            for product in self.products
            for offer in product.offers
        )


class SyntheticMarketDatasetGenerator:
    def __init__(self, seed: int = 42):
        self.random = Random(seed)

    def generate(
        self,
        *,
        product_count: int = 50,
        offers_per_product: int = 3,
        price_points_per_offer: int = 12,
    ) -> SyntheticMarketDataset:
        products = [
            self._generate_product(index, offers_per_product, price_points_per_offer)
            for index in range(product_count)
        ]
        return SyntheticMarketDataset(products=products)

    def _generate_product(
        self,
        index: int,
        offers_per_product: int,
        price_points_per_offer: int,
    ) -> SyntheticProduct:
        template = self._product_template(index)
        aliases = self._aliases(template)

        product = SyntheticProduct(
            brand=template["brand"],
            family=template["family"],
            model=template["model"],
            memory=template.get("memory"),
            storage=template.get("storage"),
            category=template["category"],
            canonical_name=self._canonical_name(template),
            aliases=aliases,
        )

        for offer_index in range(offers_per_product):
            product.offers.append(
                self._generate_offer(
                    product=product,
                    offer_index=offer_index,
                    price_points_per_offer=price_points_per_offer,
                )
            )

        return product

    def _product_template(self, index: int) -> dict:
        templates = [
            {
                "brand": "Apple",
                "family": "MacBook Air",
                "model": f"M{(index % 5) + 1}",
                "memory": "16GB",
                "storage": "512GB",
                "category": "laptop",
                "base_price": 1199,
            },
            {
                "brand": "Sony",
                "family": "WH-1000XM",
                "model": f"WH-1000XM{(index % 3) + 5}",
                "memory": None,
                "storage": None,
                "category": "headphones",
                "base_price": 349,
            },
            {
                "brand": "Samsung",
                "family": "Galaxy S",
                "model": f"S{24 + (index % 4)}",
                "memory": "12GB",
                "storage": "512GB",
                "category": "smartphone",
                "base_price": 999,
            },
            {
                "brand": "Lenovo",
                "family": "ThinkPad",
                "model": f"X1-{index % 4 + 1}",
                "memory": "32GB",
                "storage": "1TB",
                "category": "laptop",
                "base_price": 1599,
            },
        ]
        return templates[index % len(templates)]

    def _canonical_name(self, template: dict) -> str:
        parts = [
            template["brand"],
            template["family"],
            template["model"],
            template.get("memory"),
            template.get("storage"),
        ]
        return " ".join(part for part in parts if part)

    def _aliases(self, template: dict) -> list[str]:
        brand = template["brand"]
        family = template["family"]
        model = template["model"]
        memory = template.get("memory")
        storage = template.get("storage")

        aliases = [
            self._canonical_name(template),
            " ".join(part for part in [brand, family, model, memory, storage] if part),
        ]

        if brand == "Apple" and "MacBook Air" in family:
            aliases.append(f"Apple MBA {model} {self._compact(memory, storage)}")
            aliases.append(f"MacBook Air {model} ({memory} RAM, {storage} SSD)")
        elif brand == "Sony":
            aliases.append(f"Sony {model} Black")
            aliases.append(f"{model} Noise Cancelling Headphones")
        elif brand == "Samsung":
            aliases.append(f"Samsung Galaxy {model} Ultra {storage}")
            aliases.append(f"Galaxy {model} {storage}")
        elif brand == "Lenovo":
            aliases.append(f"Lenovo ThinkPad {model} {memory} {storage}")
            aliases.append(f"ThinkPad {model} {self._compact(memory, storage)}")

        return list(dict.fromkeys(aliases))

    def _compact(self, memory: str | None, storage: str | None) -> str:
        if memory and storage:
            return f"{memory.replace('GB', '')}/{storage}"
        return storage or memory or ""

    def _generate_offer(
        self,
        *,
        product: SyntheticProduct,
        offer_index: int,
        price_points_per_offer: int,
    ) -> SyntheticOffer:
        stores = ["mock-amazon-de", "mock-mediamarkt-de", "mock-saturn-de", "mock-otto-de"]
        store = stores[offer_index % len(stores)]
        title = product.aliases[offer_index % len(product.aliases)]

        base_price = self._base_price(product)
        price_history = self._generate_price_history(
            base_price=base_price,
            points=price_points_per_offer,
            pattern=offer_index % 4,
        )

        slug = title.lower().replace(" ", "-").replace("/", "-").replace("(", "").replace(")", "").replace(",", "")
        return SyntheticOffer(
            store=store,
            title=title,
            url=f"https://example.com/{store}/{slug}",
            sku=f"{store.upper()}-{abs(hash(title)) % 100000}",
            price_history=price_history,
            trust_score=70 + (offer_index * 5),
        )

    def _base_price(self, product: SyntheticProduct) -> float:
        if product.category == "laptop":
            return 1199.0 if product.brand == "Apple" else 1599.0
        if product.category == "smartphone":
            return 999.0
        if product.category == "headphones":
            return 349.0
        return 499.0

    def _generate_price_history(
        self,
        *,
        base_price: float,
        points: int,
        pattern: int,
    ) -> list[SyntheticPricePoint]:
        history: list[SyntheticPricePoint] = []

        for day in range(points):
            if pattern == 0:
                # steady decline
                amount = base_price - day * (base_price * 0.025)
            elif pattern == 1:
                # rising price
                amount = base_price * 0.82 + day * (base_price * 0.025)
            elif pattern == 2:
                # fake discount: normal -> spike -> normal
                if day < points // 3:
                    amount = base_price
                elif day < (points * 2) // 3:
                    amount = base_price * 1.45
                else:
                    amount = base_price * 1.02
            else:
                # mild fluctuation
                amount = base_price * (0.95 + self.random.random() * 0.10)

            history.append(
                SyntheticPricePoint(
                    amount=round(max(amount, 1.0), 2),
                    day_index=day,
                )
            )

        return history
