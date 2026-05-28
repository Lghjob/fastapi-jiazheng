from fastapi import APIRouter, Query, Depends
from typing import Dict, Any
from utils.result import Result
# 核心导入（统一项目规范）
from config.database import  get_db
# 导入所有搜索服务
from service.service_item_service import ServiceItemService
from service.service_staff_service import ServiceStaffService
from service.service_category_service import ServiceCategoryService

# 路由配置
router = APIRouter(prefix="/search", tags=["全局搜索接口"])

# ===================== 1. 搜索服务项目 =====================
@router.get("/services", summary="搜索服务项目")
def search_services(
    keyword: str = Query(...),
    db = Depends(get_db)
):
    service = ServiceItemService(db)
    data = service.search_service_items(keyword)
    return Result.success_data(data)

# ===================== 2. 搜索服务人员 =====================
@router.get("/staff", summary="搜索服务人员")
def search_staff(
    keyword: str = Query(...),
    db = Depends(get_db)
):
    service = ServiceStaffService(db)
    data = service.search_service_staff(keyword)
    return Result.success_data(data)

# ===================== 3. 搜索服务分类 =====================
@router.get("/categories", summary="搜索服务分类")
def search_categories(
    keyword: str = Query(...),
    db = Depends(get_db)
):
    service = ServiceCategoryService(db)
    data = service.search_categories(keyword)
    return Result.success_data(data)

# ===================== 4. 全局搜索服务和人员 =====================
@router.get("/global", summary="全局搜索服务和人员")
def global_search(
    keyword: str = Query(...),
    db = Depends(get_db)
):
    # 初始化所有服务
    item_service = ServiceItemService(db)
    staff_service = ServiceStaffService(db)
    category_service = ServiceCategoryService(db)

    # 执行搜索
    services = item_service.search_service_items(keyword)
    staff = staff_service.search_service_staff(keyword)
    categories = category_service.search_categories(keyword)

    # 组装返回结果
    result: Dict[str, Any] = {
        "services": services,
        "staff": staff,
        "categories": categories
    }

    return Result.success_data(result)