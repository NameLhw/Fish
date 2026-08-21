#!/bin/bash
# ============================================================
#  校园版咸鱼 — 一键启动脚本
#  安装依赖 + 初始化数据库 + 启动前后端
#
#  用法:  sh start.sh    （或 bash start.sh，两者均可）
#  适用:  Linux / macOS / CloudStudio / Windows Git Bash
#  注意:  脚本使用 POSIX 语法，兼容 dash（sh）与 bash
# ============================================================
set -e

# ---------- 路径 ----------
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND="$ROOT_DIR/frontend"

# 后端端口（CloudStudio / 前端代理模式用 8000，匹配 vite proxy）
export PORT="${PORT:-8000}"

echo "========================================"
echo "  校园版咸鱼 — 一键启动"
echo "========================================"

# ---------- [1/4] 后端依赖 ----------
echo ""
echo "[1/4] 安装后端依赖..."

# 后端就在项目根目录（app.py / requirements.txt 在此）
if [ -f "$ROOT_DIR/requirements.txt" ]; then
    if [ ! -d "$ROOT_DIR/venv" ]; then
        echo "  创建 Python 虚拟环境..."
        python3 -m venv "$ROOT_DIR/venv" 2>/dev/null || python -m venv "$ROOT_DIR/venv"
    fi
    # 兼容 Linux / Windows（. 为 POSIX 语法，dash/bash 均支持）
    if [ -f "$ROOT_DIR/venv/bin/activate" ]; then
        . "$ROOT_DIR/venv/bin/activate"
    elif [ -f "$ROOT_DIR/venv/Scripts/activate" ]; then
        . "$ROOT_DIR/venv/Scripts/activate"
    fi
    pip install -r "$ROOT_DIR/requirements.txt" -q
    echo "  ✓ 后端依赖就绪"
else
    echo "  ⚠ 未找到 requirements.txt，跳过"
fi

# ---------- [2/4] 初始化数据库 ----------
echo "[2/4] 检查数据库..."
if [ ! -f "$ROOT_DIR/campus_flea.db" ]; then
    echo "  初始化数据库..."
    cd "$ROOT_DIR"
    python3 init_db.py 2>/dev/null || python init_db.py
    echo "  ✓ 数据库已初始化"
else
    echo "  ✓ 数据库已存在"
fi

# ---------- [3/4] 前端依赖 ----------
echo "[3/4] 检查前端依赖..."

if [ -d "$FRONTEND" ] && [ -f "$FRONTEND/package.json" ]; then
    cd "$FRONTEND"
    if [ ! -d "node_modules" ]; then
        echo "  安装前端依赖..."
        npm install
    fi
    echo "  ✓ 前端依赖就绪"
    cd "$ROOT_DIR"
    HAS_FRONTEND=true
else
    echo "  ⚠ 未找到 frontend/package.json，跳过前端（仅启动后端）"
    HAS_FRONTEND=false
fi

# ---------- 启动后端 ----------
echo ""
echo "[3/4] 启动后端 (http://0.0.0.0:${PORT})..."

cd "$ROOT_DIR"

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    . venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    . venv/Scripts/activate
fi

python3 app.py 2>/dev/null || python app.py &
BACKEND_PID=$!

# 等待后端就绪
sleep 2
echo "  ✓ 后端已启动 (PID: $BACKEND_PID)"

# ---------- 启动前端 ----------
if [ "$HAS_FRONTEND" = true ]; then
    echo "[4/4] 启动前端 (http://localhost:5173)..."

    cd "$FRONTEND"
    npm run dev &
    FRONTEND_PID=$!
    cd "$ROOT_DIR"

    echo ""
    echo "========================================"
    echo "  ✅ 全部启动成功"
    echo "  前端:  http://localhost:5173"
    echo "  后端:  http://localhost:${PORT}"
    echo "  按 Ctrl+C 停止所有服务"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "  ✅ 后端启动成功"
    echo "  后端:  http://localhost:${PORT}"
    echo "  按 Ctrl+C 停止服务"
    echo "========================================"
fi

# ---------- 优雅退出 ----------
cleanup() {
    echo ""
    echo "正在停止服务..."
    kill $BACKEND_PID 2>/dev/null
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    [ -n "$FRONTEND_PID" ] && wait $FRONTEND_PID 2>/dev/null
    echo "已停止。"
    exit 0
}
trap cleanup INT TERM

wait
