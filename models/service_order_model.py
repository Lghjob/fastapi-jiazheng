from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, BigInteger,func
from datetime import datetime
from config.database import BaseModel 

class ServiceOrderModel(BaseModel):
    __tablename__ = "service_order"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="订单ID")
    user_id = Column(BigInteger, nullable=True, comment="用户ID")
    staff_id = Column(BigInteger, nullable=True, comment="服务人员ID")
    service_id = Column(BigInteger, nullable=True, comment="服务项目ID")

    order_status = Column(Integer, nullable=True, comment="订单状态(1:待支付,2:待接单,3:已接单,4:服务中,5:已完成,6:已取消,7:已关闭)")
    service_time = Column(DateTime, nullable=True, comment="服务开始时间")
    duration = Column(Integer, nullable=True, comment="服务时长(小时)")

    # 2. 金额全部改成 DECIMAL(10,2)
    total_amount = Column(DECIMAL(10,2), nullable=True, comment="订单金额")
    paid_amount = Column(DECIMAL(10,2), nullable=True, comment="实付金额")
    refund_amount = Column(DECIMAL(10,2), nullable=True, comment="退款金额")

    payment_method = Column(String(50), nullable=True, comment="支付方式")
    payment_time = Column(DateTime, nullable=True, comment="支付时间")
    refund_status = Column(Integer, nullable=True, comment="退款状态(0:无退款,1:退款中,2:已退款,3:退款失败)")
    cancel_reason = Column(String(500), nullable=True, comment="取消原因")
    cancel_time = Column(DateTime, nullable=True, comment="取消时间")
    complete_time = Column(DateTime, nullable=True, comment="完成时间")
    remark = Column(String(500), nullable=True, comment="备注")

    create_time = Column(DateTime, default=func.now(), comment="创建时间")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    is_deleted = Column(Integer, default=0, comment="是否删除(0:未删除,1:已删除)")