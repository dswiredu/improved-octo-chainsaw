from django.db import models

# Create your models here.
class HistoricalPrice(models.Model):
    date = models.DateField(db_index=True)
    open_price = models.DecimalField(max_digits=12, decimal_places=4)
    close_price = models.DecimalField(max_digits=12, decimal_places=4)
    high_price = models.DecimalField(max_digits=12, decimal_places=4)
    low_price = models.DecimalField(max_digits=12, decimal_places=4)
    volume = models.BigIntegerField()

    class Meta:
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(fields=["date"], name="unique_date")
        ]

    def __str__(self):
        return f"Close on {self.date} = {self.close_price}"

