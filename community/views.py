
from rest_framework import viewsets
from .models import memory
from .serializer import MemorySerializer, EmotionSerializer, LocationSerializer 
from .models import emotion, location
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
# Create your views here.

#Viewset

class EmotionViewSet(viewsets.ModelViewSet):
    queryset = emotion.objects.all().order_by('pk')
    serializer_class = EmotionSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = location.objects.all().order_by('pk')
    serializer_class = LocationSerializer

class MemoryViewSet(viewsets.ModelViewSet):
    queryset = memory.objects.all().order_by('-created_at')
    serializer_class = MemorySerializer

    @action(detail=False, methods=['get'], url_path='tag-options')
    def tag_options(self, request):
        emotions = emotion.objects.all().order_by('emotion_id')
        locations = location.objects.all().order_by('location_id')
        return Response({
            'emotions': EmotionSerializer.data,
            'locations': LocationSerializer.data
        })


