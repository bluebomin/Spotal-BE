from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from community.models import Bookmark
from recommendations.models import SavedPlace
from .serializers import UserSerializer, BookmarkSerializer, SavedPlaceSerializer

User = get_user_model()


class MyPageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        bookmarks = Bookmark.objects.filter(user=user)
        saved_places = SavedPlace.objects.filter(user=user)

        data = {
            "user": UserSerializer(user).data,
            "bookmarks": BookmarkSerializer(bookmarks, many=True).data,
            "saved_places": SavedPlaceSerializer(saved_places, many=True).data, 
        }
        return Response(data)
