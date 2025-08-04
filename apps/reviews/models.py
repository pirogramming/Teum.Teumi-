from django.db import models
from django.conf import settings
from apps.core.models import BaseEntity
from apps.matches.models import Matching


class ConversationAttitude(models.Model):
    content = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.content

    @staticmethod
    def default_choices():
        return [
            "적극적으로 참여해주셨어요",
            "경청을 잘해주셨어요",
            "질문을 많이 해주셨어요",
            "편안한 분위기를 만들어주셨어요",
            "시간을 잘 지켜주셨어요",
        ]

class ConversationValue(models.Model):
    content = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.content

    @staticmethod
    def default_choices():
        return [
            "새로운 관점을 얻었어요",
            "실용적인 조언을 받았어요",
            "동기부여가 되었어요",
            "재미있는 경험담을 들었어요",
            "전문적인 지식을 배웠어요",
        ]

class Review(BaseEntity):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="written_reviews")
    target = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_reviews")
    match = models.ForeignKey(Matching, on_delete=models.CASCADE, related_name="reviews")
    attitude = models.ManyToManyField(ConversationAttitude)
    degree = models.ManyToManyField(ConversationValue)
    rating = models.DecimalField(max_digits=2, decimal_places=1)
    meeting = models.BooleanField(null=True, blank=True)  
    comment = models.CharField(max_length=100, null=True, blank=True) #필수는 앙님
    
    def __str__(self):
        return f"Review from {self.user} to {self.target}"
