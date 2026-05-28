# 导入 FastAPI 核心框架类
"""
家政服务智能推送管理系统
后端主入口文件
技术栈：FastAPI + MySQL + SQLAlchemy
核心功能：用户管理、订单管理、智能推荐、权限控制
毕业设计：刘光辉
"""
from fastapi import FastAPI, APIRouter 
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import uvicorn
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
# 导入异常处理器
from utils.exceptions.exception_handler import service_exception_handler,global_exception_handler,validation_exception_handler
# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("SystemLog")

# 导入内部模块
from config.jwt_interceptor import JwtInterceptorMiddleware
from utils.exceptions.service_exception import ServiceException

# 数据库
from config.database import SessionLocal, get_db

# 服务
from service.service_staff_service import ServiceStaffService

# 定时任务
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 导入所有控制器
from controllers.recommendation_controller import router as recommend_router
from controllers.banner_controller import router as banner_router
from controllers.file_controller import router as file_router
from controllers.menu_controller import router as menu_router
from controllers.payment_controller import router as payment_router
from controllers.refund_controller import router as refund_router
from controllers.role_controller import router as role_router
from controllers.search_controller import router as search_router
from controllers.service_browse_history_controller import router as browse_history_router
from controllers.service_category_controller import router as category_router
from controllers.service_favorite_controller import router as favorite_router
from controllers.service_item_controller import router as service_item_router
from controllers.service_order_controller import router as order_router
from controllers.service_review_controller import router as review_router
from controllers.service_staff_controller import router as staff_router
from controllers.staff_service_item_controller import router as staff_service_item_router
from controllers.statistics_controller import router as statistics_router
from controllers.user_controller import router as user_router
from fastapi.openapi.utils import get_openapi
# 初始化异步调度器（全局定义）
scheduler = AsyncIOScheduler()
#激活加载.env文件
load_dotenv()
#===================== 系统生命周期事件 =====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("系统启动，开始初始化...")
    # 项目启动时执行一次订单统计更新
    db = SessionLocal()
    try:
        staff_service = ServiceStaffService(db)
        staff_service.update_all_service_staff_orders()
        log.info("系统启动，更新所有家政人员订单数量完成")
    except Exception as e:
        log.error(f"系统启动初始化失败: {e}")
    finally:
        db.close()

    # ===================== 在异步生命周期中启动调度器 =====================
    try:
        scheduler.start()
        log.info("定时任务调度器启动成功")
    except Exception as e:
        log.error(f"调度器启动失败: {e}")

    yield  # 程序运行中

    # ===================== 系统关闭时关闭调度器 =====================
    if scheduler.running:
        scheduler.shutdown()
        log.info("定时任务调度器已关闭")

    log.info("系统关闭，正在清理资源...")
    log.info("系统关闭完成  ")


#===================== 定时任务=====================
async def daily_update_staff_order_task():
    """
    每天凌晨 1 点执行
    """
    log.info("⏰ 开始执行每日定时任务：更新家政人员订单数量...")
    db = next(get_db())
    try:
        # 调用ServiceStaffService
        staff_service = ServiceStaffService(db=db)
        staff_service.update_all_service_staff_orders()
        log.info("每日定时任务执行完成：更新家政人员订单数量")
    finally:
        db.close()

# 配置定时任务（仅添加任务，不启动）
scheduler.add_job(
    daily_update_staff_order_task,
    trigger="cron",
    hour=1, minute=0, second=0
)

# 创建应用实例
IS_DEBUG = os.getenv("DEBUG", "True") == "True"
app = FastAPI(
    title="家务智能推送系统 API",
    lifespan=lifespan,
    debug=IS_DEBUG
)

app.add_exception_handler(ServiceException, service_exception_handler) # type: ignore
app.add_exception_handler(RequestValidationError, validation_exception_handler) # type: ignore
app.add_exception_handler(Exception, global_exception_handler)
# ==========================================
# 跨域配置（cors）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ===================== 文档加token按钮Authorize =====================
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="家务智能推送系统 API",
        version="0.1.0",
        routes=app.routes,
    )
    
    # 添加 Bearer Token 认证
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # 全局应用认证
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
# ===================== 静态资源映射=====================
BASE_DIR = Path(__file__).resolve().parent
IMG_DIR = BASE_DIR / "files" / "img"
os.makedirs(IMG_DIR, exist_ok=True)

app.mount(
    "/api/img",
    StaticFiles(directory=BASE_DIR / "files"/ "img"), 
    name="img"

)


# ========================================================
# JWT 拦截器
app.add_middleware(JwtInterceptorMiddleware)
# ===================== 统一路由前缀 /api ===================== 
api_router = APIRouter(prefix="/api")

# 挂载所有业务路由
api_router.include_router(recommend_router)
api_router.include_router(banner_router)
api_router.include_router(file_router)
api_router.include_router(menu_router)
api_router.include_router(payment_router)
api_router.include_router(refund_router)
api_router.include_router(role_router)
api_router.include_router(search_router)
api_router.include_router(browse_history_router)
api_router.include_router(category_router)
api_router.include_router(favorite_router)
api_router.include_router(service_item_router)
api_router.include_router(order_router)
api_router.include_router(review_router)
api_router.include_router(staff_router)
api_router.include_router(staff_service_item_router)
api_router.include_router(statistics_router)
api_router.include_router(user_router)

# 挂载主路由
app.include_router(api_router)

#===================== 启动项目 =====================
if __name__ == "__main__":
    HOST = os.getenv("SERVER_HOST", "127.0.0.1")
    PORT = int(os.getenv("SERVER_PORT", 8000))     
    RELOAD = os.getenv("DEBUG", "True") == "True"
    uvicorn.run("main:app", host=HOST, port=PORT, reload=RELOAD)