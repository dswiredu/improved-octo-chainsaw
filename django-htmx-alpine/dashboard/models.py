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


class Client(models.Model):
    client_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.client_id})"

class Account(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='accounts')
    account_id = models.CharField(max_length=30)
    account_name = models.CharField(max_length=100)

    def __str__(self):
        return self.account_name

class Instrument(models.Model):
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.symbol

class PositionSnapshot(models.Model):
    date = models.DateField()
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='positions')
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name='positions')
    
    units = models.DecimalField(max_digits=20, decimal_places=2)
    market_price = models.DecimalField(max_digits=12, decimal_places=2)
    market_value = models.DecimalField(max_digits=20, decimal_places=2)
    book_value = models.DecimalField(max_digits=20, decimal_places=2)
    
    deposits = models.DecimalField(max_digits=20, decimal_places=2)
    withdrawals = models.DecimalField(max_digits=20, decimal_places=2)
    net_deposits = models.DecimalField(max_digits=20, decimal_places=2)
    
    total_return = models.DecimalField(max_digits=8, decimal_places=4)
    cumulative_return = models.DecimalField(max_digits=8, decimal_places=4)
    pct_of_portfolio = models.DecimalField(max_digits=6, decimal_places=4)

    # class Meta:
    #     unique_together = ("date", "account", "instrument")

    def __str__(self):
        return f"{self.date} | {self.account.account_name} | {self.instrument.symbol}"