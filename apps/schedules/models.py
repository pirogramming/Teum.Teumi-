from django.db import models
from django.conf import settings

class DayOfWeek(models.TextChoices):
    MONDAY = "Monday", "월"
    TUESDAY = "Tuesday", "화"
    WEDNESDAY = "Wednesday", "수"
    THURSDAY = "Thursday", "목"
    FRIDAY = "Friday", "금"

class FreeTime(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="free_times")
    day_of_week = models.CharField(max_length=10, choices=DayOfWeek.choices)

    # 24시간단위로 저장
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.day_of_week} {self.start_time} ~ {self.end_time}"
