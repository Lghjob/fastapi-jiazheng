import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from schemas.banner import Banner

# 自定义异常（你已有的，不用动）
from utils.exceptions.service_exception import ServiceException

# SQLAlchemy 模型（我等下给你生成）
from models.banner_model import BannerModel

# 日志
logger = logging.getLogger(__name__)

class BannerService:
    def __init__(self, db: Session):
        self.db = db

    def create_banner(self, banner: Banner) -> None:
        # 默认状态
        if banner.status is None:
            banner.status = 1

        # 转为数据库模型
        db_banner = BannerModel(**banner.model_dump())
        
        try:
            self.db.add(db_banner)
            self.db.commit()
            logger.info(f"创建轮播图成功: {db_banner.id}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建轮播图失败: {e}")
            raise ServiceException("创建轮播图失败")

    def update_banner(self, banner: Banner) -> None:
        # 查询是否存在
        existing_banner = self.db.get(BannerModel, banner.id)
        if not existing_banner:
            raise ServiceException("轮播图不存在")

        # 更新数据
        for key, value in banner.model_dump(exclude_unset=True).items():
            setattr(existing_banner, key, value)

        try:
            self.db.commit()
            logger.info(f"更新轮播图成功: {banner.id}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新轮播图失败: {e}")
            raise ServiceException("更新轮播图失败")

    def delete_banner(self, id: int) -> None:
        banner = self.db.get(BannerModel, id)
        if not banner:
            raise ServiceException("轮播图不存在")

        try:
            self.db.delete(banner)
            self.db.commit()
            logger.info(f"删除轮播图成功: {id}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除轮播图失败: {e}")
            raise ServiceException("删除轮播图失败")

    def get_banner_by_id(self, id: int) -> Banner:
        banner = self.db.get(BannerModel, id)
        if not banner:
            raise ServiceException("轮播图不存在")
        return Banner.model_validate(banner)

    def get_active_banners(self) -> List[Banner]:
        banners = self.db.query(BannerModel)\
            .filter(BannerModel.status == 1)\
            .order_by(asc(BannerModel.create_time))\
            .all()
        return [Banner.model_validate(b) for b in banners]

    def get_banners_by_page(
        self,
        title: Optional[str],
        status: Optional[int],
        page_num: int,
        page_size: int
    ):
        query = self.db.query(BannerModel)

        if title:
            query = query.filter(BannerModel.title.like(f"%{title}%"))
        if status is not None:
            query = query.filter(BannerModel.status == status)

        query = query.order_by(desc(BannerModel.create_time))

        total = query.count()
        offset = (page_num - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        return {
            "records": [Banner.model_validate(r) for r in records],
            "total": total,
            "pageNum": page_num,  # 和前端一样 pageNum
            "pageSize": page_size # 和前端一样 pageSize
        }