@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ================================
echo   校园版咸鱼 - 启动中...
echo ================================
echo.

REM 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo [1/3] 创建虚拟环境...
    python -m venv venv
)

echo [1/3] 激活虚拟环境...
call venv\Scripts\activate.bat

echo [2/3] 安装依赖...
pip install -r requirements.txt -q

echo [3/3] 检查数据库...
if not exist "campus_flea.db" (
    echo       初始化数据库...
    python init_db.py
)

echo.
echo ================================
echo   启动成功!
echo   访问地址: http://127.0.0.1:5000
echo   管理员: admin / admin123
echo ================================
echo.

python app.py

pause
