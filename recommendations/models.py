from django.db import models
from django.conf import settings

# 추천 가게
class Place(models.Model):
    shop_id = models.BigAutoField(primary_key=True)
    emotion = models.ForeignKey(
        "community.Emotion",   
        on_delete=models.PROTECT,
        related_name="places"
    )
    location = models.ForeignKey(
        "community.Location",   
        on_delete=models.PROTECT,
        related_name="places"
    )
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "place"

    def __str__(self):
        return self.name


class AISummary(models.Model):
    summary_id = models.BigAutoField(primary_key=True)
    shop = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="summaries"
    )
    summary = models.TextField()

    class Meta:
        db_table = "ai_summary"

    def __str__(self):
        return f"Summary for {self.shop.name}"


class SavedPlace(models.Model):
    saved_id = models.BigAutoField(primary_key=True)
    shop = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="saved_records"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_places"
    )
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "saved_place"
        constraints = [
            models.UniqueConstraint(fields=["shop", "user"], name="uniq_user_shop_save")
        ]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["created_date"])
        ]

    def __str__(self):
        return f"{self.user} saved {self.shop.name}"
