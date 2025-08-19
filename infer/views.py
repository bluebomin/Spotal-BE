from django.shortcuts import render
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import UserInferenceSession, InferenceRecommendation
from .serializers import (
    UserInferenceSessionSerializer, 
    UserInferenceSessionCreateSerializer,
    InferenceRecommendationSerializer
)
from .services import get_inference_recommendations
from community.models import Emotion, Location

# Create your views here.

@api_view(['GET'])
@permission_classes([AllowAny])
def get_inference_options(request):
    """추론에 필요한 감정과 위치 옵션 조회"""
    try:
        emotions = Emotion.objects.all().order_by('emotion_id')
        locations = Location.objects.all().order_by('location_id')
        
        emotion_data = [{'emotion_id': e.emotion_id, 'name': e.name} for e in emotions]
        location_data = [{'location_id': l.location_id, 'name': l.name} for l in locations]
        
        return Response({
            'message': '추론 옵션을 성공적으로 조회했습니다!',
            'emotions': emotion_data,
            'locations': location_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'옵션 조회에 실패했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_inference_session(request):
    """사용자 추론 세션 생성 및 Google Maps API + GPT 추천"""
    try:
        print(f"=== 요청 데이터 확인 ===")
        print(f"request.data: {request.data}")
        print(f"request.data 타입: {type(request.data)}")
        print(f"request.data 키들: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'keys 없음'}")
        
        # 1. 입력 데이터 검증
        print(f"=== 시리얼라이저 검증 시작 ===")
        serializer = UserInferenceSessionCreateSerializer(data=request.data)
        print(f"시리얼라이저 생성 완료")
        
        if not serializer.is_valid():
            print(f"시리얼라이저 검증 실패: {serializer.errors}")
            return Response({
                'error': '입력 데이터가 올바르지 않습니다.',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"시리얼라이저 검증 성공")
        print(f"검증된 데이터: {serializer.validated_data}")
        
        # 2. 추론 세션 생성
        session_data = serializer.validated_data
        print(f"=== 세션 데이터 추출 ===")
        print(f"session_data: {session_data}")
        
        location_id = session_data['selected_location']
        emotion_ids = session_data['selected_emotions']
        
        print(f"location_id: {location_id} (타입: {type(location_id)})")
        print(f"emotion_ids: {emotion_ids} (타입: {type(emotion_ids)})")
        
        # 3. 평점 기준 (사용자가 조정 가능)
        min_rating = request.data.get('min_rating', 4.8)
        print(f"min_rating: {min_rating}")
        
        # 4. Google Maps API + GPT 추천 생성
        print(f"=== 추천 시스템 호출 시작 ===")
        recommendations, error_message = get_inference_recommendations(
            location_id, emotion_ids, min_rating
        )
        
        if error_message:
            print(f"추천 시스템 오류: {error_message}")
            return Response({
                'error': error_message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"추천 시스템 성공: {recommendations}")
        
        # 5. 세션 저장
        print(f"=== 세션 저장 시작 ===")
        session = UserInferenceSession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            selected_location_id=location_id
        )
        session.selected_emotions.set(emotion_ids)
        print(f"세션 저장 완료: {session.session_id}")
        
        # 6. GPT 추천 결과 저장
        print(f"=== GPT 추천 결과 저장 ===")
        inference_recommendation = InferenceRecommendation.objects.create(
            session=session,
            gpt_recommendation_text=recommendations['gpt_recommendations']
        )
        print(f"GPT 추천 결과 저장 완료: {inference_recommendation.recommendation_id}")
        
        # 7. 응답 데이터 구성 (필요한 정보만)
        print(f"=== 응답 데이터 구성 ===")
        
        # 가게 정보 단순화 (필요한 정보만)
        simplified_places = []
        for place in recommendations['top_places']:
            simplified_place = {
                'name': place.get('name', ''),
                'address': place.get('address', ''),
                'status': place.get('status', ''),
                'summary': place.get('summary', ''),
                'emotion_tags': place.get('emotion_tags', [])
            }
            simplified_places.append(simplified_place)
        
        response_data = {
            'session_id': session.session_id,
            'location': recommendations['location'],
            'emotions': recommendations['emotions'],
            'min_rating': recommendations['min_rating'],
            'total_found': recommendations['total_high_rated_found'],
            'gpt_explanation': recommendations['gpt_recommendations'],
            'places': simplified_places
        }
        
        print(f"응답 데이터 구성 완료")
        
        return Response({
            'message': f"{recommendations['location']}의 평점 {recommendations['min_rating']} 이상 {', '.join(recommendations['emotions'])} 가게 추천이 완료되었습니다!",
            'data': response_data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"=== 뷰 함수 오류 발생 ===")
        print(f"오류 타입: {type(e)}")
        print(f"오류 메시지: {str(e)}")
        import traceback
        print(f"전체 오류 추적:")
        traceback.print_exc()
        
        return Response({
            'error': f'추론 세션 생성에 실패했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_inference_session(request, session_id):
    """특정 추론 세션 조회"""
    try:
        session = UserInferenceSession.objects.get(pk=session_id)
        serializer = UserInferenceSessionSerializer(session)
        
        return Response({
            'message': '추론 세션을 성공적으로 조회했습니다!',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except UserInferenceSession.DoesNotExist:
        return Response({
            'error': '해당 세션을 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'세션 조회에 실패했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_inference_history(request):
    """사용자의 추론 히스토리 조회"""
    try:
        if not request.user.is_authenticated:
            return Response({
                'error': '로그인이 필요합니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        sessions = UserInferenceSession.objects.filter(user=request.user).order_by('-created_at')
        serializer = UserInferenceSessionSerializer(sessions, many=True)
        
        return Response({
            'message': '사용자 추론 히스토리를 성공적으로 조회했습니다!',
            'data': serializer.data,
            'total_count': sessions.count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'히스토리 조회에 실패했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
