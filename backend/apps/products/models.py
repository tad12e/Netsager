from django.db import models


class Product(models.Model):
	name = models.CharField(max_length=255, db_index=True)
	brand = models.CharField(max_length=120, blank=True, default="", db_index=True)
	model_name = models.CharField(max_length=120, blank=True, default="", db_index=True)
	category = models.CharField(max_length=120, blank=True, default="", db_index=True)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["name"]
		constraints = [
			models.UniqueConstraint(
				fields=["brand", "model_name", "name"],
				name="uniq_product_brand_model_name",
			)
		]

	def __str__(self):
		pieces = [self.brand, self.model_name, self.name]
		label = " ".join(piece for piece in pieces if piece)
		return label or str(self.pk)
