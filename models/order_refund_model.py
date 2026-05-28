from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, BigInteger,func
from datetime import datetime
from config.database import BaseModel

class OrderRefundModel(BaseModel):
    __tablename__ = "order_refund"

    # 主键ID  Long → BigInteger
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    # 订单ID Long → BigInteger
    order_id = Column(BigInteger, nullable=True, comment="订单ID")
    # 用户ID Long → BigInteger
    user_id = Column(BigInteger, nullable=True, comment="用户ID")
    # 退款金额 BigDecimal → DECIMAL(精准匹配，禁止用Float)
    refund_amount = Column(DECIMAL(10, 2), nullable=True, comment="退款金额")
 
    refund_reason = Column(String(500), nullable=True, comment="退款原因")
   
    refund_status = Column(Integer, nullable=True, comment="退款状态(1:待审核,2:审核通过,3:审核拒绝,4:退款中,5:已退款,6:退款失败)")
 
    refund_type = Column(Integer, nullable=True, comment="退款类型(1:用户取消,2:服务人员取消,3:超时未接单,4:服务纠纷)")
    
    # 审核人ID Long → BigInteger
    audit_user_id = Column(BigInteger, nullable=True, comment="审核人ID")
    # 审核时间 LocalDateTime → DateTime
    audit_time = Column(DateTime, nullable=True, comment="审核时间")
    # 审核备注
    audit_remark = Column(String(500), nullable=True, comment="审核备注")
    # 退款完成时间
    refund_time = Column(DateTime, nullable=True, comment="退款完成时间")
    
    # 创建时间（插入时填充）
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
    # 更新时间（插入/更新时填充）
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 逻辑删除 0未删除 1已删除
    is_deleted = Column(Integer, default=0, comment="是否删除(0:未删除,1:已删除)")