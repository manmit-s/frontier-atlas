from typing import List, Optional
from src.crawler.base import BaseCrawler
from src.llm.schemas import ProductEntity, ProductContent, SourceInfo, PricingModelEnum
from src.entity_resolution.resolver import EntityResolver
from src.llm.schemas import EntityMappingLog
from src.utils.logging import logger

class ProductCrawler(BaseCrawler):
    """Crawler for AI products from Hugging Face Models and AI catalogues."""

    def __init__(self, name: str = "Hugging Face Models", entity_resolver: Optional[EntityResolver] = None):
        super().__init__(name=name)
        self.resolver = entity_resolver or EntityResolver()
        self.mapping_logs: List[EntityMappingLog] = []

    async def crawl(self, limit: int = 1000) -> List[ProductEntity]:
        products: List[ProductEntity] = []
        logger.info(f"[{self.name}] Ingesting products (target: {limit})...")

        # Hugging Face Models API supports limit=1000 in batch
        url = f"https://huggingface.co/api/models?limit={limit}&full=false"

        try:
            items = await self.http_client.fetch_json(url)
            if not isinstance(items, list):
                logger.error(f"[{self.name}] Expected JSON array from Hugging Face, got {type(items)}")
                return products

            for item in items:
                if len(products) >= limit:
                    break

                model_id = item.get("id") or item.get("_id") or ""
                if not model_id:
                    continue

                # Split owner/product name
                if "/" in model_id:
                    raw_org, prod_name = model_id.split("/", 1)
                else:
                    raw_org, prod_name = "Independent", model_id

                source_url = f"https://huggingface.co/{model_id}"

                # Canonicalize startup/creator name via EntityResolver
                canonical_org, map_log = self.resolver.resolve(raw_org, source_url=source_url)
                self.mapping_logs.append(map_log)

                # Open-source models are FREE or FREEMIUM
                pricing = PricingModelEnum.FREE

                product = ProductEntity(
                    schemaVersion="1.0",
                    recordType="PRODUCT",
                    source=SourceInfo(name=self.name, url=source_url),
                    content=ProductContent(
                        startupName=canonical_org,
                        pricingModel=pricing
                    )
                )
                products.append(product)

        except Exception as e:
            logger.error(f"[{self.name}] Error fetching products: {e}")

        logger.info(f"[{self.name}] Ingestion complete: collected {len(products)} products.")
        return products
