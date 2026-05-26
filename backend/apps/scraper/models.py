from django.db import models


class SourceSite(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    base_url = models.URLField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductListing(models.Model):
    source_site = models.ForeignKey(
        'scraper.SourceSite',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='listings',
    )
    product = models.ForeignKey(
        'products.Product',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='listings',
    )

    source = models.CharField(max_length=100, db_index=True)
    source_url = models.URLField(db_index=True)

    source_listing_id = models.CharField(max_length=200, blank=True, db_index=True)

    title = models.CharField(max_length=500)

    price_text = models.CharField(max_length=100, blank=True, default="")
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="ETB")

    image_url = models.URLField(blank=True)
    availability = models.BooleanField(default=True)

    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scraped_at"]
        constraints = [
            models.UniqueConstraint(fields=["source", "source_url"], name="uniq_scraped_listing_source_url"),
        ]

    def __str__(self):
        return f"{self.source}: {self.title}".strip()