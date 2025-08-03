from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseEntity

User = get_user_model()

class MatchingStatus(models.TextChoices):
    PENDING = '대기중', '대기중'
    ACCEPTED = '수락됨', '수락됨'
    REJECTED = '거절됨', '거절됨'

class Matching(BaseEntity):
    sender = models.ForeignKey(User, related_name='sent_matches', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_matches', on_delete=models.CASCADE)

    status = models.CharField(
        max_length=10,
        choices=MatchingStatus.choices,
        default=MatchingStatus.PENDING
    )

    matched_at = models.DateTimeField(null=True, blank=True)

    request_message = models.TextField(null=True, blank=True)
    refusal_message = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['sender', 'receiver'], name='unique_sender_receiver')
        ]

    def __str__(self):
        return f"{self.sender} → {self.receiver} ({self.status})"
