from django.db import models

# Create your models here.

class SeaerchShop(models.Model):
    shop_id = models.AutoField(primary_key=True)
    emotion = models.ForeignKey('Emotion', on_delete=models.CASCADE)
    location = models.ForeignKey('Location', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    uptaenm = models.CharField(max_length=50)

  
 