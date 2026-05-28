import logging
from fastapi import APIRouter, Path, Query, Depends
from sqlalchemy.orm import Session

# 导入自定义模块
from utils.result import Result
from schemas.service_favorite import ServiceFavorite
from service.service_favorite_service import ServiceFavoriteService
from config.database import get_db

# 路由配置
router = APIRouter(prefix="/favorite", tags=["收藏管理接口"])

# 日志配置
logger = logging.getLogger("ServiceFavoriteController")

# ===================== 接口迁移 =====================

@router.post("", summary="添加收藏")
def add_favorite(favorite: ServiceFavorite, db: Session = Depends(get_db)):
    logger.info(f"添加收藏: userId={favorite.user_id}")
    service = ServiceFavoriteService(db)
    service.add_favorite(favorite)
    return Result.success_msg("收藏成功", None)

@router.delete("", summary="取消收藏")
def cancel_favorite(
    userId: int = Query(..., description="用户ID"),
    serviceId: int = Query(..., description="服务ID"),
    db: Session = Depends(get_db)
):

    logger.info(f"取消收藏: userId={userId}, serviceId={serviceId}")
    service = ServiceFavoriteService(db)
    service.cancel_favorite(userId, serviceId)
    return Result.success_msg("取消成功", None)

@router.get("/list", summary="获取收藏列表")
def get_favorite_list(
    pageNum: int = Query(1, description="页码"),
    pageSize: int = Query(10, description="每页数量"),
    userId: str = Query("", description="用户ID"),
    serviceId: str = Query("", description="服务ID"),
    db: Session = Depends(get_db)
):
    """
    支持可选参数：userId, serviceId
    """
    logger.info(f"获取收藏列表: pageNum={pageNum}, pageSize={pageSize}")
    service = ServiceFavoriteService(db)
    data = service.get_favorites_by_page(userId, serviceId, pageNum, pageSize)
    return Result.success_data(data)

@router.get("/check", summary="检查是否已收藏")
def check_favorite(
    userId: int = Query(..., description="用户ID"),
    serviceId: int = Query(..., description="服务ID"),
    db: Session = Depends(get_db)
):
    logger.info(f"检查是否已收藏: userId={userId}, serviceId={serviceId}")
    service = ServiceFavoriteService(db)
    data = service.is_favorite(userId, serviceId)
    return Result.success_data(data)

@router.get("/{id}", summary="获取收藏详情")
def get_favorite(
    id: int = Path(..., description="收藏ID"),
    db: Session = Depends(get_db)
):
    logger.info(f"获取收藏详情: {id}")
    service = ServiceFavoriteService(db)
    data = service.get_favorite_by_id(id)
    return Result.success_data(data)