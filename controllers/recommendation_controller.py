from fastapi import APIRouter, Path, Query, Depends

from utils.result import Result

# 数据库依赖
from config.database import get_db

# 推荐算法服务
from service.recommendation.user_based_recommendation_service import (
    UserBasedRecommendationService
)

from service.recommendation.content_based_recommendation_service import (
    ContentBasedRecommendationService
)

from service.recommendation.user_profile_recommendation_service import (
    UserProfileRecommendationService
)


# =========================================================
# 路由
# =========================================================
router = APIRouter(
    prefix="/recommend",
    tags=["推荐系统接口"]
)

# =========================================================
# 1. 基于用户的协同过滤推荐（UserCF）
# =========================================================
@router.get(
    "/user-based/{user_id}",
    summary="基于用户协同过滤的推荐"
)
def get_user_based_recommendations(
    user_id: int = Path(..., description="用户ID"),
    limit: int = Query(5, description="推荐数量"),
    db=Depends(get_db)
):

    try:

        service = UserBasedRecommendationService(db)

        data = service.get_recommendations(
            user_id=user_id,
            limit=limit
        )

        return Result.success_data(data)

    except Exception as e:

        return Result.error_msg(str(e))


# =========================================================
# 2. 基于内容的推荐（TF-IDF）
# =========================================================
@router.get(
    "/content-based/{service_id}",
    summary="基于内容的推荐"
)
def get_content_based_recommendations(
    service_id: int = Path(..., description="服务ID"),
    limit: int = Query(5, description="推荐数量"),
    db=Depends(get_db)
):

    try:

        service = ContentBasedRecommendationService(db)

        data = service.get_recommendations(
            service_id=service_id,
            limit=limit
        )

        return Result.success_data(data)

    except Exception as e:

        return Result.error_msg(str(e))


# =========================================================
# 3. 用户画像推荐
# =========================================================
@router.get(
    "/user-profile/{user_id}",
    summary="用户画像推荐"
)
def get_user_profile_recommendations(
    user_id: int = Path(..., description="用户ID"),
    limit: int = Query(5, description="推荐数量"),
    db=Depends(get_db)
):

    try:

        service = UserProfileRecommendationService(db)

        data = service.get_recommendations(
            user_id=user_id,
            limit=limit
        )

        return Result.success_data(data)

    except Exception as e:

        return Result.error_msg(str(e))
