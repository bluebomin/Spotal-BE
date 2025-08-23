from django.db import models
from community.models import Emotion

# Create your models here.

class SearchShop(models.Model):
    shop_id = models.AutoField(primary_key=True)
    emotion_id = models.ManyToManyField(Emotion)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    uptaenm = models.CharField(max_length=50)
   
  
 