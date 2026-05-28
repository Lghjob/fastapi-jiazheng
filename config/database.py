from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("DB_URL", "mysql+pymysql://root:[这里输入你的密码]@localhost:3306/housekeeping_db")
engine = create_engine(SQLALCHEMY_DATABASE_URL)# 2. 创建数据库引擎
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # 3. 创建会话
BaseModel = declarative_base() # 4. ORM基类

# ================= 自动填充时间 Mixin =================
class TimedstampMixin:
    """
    这是一个可复用的 Mixin 类。
    只有继承了它的模型，才会拥有这两个时间字段。
    """
    created_time = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
# ==================================================
class TimestampMixin:
    """
    这是一个可复用的 Mixin 类。
    只有继承了它的模型，才会拥有这两个时间字段。
    """
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
# ==================================================
#数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()