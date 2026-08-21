#!/bin/bash
# ============================================================
#  校园版咸鱼 — 一键启动脚本
#  安装依赖 + 初始化数据库 + 启动前后端
#
#  用法:  sh start.sh    （或 bash start.sh，两者均可）
#  适用:  Linux / macOS / CloudStudio / Windows Git Bash
#  注意:  脚本使用 POSIX 语法，兼容 dash（sh）与 bash
# ============================================================
# 不使用 set -e：后台进程崩溃时 set -e 会导致脚本提前退出，
# 无法执行健康检查和错误提示。改用显式错误处理。

# ---------- 路径 ----------
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND="$ROOT_DIR/frontend"

# 后端端口（CloudStudio / 前端代理模式用 8000，匹配 vite proxy）
export PORT="${PORT:-8000}"

# ---------- 工具函数 ----------

# 选择 Python 解释器：优先 venv 内的，避免 WindowsApps python3 stub
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

# 杀掉占用指定端口的所有进程（兼容多种 Linux 环境）
kill_port() {
    local port="$1"
    local pids=""

    # 方法1: lsof
    if command -v lsof >/dev/null 2>&1; then
        pids=$(lsof -t -i:"${port}" 2>/dev/null)
    fi

    # 方法2: fuser
    if [ -z "$pids" ] && command -v fuser >/dev/null 2>&1; then
        pids=$(fuser "${port}/tcp" 2>/dev/null)
    fi

    # 方法3: ss + grep
    if [ -z "$pids" ] && command -v ss >/dev/null 2>&1; then
        pids=$(ss -tlnp 2>/dev/null | grep ":${port} " | grep -oP 'pid=\K[0-9]+' | tr '\n' ' ')
    fi

    # 方法4: netstat + awk (Windows Git Bash / 老旧 Linux)
    if [ -z "$pids" ] && command -v netstat >/dev/null 2>&1; then
        pids=$(netstat -ano 2>/dev/null | grep ":${port} " | grep -i "LISTEN" | awk '{print $NF}' | sort -u | tr '\n' ' ')
    fi

    if [ -n "$pids" ]; then
        echo "  ⚠ 端口 ${port} 被旧进程占用 (PID: ${pids})，正在清理..."
        for pid in $pids; do
            kill "$pid" 2>/dev/null
        done
        sleep 1
        for pid in $pids; do
            kill -9 "$pid" 2>/dev/null
        done
        sleep 1
        echo "  ✓ 端口 ${port} 已释放"
    fi
}

# 杀掉所有运行 app.py 的 Python 进程（兜底，防止端口探测遗漏）
kill_app_py() {
    if command -v pkill >/dev/null 2>&1; then
        local count
        count=$(pgrep -f "app\.py" 2>/dev/null | wc -l)
        if [ "$count" -gt 0 ]; then
            echo "  ⚠ 发现 ${count} 个旧 app.py 进程，正在清理..."
            pkill -f "app\.py" 2>/dev/null
            sleep 1
            pkill -9 -f "app\.py" 2>/dev/null
            sleep 1
            echo "  ✓ 旧 app.py 进程已清理"
        fi
    fi
}

echo "========================================"
echo "  校园版咸鱼 — 一键启动"
echo "========================================"

# ---------- [1/5] 后端依赖 ----------
echo ""
echo "[1/5] 安装后端依赖..."

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

# ---------- [4/5] 启动后端 ----------
echo ""
echo "[4/5] 启动后端 (端口 ${PORT})..."

cd "$ROOT_DIR"

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    . venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    . venv/Scripts/activate
fi

# 选择 Python 解释器
pick_python

# 清理旧进程（双保险：端口探测 + 进程名匹配）
kill_port "$PORT"
kill_app_py

# 启动后端
"$PY_CMD" app.py &
BACKEND_PID=$!

# 轮询健康接口校验后端是否真正就绪
BACKEND_READY=0
i=0
while [ $i -lt 10 ]; do
    # 先检查进程是否还活着
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        # 进程已退出，等待一下让输出刷新
        sleep 1
        break
    fi
    # 探测健康接口
    if curl -s "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
        BACKEND_READY=1
        break
    fi
    sleep 1
    i=$((i + 1))
done

if [ "$BACKEND_READY" -eq 1 ]; then
    echo "  ✓ 后端已启动 (PID: $BACKEND_PID)"
else
    echo "  ✗ 后端启动失败"
    echo "    请查看上方的错误信息，常见原因:"
    echo "    1. 端口 ${PORT} 被占用 → 执行: pkill -9 -f app.py"
    echo "    2. 依赖缺失 → 执行: pip install -r requirements.txt"
    echo "    3. 数据库问题 → 删除 campus_flea.db 后重试"

    # 清理失败的进程
    kill "$BACKEND_PID" 2>/dev/null
    kill -9 "$BACKEND_PID" 2>/dev/null
    exit 1
fi

# ---------- [5/5] 前端 ----------
if [ "$HAS_FRONTEND" = true ]; then
    if [ "$DEV_FRONTEND" = "1" ]; then
        # 开发模式：Vite dev server（HMR），仅本机可访问
        echo "[5/5] 开发模式启动前端 (http://localhost:5173)..."
        cd "$FRONTEND"
        npm run dev &
        FRONTEND_PID=$!
        cd "$ROOT_DIR"
    else
        # 生产/云环境模式：构建前端，由后端在 /app/ 下托管
        echo "[5/5] 构建前端并由后端托管 (/app/)..."
        cd "$FRONTEND"
        npm run build
        cd "$ROOT_DIR"
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
        echo "    上述 localhost 仅供容器内部验证，"
        echo "    外部浏览器请用端口面板 ${PORT} 的公网链接"
        echo "    拼接路径 / (后端) 和 /app/ (前端)"
        echo "    (5173 端口未暴露，不可从外部访问)"
    fi
    echo "  按 Ctrl+C 停止所有服务"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "  ✅ 后端启动成功"
    echo "  后端页面:   http://localhost:${PORT}/"
    echo "  ⚠ CloudStudio 用户请用端口面板 ${PORT} 的公网链接"
    echo "  按 Ctrl+C 停止服务"
    echo "========================================"
fi

# ---------- 优雅退出 ----------
cleanup() {
    echo ""
    echo "正在停止服务..."
    # 杀后端
    kill "$BACKEND_PID" 2>/dev/null
    kill -9 "$BACKEND_PID" 2>/dev/null
    # 杀前端（dev 模式才有）
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
    [ -n "$FRONTEND_PID" ] && kill -9 "$FRONTEND_PID" 2>/dev/null
    # 兜底：按名字杀残留进程
    pkill -f "app\.py" 2>/dev/null
    pkill -f "vite" 2>/dev/null
    echo "已停止。"
    exit 0
}
trap cleanup INT TERM

wait
