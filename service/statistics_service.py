import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy import  asc
# 导入你项目已有的文件
from schemas.user import User
from schemas.service_item import ServiceItem
from schemas.service_category import ServiceCategory
from schemas.service_staff import ServiceStaff
from schemas.service_order import ServiceOrder
from utils.exceptions.service_exception import ServiceException
from utils.enums.order_status import OrderStatus

# 导入 SQLAlchemy Model
from models.user_model import UserModel
from models.service_item_model import ServiceItemModel
from models.service_category_model import ServiceCategoryModel
from models.service_staff_model import ServiceStaffModel
from models.service_order_model import ServiceOrderModel

# 日志配置
logger = logging.getLogger(__name__)

class StatisticsService:
    def __init__(self, db: Session):
        self.db = db

    # ===================== 系统概览 =====================
    def get_system_overview(self, staff_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取系统概览数据
        """
        logger.info(f"获取统计数据，staffId:{staff_id}")
        overview: Dict[str, Any] = {}

        # 1. 统计用户总数
        total_users = self.db.query(UserModel).count()
        overview["totalUsers"] = total_users

        # 2. 统计服务项目总数
        total_services = self.db.query(ServiceItemModel)\
            .filter(
                ServiceItemModel.status == 1,
                ServiceItemModel.is_deleted == 0
            )\
            .count()
        overview["totalServices"] = total_services

        # 3. 统计服务类型总数
        total_categories = self.db.query(ServiceCategoryModel)\
            .filter(ServiceCategoryModel.is_deleted == 0)\
            .count()
        overview["totalCategories"] = total_categories

        # 4. 统计服务人员总数
        total_staff = self.db.query(ServiceStaffModel)\
            .filter(ServiceStaffModel.is_deleted == 0)\
            .count()
        overview["totalStaff"] = total_staff

        # 5. 统计订单相关数据
        order_query = self.db.query(ServiceOrderModel)\
            .filter(ServiceOrderModel.is_deleted == 0)
        if staff_id and staff_id.strip():
            order_query = order_query.filter(ServiceOrderModel.staff_id == int(staff_id))

        # 订单总数
        total_orders = order_query.count()
        overview["totalOrders"] = total_orders

        # 计算订单完成率
        completed_query = order_query.filter(
            ServiceOrderModel.order_status == OrderStatus.COMPLETED.get_value()
        )
        completed_orders = completed_query.count()
        if total_orders > 0:
            completion_rate = Decimal(completed_orders) * Decimal(100) / Decimal(total_orders)
            completion_rate = float(completion_rate.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP))
        else:
            completion_rate = 0.0
        overview["completionRate"] = completion_rate

        # 6. 统计总交易金额和平均订单金额
        completed_order_query = self.db.query(ServiceOrderModel)\
            .filter(
                ServiceOrderModel.order_status == OrderStatus.COMPLETED.get_value(),
                ServiceOrderModel.is_deleted == 0
            )
        if staff_id and staff_id.strip():
            completed_order_query = completed_order_query.filter(
                ServiceOrderModel.staff_id == int(staff_id)
            )

        completed_order_list = completed_order_query.all()

        # 总交易金额
        total_amount = Decimal(0)
        for order in completed_order_list:
            if order.total_amount:
                total_amount += Decimal(str(order.total_amount))
        overview["totalAmount"] = float(total_amount)

        # 平均订单金额
        if completed_orders > 0:
            avg_order_amount = total_amount / Decimal(completed_orders)
            avg_order_amount = float(avg_order_amount.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP))
        else:
            avg_order_amount = 0.0
        overview["avgOrderAmount"] = avg_order_amount

        return overview

    # ===================== 订单金额趋势 =====================
    def get_order_trend(
        self,
        time_range: str,
        group_by: Optional[str] = None,
        staff_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取订单金额趋势
        """
        # 1. 验证并设置时间范围
        end_time = datetime.now()
        start_time: datetime

        time_range_lower = time_range.lower()
        if time_range_lower == "month":
            start_time = end_time - timedelta(days=30)
            group_by = group_by if group_by else "day"
        elif time_range_lower == "year":
            start_time = end_time - timedelta(days=365)
            group_by = group_by if group_by else "month"
        elif time_range_lower == "three_years":
            start_time = end_time - timedelta(days=365 * 3)
            group_by = group_by if group_by else "month"
        else:
            raise ServiceException("无效的时间范围")

        # 2. 查询指定时间范围内的已完成订单
        order_query = self.db.query(ServiceOrderModel)\
            .filter(
                ServiceOrderModel.order_status == OrderStatus.COMPLETED.get_value(),
                ServiceOrderModel.is_deleted == 0,
                ServiceOrderModel.complete_time >= start_time,
                ServiceOrderModel.complete_time <= end_time
            )\
            .order_by(asc(ServiceOrderModel.complete_time))

        if staff_id and staff_id.strip():
            order_query = order_query.filter(ServiceOrderModel.staff_id == int(staff_id))

        orders = order_query.all()

        # 3. 根据分组方式处理数据
        grouped_orders: Dict[str, List[ServiceOrder]] = {}

        group_by_lower = group_by.lower() if group_by else "day"
        if group_by_lower == "day":
            for order in orders:
                if order.complete_time:
                    key = order.complete_time.strftime("%Y-%m-%d")
                    if key not in grouped_orders:
                        grouped_orders[key] = []
                    grouped_orders[key].append(ServiceOrder.model_validate(order, from_attributes=True))
        elif group_by_lower == "week":
            for order in orders:
                if order.complete_time:
                    # 计算周开始（周一）
                    order_time = order.complete_time
                    week_start = order_time - timedelta(days=order_time.weekday())
                    key = week_start.strftime("%Y-%m-%d") + "周"
                    if key not in grouped_orders:
                        grouped_orders[key] = []
                    grouped_orders[key].append(ServiceOrder.model_validate(order, from_attributes=True))
        elif group_by_lower == "month":
            for order in orders:
                if order.complete_time:
                    # 修改月份显示格式
                    key = order.complete_time.strftime("%Y年%m月")
                    if key not in grouped_orders:
                        grouped_orders[key] = []
                    grouped_orders[key].append(ServiceOrder.model_validate(order, from_attributes=True))
        else:
            raise ServiceException("无效的分组方式")

        # 4. 准备返回数据
        x_axis = list(grouped_orders.keys())
        # 根据日期字符串排序
        x_axis.sort(key=lambda x: x.replace("年", "").replace("月", "").replace("周", ""))

        # 计算每个分组的金额
        series_data = []
        for date in x_axis:
            group_amount = Decimal(0)
            for order in grouped_orders[date]:
                if order.total_amount:
                    group_amount += Decimal(str(order.total_amount))
            series_data.append(float(group_amount))

        # 计算总计数据
        total_amount = Decimal(0)
        for order in orders:
            if order.total_amount:
                total_amount += Decimal(str(order.total_amount))

        if orders:
            avg_amount = total_amount / Decimal(len(orders))
            avg_amount = float(avg_amount.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP))
        else:
            avg_amount = 0.0

        result: Dict[str, Any] = {
            "xAxis": x_axis,
            "series": [
                {
                    "name": "订单金额",
                    "data": series_data
                }
            ],
            "total": {
                "amount": float(total_amount),
                "count": len(orders),
                "avgAmount": avg_amount
            }
        }

        return result