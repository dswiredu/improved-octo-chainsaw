import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import JSONField


class ScenarioDataSet(models.Model):
    """
    Represents one uploaded scenario dataset from a user.
    Stores metadata, processing status, and cached column names (variables).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="scenario_datasets"
    )
    name = models.CharField(max_length=50)
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        default="pending",
    )

    logs = models.TextField(blank=True)

    column_names = JSONField(
        blank=True,
        default=list,
        help_text="Cached list of variable names (columns) extracted from the file",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"], name="unique_scenario_per_user"
            )
        ]

    def log(self, message: str):
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs = (self.logs or "") + f"[{timestamp}] {message}\n"
        self.save(update_fields=["logs"])

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class ScenarioValue(models.Model):
    """
    Stores one numeric value for one variable at a specific timestep,
    linked to a scenario dataset.
    """

    dataset = models.ForeignKey(
        ScenarioDataSet, on_delete=models.CASCADE, related_name="values"
    )

    timestep = models.IntegerField()
    variable = models.CharField(max_length=100)
    value = models.FloatField()

    class Meta:
        indexes = [
            models.Index(fields=["dataset", "variable", "timestep"]),
        ]
        ordering = ["timestep"]

    def __str__(self):
        return f"{self.dataset.name} | {self.variable} @ {self.timestep} = {self.value}"
