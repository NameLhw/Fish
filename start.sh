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

# 选择 Python 解释器：优先使用 venv 内的解释器（最可靠），
# 避免 Windows 的 WindowsApps python3 商店 stub（执行会静默退出）
pick_python() {
    if [ -f "venv/bin/python3" ]; then
        PY_CMD="venv/bin/python3"
    elif [ -f "venv/bin/python" ]; then
        PY_CMD="venv/bin/python"
    elif [ -f "venv/Scripts/python.exe" ]; then
        PY_CMD="venv/Scripts/python.exe"
    elif command -v python3 >/dev/null 2>&1; then
        PY_CMD=python3
    else
        PY_CMD=python
    fi
}

echo "========================================"
echo "  校园版咸鱼 — 一键启动"
echo "========================================"

# ---------- [1/5] 后端依赖 ----------
echo ""
echo "[1/5] 安装后端依赖..."

# 后端就在项目根目录（app.py / requirements.txt 在此）
if [ -f "$ROOT_DIR/requirements.txt" ]; then
    cd "$ROOT_DIR"
    if [ ! -d "venv" ]; then
        echo "  创建 Python 虚拟环境..."
        python3 -m venv venv 2>/dev/null || python -m venv venv
    fi
    # 兼容 Linux / Windows（. 为 POSIX 语法，dash/bash 均支持）
    if [ -f "venv/bin/activate" ]; then
        . venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        . venv/Scripts/activate
    fi
    # 注意：用相对路径调用 pip，避免中文路径传参乱码（Windows Git Bash）
    pip install -r requirements.txt -q
    echo "  ✓ 后端依赖就绪"
else
    echo "  ⚠ 未找到 requirements.txt，跳过"
fi

# ---------- [2/5] 初始化数据库 ----------
echo "[2/5] 检查数据库..."
if [ ! -f "$ROOT_DIR/campus_flea.db" ]; then
    echo "  初始化数据库..."
    cd "$ROOT_DIR"
    pick_python
    "$PY_CMD" init_db.py
    echo "  ✓ 数据库已初始化"
else
    echo "  ✓ 数据库已存在"
fi

# ---------- [3/5] 前端依赖 ----------
echo "[3/5] 检查前端依赖..."

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
echo "[4/5] 启动后端 (端口 ${PORT})..."

cd "$ROOT_DIR"

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    . venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    . venv/Scripts/activate
fi

# 选择 Python 解释器（提前确定，确保 $! 是 python 进程真实 PID，
# 否则 Ctrl+C 时 kill 不到 python，会留下孤儿进程占用端口）
pick_python

# 清理占用端口的残留进程（防止 "Address already in use" 报错）
OLD_PIDS=""
if command -v lsof >/dev/null 2>&1; then
    OLD_PIDS=$(lsof -t -i:"${PORT}" 2>/dev/null)
elif command -v fuser >/dev/null 2>&1; then
    OLD_PIDS=$(fuser "${PORT}/tcp" 2>/dev/null)
fi
if [ -n "$OLD_PIDS" ]; then
    echo "  ⚠ 端口 ${PORT} 被旧进程占用 (PID: ${OLD_PIDS})，正在清理..."
    kill $OLD_PIDS 2>/dev/null
    sleep 1
    kill -9 $OLD_PIDS 2>/dev/null
    sleep 1
fi

"$PY_CMD" app.py &
BACKEND_PID=$!

# 轮询健康接口校验后端真正就绪（curl 探测比 kill -0 跨环境更可靠，
# 例如 Windows Git Bash 后台任务中 $! 是包装进程，kill -0 会误判）
BACKEND_READY=0
i=0
while [ $i -lt 15 ]; do
    if curl -s "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
        BACKEND_READY=1
        break
    fi
    kill -0 "$BACKEND_PID" 2>/dev/null || break
    sleep 1
    i=$((i + 1))
done

if [ "$BACKEND_READY" -eq 1 ]; then
    echo "  ✓ 后端已启动 (PID: $BACKEND_PID)"
else
    echo "  ✗ 后端启动失败（端口 ${PORT} 无响应）"
    echo "    常见原因: 端口被占用 / 依赖缺失，请查看上方错误信息"
    exit 1
fi

# ---------- 启动前端 ----------
if [ "$HAS_FRONTEND" = true ]; then
    if [ "$DEV_FRONTEND" = "1" ]; then
        # 开发模式：Vite dev server（HMR 热更新），仅本机/局域网可访问
        echo "[5/5] 开发模式启动前端 (http://localhost:5173)..."
        cd "$FRONTEND"
        npm run dev &
        FRONTEND_PID=$!
        cd "$ROOT_DIR"
        echo "  前端(dev): http://localhost:5173"
    else
        # 生产/云环境模式：构建前端，由后端在 8000 端口的 /app/ 下托管
        # CloudStudio 只暴露一个端口时，外部也能直接访问前端
        echo "[5/5] 构建前端并由后端托管 (/app/)..."
        cd "$FRONTEND"
        npm run build
        cd "$ROOT_DIR"
        echo "  前端(托管): http://localhost:${PORT}/app/"
    fi

    echo ""
    echo "========================================"
    echo "  ✅ 全部启动成功"
    if [ "$DEV_FRONTEND" = "1" ]; then
        echo "  前端(dev):  http://localhost:5173"
        echo "  后端:       http://localhost:${PORT}"
        echo "  (dev 模式仅限本机浏览器访问)"
    else
        echo "  后端页面:   http://localhost:${PORT}/"
        echo "  前端页面:   http://localhost:${PORT}/app/"
        echo ""
        echo "  ⚠ CloudStudio 用户注意:"
        echo "    上述 localhost 地址仅供容器内部验证，"
        echo "    外部浏览器请使用端口面板中 ${PORT} 端口"
        echo "    的公网链接，并在其后拼接路径 / 和 /app/"
        echo "    (5173 端口未对外暴露，无法从外部访问)"
    fi
    echo "  按 Ctrl+C 停止所有服务"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "  ✅ 后端启动成功"
    echo "  后端页面:   http://localhost:${PORT}/"
    echo "  ⚠ CloudStudio 用户请用端口面板中 ${PORT} 端口的公网链接访问"
    echo "  按 Ctrl+C 停止服务"
    echo "========================================"
fi

# ---------- 优雅退出 ----------
cleanup() {
    echo ""
    echo "正在停止服务..."
    kill "$BACKEND_PID" 2>/dev/null
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
    # 兜底清理残留进程（npm/vite 是孙进程，kill npm 杀不到它们）
    pkill -f "app\.py" 2>/dev/null
    pkill -f "vite" 2>/dev/null
    wait "$BACKEND_PID" 2>/dev/null
    [ -n "$FRONTEND_PID" ] && wait "$FRONTEND_PID" 2>/dev/null
    echo "已停止。"
    exit 0
}
trap cleanup INT TERM

wait
