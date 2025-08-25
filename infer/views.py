from django.shortcuts import render
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import UserInferenceSession, AISummary
from .serializers import (
    UserInferenceSessionSerializer, 
    UserInferenceSessionCreateSerializer,
    RecommendationResultSerializer
)
from .services import get_inference_recommendations
from community.models import Emotion, Location
from recommendations.models import SavedPlace, Place
from recommendations.services.google_service import get_photo_url

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
        user_id = request.data.get("user_id", None)  # user 필드 optional

        print(f"=== 요청 데이터 확인 ===")
        print(f"request.data: {request.data}")
        print(f"request.data 타입: {type(request.data)}")
        print(f"request.data 키들: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'keys 없음'}")
        
        # 1. 입력 데이터 검증
        print(f"=== 시리얼라이저 검증 시작 ===")
        serializer = UserInferenceSessionCreateSerializer(data=request.data, context={'request': request})
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
        
        # serializer 필드명과 일치
        location_id = session_data['selected_location']
        emotion_ids = session_data['selected_emotions']
        
        print(f"location_id: {location_id} (타입: {type(location_id)})")
        print(f"emotion_ids: {emotion_ids} (타입: {type(emotion_ids)})")
        
        # 3. Google Maps API + GPT 추천 생성 (평점 필터링 없음)
        print(f"=== 추천 시스템 호출 시작 ===")
        recommendations, error_message = get_inference_recommendations(
            location_id, emotion_ids  # location_id는 이미 리스트
        )
        
        if error_message:
            print(f"추천 시스템 오류: {error_message}")
            return Response({
                'error': error_message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"추천 시스템 성공: {recommendations}")

        # 감정보관함 제외: user_id가 있으면 SavedPlace 필터링
        saved_shop_ids = []
        if user_id:
            saved_shop_ids = SavedPlace.objects.filter(
                user_id=user_id, rec=2
            ).values_list("shop_id", flat=True)
        
        # 4. 세션 저장
        print(f"=== 세션 저장 시작 ===")
        session = UserInferenceSession.objects.create(
            user=request.user if request.user.is_authenticated else None
        )
        # ManyToManyField 설정
        session.selected_location.set(location_id)
        session.selected_emotions.set(emotion_ids)
        print(f"세션 저장 완료: {session.session_id}")
        
        # 5. 새로운 모델 구조로 데이터 저장
        print(f"=== 새로운 모델 구조로 데이터 저장 ===")
        saved_places = []
        
        for place_data in recommendations['top_places']:
            place_id = place_data.get("place_id")
            if not place_id:
                print(f"[DEBUG] place_id 없음, skip: {place_data}")
                continue  # place 정의 안 된 상태로 내려가지 않도록 안전 처리

            place, created = Place.objects.get_or_create(
                google_place_id=place_id,
                defaults={
                    "name": place_data.get("name", ""),
                    "address": place_data.get("address", ""),
                    "photo_reference": place_data.get("photo_reference", ""),
                    "location_id": location_id[0],
                    "status": place_data.get("status", "operating"),
                }
            )
            
            # 감정 태그 설정
            if 'emotion_tags' in place_data and place_data['emotion_tags']:
                # 감정 태그가 문자열 리스트로 오는 경우를 처리
                emotion_names = place_data['emotion_tags']
                print(f"[DEBUG] 감정 태그 설정 시작: {emotion_names}")
                
                if isinstance(emotion_names, list):
                    # 감정 이름으로 감정 객체 찾기
                    emotions = Emotion.objects.filter(name__in=emotion_names)
                    print(f"[DEBUG] DB에서 찾은 감정 객체: {emotions}")
                    print(f"[DEBUG] 감정 객체 수: {emotions.count()}")
                    
                    if emotions.exists():
                        place.emotions.set(emotions)
                        print(f"[DEBUG] 감정 태그 설정 완료: {[e.name for e in emotions]}")
                    else:
                        print(f"[DEBUG] 감정 태그를 찾을 수 없음: {emotion_names}")
                        # DB에 없는 감정태그는 새로 생성하거나, 기본 감정태그 사용
                        # recommendations와 동일한 방식으로 처리
                        fallback_emotions = Emotion.objects.filter(name__in=['정겨움', '편안함', '조용함'])
                        if fallback_emotions.exists():
                            place.emotions.set(fallback_emotions)
                            print(f"[DEBUG] fallback 감정 태그 설정: {[e.name for e in fallback_emotions]}")
                        else:
                            print(f"[DEBUG] fallback 감정 태그도 설정 실패")
            

            ai_summary = None 
            if created:
                ai_summary = AISummary.objects.create(
                    place=place,
                    summary=place_data.get('summary', '')
                )
            else:
                ai_summary = place.infer_ai_summary.order_by("-created_date").first()

            ai_summary_text = ai_summary.summary if ai_summary else place_data.get('summary', '')

            # 감정보관함에 이미 있으면 skip
            if user_id and place.shop_id in saved_shop_ids:
                continue
            
            # recommendations와 동일한 구조로 데이터 구성
            saved_places.append({
                'shop_id': place.shop_id,
                'name': place.name,
                'address': place.address,
                'rec': 2,
                'emotions': [emotion.name for emotion in place.emotions.all()],  # Place 모델의 emotions 필드 사용
                'location': place.location.name,  # Place 모델의 location 필드 사용
                'ai_summary': ai_summary.summary,
                'image_url': get_photo_url(place.photo_reference) if place.photo_reference else None,
                'status': place.get_status_display(),  # status 필드 추가 (한글 표시)
                'created_date': place.created_date.isoformat(),
                'modified_date': place.modified_date.isoformat()
            })
        
        print(f"데이터 저장 완료: {len(saved_places)}개 장소")
        
        # 6. 응답 데이터 구성 - 프론트가 기대하는 구조 (places 배열만)
        print(f"=== 응답 데이터 구성 ===")
        
        print(f"응답 데이터 구성 완료")
        
        # 프론트가 기대하는 구조: places 배열만 반환
        return Response(saved_places, status=status.HTTP_201_CREATED)
        
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
