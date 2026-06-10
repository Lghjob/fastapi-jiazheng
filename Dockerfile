# 1. 选择基础系统（底层环境）
FROM --platform=arm64 python:3.12-slim 

# 2. 设置容器内的工作目录
WORKDIR /main

# 3. 把本地的依赖文件复制到容器里
COPY requirements.txt .

# 4. 在容器里安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 5. 把你所有的项目代码复制到容器里
COPY . .

# 6. 声明容器暴露的端口
EXPOSE 8000

# 7. 容器启动后自动运行的命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]