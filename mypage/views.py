from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import User, Bookmark, SavedPlace
from .serializers import UserSerializer, BookmarkSerializer, SavedPlaceSerializer

class MyPageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):   # URL path로 user_id 받음
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        bookmarks = Bookmark.objects.filter(user=user)
        saved_places = SavedPlace.objects.filter(user=user)

        data = {
            "user": UserSerializer(user).data,
            "bookmarks": BookmarkSerializer(bookmarks, many=True).data,
            "saved_places": SavedPlaceSerializer(saved_places, many=True).data
        }
        return Response(data)

## 완성 안 되었음! 장소 이미지 구글 api 연동 후, 북마크 되는지 테스트 해 봐야 함~!!
## 그 이후에 마이페이지 뷰 완성할 수 있음 ......