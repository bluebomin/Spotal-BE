from django.shortcuts import render
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from .models import UserInferenceSession, Place, AISummary
from .serializers import (
    UserInferenceSessionSerializer, 
    UserInferenceSessionCreateSerializer,
    RecommendationResultSerializer
)
from .services import get_inference_recommendations
from community.models import Emotion, Location

# Create your views here.

@extend_schema(
    tags=['감정 기반 추천'],
    summary='감정 및 위치 옵션 조회',
    description='추론에 필요한 감정 태그와 위치 옵션을 조회합니다.',
    responses={
        200: {
            'description': '옵션 조회 성공',
            'examples': {
                'application/json': {
                    'message': '추론 옵션을 성공적으로 조회했습니다!',
                    'emotions': [
                        {'emotion_id': 1, 'name': '행복'},
                        {'emotion_id': 2, 'name': '설렘'}
                    ],
                    'locations': [
                        {'location_id': 1, 'name': '홍대'},
                        {'location_id': 2, 'name': '강남'}
                    ]
                }
            }
        }
    }
)
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

@extend_schema(
    tags=['감정 기반 추천'],
    summary='가게 추천 생성',
    description='사용자가 선택한 동네와 감정을 기반으로 Google Maps API와 GPT를 활용하여 가게를 추천합니다.',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'selected_location': {
                    'type': 'integer',
                    'description': '선택된 동네의 ID',
                    'example': 1
                },
                'selected_emotions': {
                    'type': 'array',
                    'items': {'type': 'integer'},
                    'description': '선택된 감정 태그 ID 목록 (최대 3개)',
                    'example': [1, 2]
                }
            },
            'required': ['selected_location', 'selected_emotions']
        }
    },
    responses={
        201: {
            'description': '추천 생성 성공',
            'examples': {
                'application/json': {
                    'message': '홍대의 행복, 설렘 가게 추천이 완료되었습니다!',
                    'data': {
                        'session_id': 1,
                        'location': '홍대',
                        'emotions': ['행복', '설렘'],
                        'total_places_found': 5,
                        'gpt_recommendation': '홍대에서 행복과 설렘을 느낄 수 있는 가게들을 추천합니다...',
                        'places': [
                            {
                                'place_id': 1,
                                'name': '행복카페',
                                'address': '서울 마포구 홍대로 123',
                                'image_url': 'https://...',
                                'summary': '행복한 분위기의 카페입니다...',
                                'emotion_tags': ['행복', '설렘']
                            }
                        ]
                    }
                }
            }
        },
        400: {
            'description': '잘못된 요청',
            'examples': {
                'application/json': {
                    'error': '입력 데이터가 올바르지 않습니다.',
                    'details': {'selected_emotions': ['감정 태그는 최대 3개까지 선택 가능합니다.']}
                }
            }
        }
    }
)
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
            # Place 모델에 저장
            place = Place.objects.create(
                name=place_data.get('name', ''),
                address=place_data.get('address', ''),
                image_url=place_data.get('image_url', ''),
                location_id=location_id[0]  # 첫 번째 동네를 기본으로 설정
            )
            
            # 감정 태그 설정
            if 'emotion_tags' in place_data and place_data['emotion_tags']:
                # 감정 태그가 문자열 리스트로 오는 경우를 처리
                emotion_names = place_data['emotion_tags']
                if isinstance(emotion_names, list):
                    # 감정 이름으로 감정 객체 찾기
                    emotions = Emotion.objects.filter(name__in=emotion_names)
                    place.emotions.set(emotions)
            
            # AISummary 모델에 저장
            ai_summary = AISummary.objects.create(
                place=place,
                summary=place_data.get('summary', '')
            )
            
            # recommendations와 동일한 구조로 데이터 구성
            saved_places.append({
                'shop_id': place.shop_id,
                'name': place.name,
                'address': place.address,
                'emotions': [emotion.name for emotion in place.emotions.all()],
                'location': place.location.name,  # Place 모델의 location 필드 사용
                'ai_summary': ai_summary.summary,
                'image_url': place.image_url,
                'created_date': place.created_date.isoformat(),
                'modified_date': place.modified_date.isoformat()
            })
        
        print(f"데이터 저장 완료: {len(saved_places)}개 장소")
        
        # 6. 응답 데이터 구성 - recommendations와 동일한 구조
        print(f"=== 응답 데이터 구성 ===")
        response_data = {
            'session_id': session.session_id,
            'location': recommendations['location'],
            'emotions': recommendations['emotions'],
            'total_places_found': recommendations['total_places_found'],
            'gpt_recommendation': recommendations['gpt_recommendation'],
            'places': saved_places  # recommendations와 동일한 구조
        }
        
        print(f"응답 데이터 구성 완료")
        
        return Response({
            'message': f"{recommendations['location']}의 {', '.join(recommendations['emotions'])} 가게 추천이 완료되었습니다!",
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

@extend_schema(
    tags=['감정 기반 추천'],
    summary='특정 추천 세션 조회',
    description='특정 추론 세션의 상세 정보를 조회합니다.',
    parameters=[
        OpenApiParameter(
            name='session_id',
            type=int,
            location=OpenApiParameter.PATH,
            description='조회할 세션의 ID',
            required=True
        )
    ],
    responses={
        200: {
            'description': '세션 조회 성공',
            'examples': {
                'application/json': {
                    'message': '추론 세션을 성공적으로 조회했습니다!',
                    'data': {
                        'session_id': 1,
                        'user': None,
                        'selected_location': {'location_id': 1, 'name': '홍대'},
                        'selected_emotions': [{'emotion_id': 1, 'name': '행복'}],
                        'created_at': '2024-01-01T12:00:00Z'
                    }
                }
            }
        },
        404: {
            'description': '세션을 찾을 수 없음',
            'examples': {
                'application/json': {
                    'error': '해당 세션을 찾을 수 없습니다.'
                }
            }
        }
    }
)
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

@extend_schema(
    tags=['감정 기반 추천'],
    summary='사용자 추천 히스토리 조회',
    description='로그인한 사용자의 추론 히스토리를 조회합니다.',
    responses={
        200: {
            'description': '히스토리 조회 성공',
            'examples': {
                'application/json': {
                    'message': '사용자 추론 히스토리를 성공적으로 조회했습니다!',
                    'data': [
                        {
                            'session_id': 1,
                            'selected_location': {'location_id': 1, 'name': '홍대'},
                            'selected_emotions': [{'emotion_id': 1, 'name': '행복'}],
                            'created_at': '2024-01-01T12:00:00Z'
                        }
                    ],
                    'total_count': 1
                }
            }
        },
        401: {
            'description': '인증 필요',
            'examples': {
                'application/json': {
                    'error': '로그인이 필요합니다.'
                }
            }
        }
    }
)
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
