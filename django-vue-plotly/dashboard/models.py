from django.db import models

class Ticker(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    exchange = models.CharField(max_length=50, blank=True, null=True)
    sector = models.CharField(max_length=50, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    
    # TODO: Add more if needed ticker.info has ALOT of data!

    def __str__(self):
        return f"{self.symbol} - {self.name}" if self.name else self.symbol

class TickerMetadata(models.Model):
    # One-to-one relationship to Ticker
    """Calss for populating ticker metadata"""
    ticker = models.OneToOneField(Ticker, on_delete=models.CASCADE, related_name='metadata')
    
    # Example fields from yfinance .info
    long_business_summary = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    market_cap = models.BigIntegerField(blank=True, null=True)
    beta = models.FloatField(blank=True, null=True)
    dividend_yield = models.FloatField(blank=True, null=True)
    full_time_employees = models.IntegerField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Track when metadata was last updated
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Metadata for {self.ticker.symbol}"

class HistoricalPrice(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name='historical_prices') # Convenient way to access all prices for a given ticker
    date = models.DateField(db_index=True)
    open_price = models.DecimalField(max_digits=12, decimal_places=4)
    high_price = models.DecimalField(max_digits=12, decimal_places=4)
    low_price = models.DecimalField(max_digits=12, decimal_places=4)
    close_price = models.DecimalField(max_digits=12, decimal_places=4)
    volume = models.BigIntegerField()

    class Meta:
        unique_together = ('ticker', 'date')
        ordering = ['date']
        indexes = [
            models.Index(fields=['ticker', 'date'])
        ]

    def __str__(self):
        return f"{self.ticker.symbol} on {self.date}: Close={self.close_price}"