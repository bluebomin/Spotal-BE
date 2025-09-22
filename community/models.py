from django.db import models
from django.conf import settings

# Create your models here.
class Emotion(models.Model):
    emotion_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Location(models.Model):
    location_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
# 커뮤니티 글
class Memory(models.Model):
    memory_id = models.AutoField(primary_key=True)
    emotion_id = models.ManyToManyField(Emotion) # 감정 여러개 선택 가능
    location = models.ForeignKey(Location, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="memories",
    ) # 위치는 하나만 선택 가능
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='memories')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    

# 커뮤니티 이미지
class Image(models.Model):
    image_id = models.AutoField(primary_key=True)
    memory= models.ForeignKey(Memory, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=200,blank=True, default="")
    image_name = models.CharField(max_length=100,blank=True, default="")

 

# 북마크
class Bookmark(models.Model):
    bookmark_id = models.BigAutoField(primary_key=True)
    memory = models.ForeignKey(
        "community.Memory", 
        on_delete=models.CASCADE, 
        related_name="bookmarks"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookmarks"
    )
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bookmark"
        constraints = [
            models.UniqueConstraint(fields=["memory", "user"], name="uniq_user_memory_bookmark")
        ]

    def __str__(self):
        return f"{self.user} bookmarked {self.memory.id}"
    



class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    memory = models.ForeignKey(Memory, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    def is_reply(self):
        return self.parent is not None

    def __str__(self):
        return f"Comment by {self.user.nickname} on Memory {self.memory.memory_id}"