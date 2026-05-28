from fastapi import APIRouter, Path, Query, Depends
from utils.result import Result
# 统一项目导入规范
from config.database import  get_db
from service.service_browse_history_service import ServiceBrowseHistoryService

# 路由配置
router = APIRouter(prefix="/browse-history", tags=["浏览记录管理接口"])

# ===================== 1. 记录浏览历史 =====================
@router.post("", summary="记录浏览历史")
def record_history(
    userId: int = Query(...),
    serviceId: int = Query(...),
    db = Depends(get_db)
):
    service = ServiceBrowseHistoryService(db)
    service.record_browse_history(userId, serviceId)
    return Result.success_msg("记录成功", None)

# ===================== 2. 清除浏览历史 =====================
@router.delete("", summary="清除浏览历史")
def clear_history(
    userId: int = Query(...),
    db = Depends(get_db)
):
    service = ServiceBrowseHistoryService(db)
    service.clear_browse_history(userId)
    return Result.success_msg("清除成功", None)



# ===================== 4. 获取浏览历史列表 =====================
@router.get("/list", summary="获取浏览历史列表")
def get_history_list(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    userId: int = Query(None),
    serviceId: int = Query(None),
    db = Depends(get_db)
):
    service = ServiceBrowseHistoryService(db)
    data = service.get_history_by_page(userId, serviceId, pageNum, pageSize)
    return Result.success_data(data)

# ===================== 3. 获取浏览历史详情 =====================
@router.get("/{id}", summary="获取浏览历史详情")
def get_history(
    id: int = Path(...),
    db = Depends(get_db)
):
    service = ServiceBrowseHistoryService(db)
    data = service.get_history_by_id(id)
    return Result.success_data(data)