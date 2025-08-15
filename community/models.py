from django.db import models


# Create your models here.
class emotion(models.Model):
    emotion_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class location(models.Model):
    location_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
# 커뮤니티 글
class memory(models.Model):
    memory_id = models.AutoField(primary_key=True)
    emotion_id = models.ManyToManyField(emotion) # 감정 여러개 선택 가능
    location = models.ForeignKey(location, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="memories",
    ) # 위치는 하나만 선택 가능
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='memories')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    

# 커뮤니티 이미지
class image(models.Model):
    image_id = models.AutoField(primary_key=True)
    memory= models.ForeignKey(memory, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=200,blank=True, default="")
    image_name = models.CharField(max_length=100,blank=True, default="")

 


   