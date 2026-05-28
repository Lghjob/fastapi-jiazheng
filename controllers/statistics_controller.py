from fastapi import APIRouter, Query, Depends
from typing import Optional
from utils.result import Result
#删除从 main 导入，直接从 database 导入（解决循环导入）
from config.database import get_db
from service.statistics_service import StatisticsService

# 路由配置
router = APIRouter(
    prefix="/statistics",
    tags=["数据统计接口"]
)

# ===================== 1. 获取系统概览数据 =====================
@router.get("/overview", summary="获取系统概览数据")
def get_system_overview(
    staffId: Optional[str] = Query(None),
    db = Depends(get_db)
):
    try:
        service = StatisticsService(db)
        data = service.get_system_overview(staffId)
        return Result.success_data(data)
    except Exception as e:
        return Result.error_msg(msg="失败")

# ===================== 2. 获取订单金额趋势 =====================
@router.get("/order-trend", summary="获取订单金额趋势")
def get_order_trend(
    timeRange: str = Query(..., pattern="^(month|year|three_years)$", description="时间范围(month:近一月, year:近一年, three_years:近三年)"),
    groupBy: Optional[str] = Query(None, pattern="^(day|week|month)$", description="分组方式(day:按天, week:按周, month:按月)"),
    staffId: Optional[str] = Query(None),
    db = Depends(get_db)
):
    try:
        service = StatisticsService(db)
        data = service.get_order_trend(timeRange, groupBy, staffId)
        return Result.success_data(data)
    except Exception as e:
        return Result.error_msg(str(e))