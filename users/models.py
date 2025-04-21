from django.db import models
from django.contrib.auth.models import AbstractUser

from content.models import Video

class CustomUser(AbstractUser): 
  """
  Model for the user. Use a custom user with abstract User
  """  
  custom = models.CharField(max_length=500, default='')   
  address = models.CharField(max_length=150, default='')   
  phone = models.CharField(max_length=25, default='')

  favorite_videos = models.ManyToManyField(Video, related_name='favorited_by', blank=True)