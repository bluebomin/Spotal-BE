from django.db import models

# Create your models here.

class AISummary(models.Model):
    summary_id = models.AutoField(primary_key=True)
    #shop_id = models.ForeignKey('users.Shop', on_delete=models.CASCADE, related_name='ai_summaries')
    summary = models.TextField()

  
 