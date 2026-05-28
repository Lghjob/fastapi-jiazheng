from fastapi import APIRouter, Path, Query, Body, Depends
from sqlalchemy.orm import Session
from utils.result import Result
from config.database import  get_db
from schemas.banner import Banner
from service.banner_service import BannerService
from typing import Optional

router = APIRouter(prefix="/banner", tags=["轮播图管理接口"])

@router.post("", summary="创建轮播图")
def create_banner(banner: Banner = Body(...), db: Session = Depends(get_db)):
    service = BannerService(db)
    service.create_banner(banner)
    return Result.success_msg("创建成功", None)



@router.get("/active", summary="获取启用的轮播图列表")
def get_active_banners(db: Session = Depends(get_db)):
    service = BannerService(db)
    data = service.get_active_banners()
    return Result.success_data(data)

@router.get("/page", summary="获取轮播图分页列表")
def get_banner_list(
    page_num: int = Query(1),
    page_size: int = Query(10),
    title: str = Query(None),
    status: str = "",
    db: Session = Depends(get_db)
):
    # 手动把空字符串变成 None
    status_value = int(status) if status else None
    service = BannerService(db)
    data = service.get_banners_by_page(title, status_value, page_num, page_size)
    return Result.success_data(data)

@router.get("/{id}", summary="获取轮播图详情")
def get_banner_by_id(id: int = Path(...), db: Session = Depends(get_db)):
    service = BannerService(db)
    data = service.get_banner_by_id(id)
    return Result.success_data(data)

@router.put("/{id}", summary="更新轮播图")
def update_banner(
    id: int = Path(...),
    banner: Banner = Body(...),
    db: Session = Depends(get_db)
):
    banner.id = id
    service = BannerService(db)
    service.update_banner(banner)
    return Result.success_msg("更新成功", None)

@router.delete("/{id}", summary="删除轮播图")
def delete_banner(id: int = Path(...), db: Session = Depends(get_db)):
    service = BannerService(db)
    service.delete_banner(id)
    return Result.success_msg("删除成功", None)