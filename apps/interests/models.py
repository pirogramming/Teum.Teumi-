from django.db import models
from apps.core.models import BaseEntity

class Interest(BaseEntity):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, null=True)
