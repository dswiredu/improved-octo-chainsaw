from django.db import models
from django.contrib.auth.models import User

def get_default_user():
    return User.objects.first().id

class ScriptExecution(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=get_default_user)
    script_name = models.CharField(max_length=255)
    arguments = models.TextField(blank=True, null=True)
    output = models.TextField(blank=True, null=True)
    success = models.BooleanField(default=False)  # New: Was execution successful?
    duration = models.FloatField(null=True, blank=True)  # New: Execution time in seconds
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "✅ Success" if self.success else "❌ Failed"
        return f"{self.script_name} - {self.user.username} - {status} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
