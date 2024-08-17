from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from .models import Video
from .serializers import VideoSerializer
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator



CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)
@method_decorator(cache_page(CACHE_TTL), name='dispatch')
class VideoListView(generics.ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer