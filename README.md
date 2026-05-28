Markdown
# 家务服务智能推送系统 - 高性能异步后端 API
# Housework Service Intelligent Push System (Backend)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red?style=flat)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 📌 项目简介
本项目是一款基于 **FastAPI** 异步高并发框架重构的企业级家务智能推送系统后端。系统采用前后端分离架构，针对原有传统架构进行了全面的 Python 化高性能重写。核心业务涵盖家政服务类目管理、多角色权限认证、订单交易流转以及多种智能推荐算法，专为高频家务服务匹配场景设计。

> **项目定位**：标准三层架构（MVC 变种）的分布式后端 API，具备严格的数据校验、完备的异常处理机制以及标准的代码组织规范。
>
> *这是我真正意义上的第一个开源项目，希望能为 Python 后端生态和高并发服务匹配场景提供一些参考与帮助。*

---

## 🚀 核心技术栈
* **核心框架**：`FastAPI` (基于 Starlette 与 Pydantic，具备天然的异步高并发处理能力)
* **ORM 框架**：`SQLAlchemy 2.0+` (采用面向对象思维进行高效的数据库持久化操作)
* **安全认证**：`PyJWT` (实现无状态、多角色的路由拦截器与完备的权限控制)
* **数据校验**：`Pydantic v2` (实现企业级的入参严格过滤、DTO 数据传输对象封装)
* **工程规范**：严格划分 Controller、Service、Model 层，具备全局异常捕获（Exception Handler）与标准统一响应体（Result JSON）。

---

## 📂 核心架构设计

项目目录严格遵循工业级高内聚、低耦合的设计原则，结构如下：

```text
.
├─config/         # 全局配置（CORS跨域、数据库连接池、JWT拦截中间件）
├─controllers/    # 路由控制层（接收请求、Pydantic 参数校验、分发业务）
├─models/         # 数据模型层（SQLAlchemy ORM 实体映射、表结构设计）
├─schemas/        # 数据校验层（Pydantic Schemas、DTO 传输对象模型）
├─service/        # 核心业务逻辑层（事务控制、多策略推荐算法实现）
│  └─recommendation/  # 智能推荐引擎（包含多策略核心推荐算法）
└─utils/          # 通用工具类（JWT令牌、密码哈希、响应状态码定义）
```
# ⚙️ 核心亮点模块说明
统一拦截与多角色鉴权：在 config/jwt_interceptor.py 中实现路由拦截机制，通过解析 JWT 令牌进行动态身份验权，无缝对接 role_model 实现多级菜单的权限控制。

多策略智能推送引擎：在 service/recommendation/ 下独立实现了三套推荐机制，全面契合人工智能专业应用场景：

基于内容的机器学习推荐（Content-Based）：结合了服务项目标题文本的词向量，通过余弦计算相似度完成推荐。

基于用户协同过滤（User-Based CF）：通过群体行为相似度，计算家务服务的相似度进行精准推送。

基于用户画像的推荐（User-Profile）：通过对登录用户历史的交易行为等信息计算，推荐与历史购买相似度较高的服务。

健壮的防御性编程：在 utils/exceptions/ 实现了全局异常捕获，确保系统在发生运行时错误时，仍能向前端返回统一格式的 JSON 错误凭证（ResultCode），提高系统可用性与容错能力。

# 🛠️ 本地开发环境部署
1. 克隆项目
Bash
git clone https://github.com/[你的GitHub用户名]/[你的仓库名称].git
cd [你的仓库名称]
2. 创建虚拟环境并安装依赖
Bash
python -m venv venv

# Windows 激活命令
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
3. 配置数据库连接
修改 config/database.py 中的数据库连接字符串（URL）或者新建.env文件创建数据库链接字符串，具体可参考.env.example，配置您本地的 MySQL/SQLite 数据库信息：

Python
DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/db_name"
4. 启动服务
使用 Uvicorn 驱动异步高并发服务器：

Bash
uvicorn main:app --reload
服务启动后，可直接访问 http://127.0.0.1:8000/docs 查阅自动生成的交互式 Swagger API 文档。

# 📄 开源协议
本项目基于 MIT License 协议开源。
