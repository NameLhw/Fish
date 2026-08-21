<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from './utils/request'

// 后端连通状态: checking | ok | fail
const backendStatus = ref<'checking' | 'ok' | 'fail'>('checking')
const backendDetail = ref('正在检测后端连接...')

async function checkBackend() {
  backendStatus.value = 'checking'
  backendDetail.value = '正在检测后端连接...'
  try {
    const res: any = await request.get('/health')
    backendStatus.value = 'ok'
    backendDetail.value = `后端运行正常 (${res.data?.service || '校园版咸鱼'} v${res.data?.version || '?'})`
  } catch (e: any) {
    backendStatus.value = 'fail'
    backendDetail.value = e?.response
      ? `后端返回错误 (${e.response.status})`
      : '无法连接后端，请确认 start.sh 已启动'
  }
}

onMounted(checkBackend)
</script>

<template>
  <div class="page">
    <header class="hero">
      <div class="logo">🐟</div>
      <h1>校园版咸鱼</h1>
      <p>面向大学生的二手交易平台 · 前端已就绪</p>
    </header>

    <main class="cards">
      <!-- 前端状态 -->
      <section class="card">
        <div class="card-head">
          <span class="dot ok"></span>
          <h2>前端服务</h2>
        </div>
        <p class="desc">
          Vite 开发服务器运行中，<strong>HMR 热更新已启用</strong> —— 修改代码后浏览器自动刷新，无需手动更新。
        </p>
        <p class="meta">开发地址：http://localhost:5173</p>
      </section>

      <!-- 后端状态 -->
      <section class="card">
        <div class="card-head">
          <span class="dot" :class="backendStatus"></span>
          <h2>后端服务</h2>
        </div>
        <p class="desc">{{ backendDetail }}</p>
        <p class="meta">API 代理：/api → http://localhost:8000</p>
        <button class="btn" @click="checkBackend">重新检测</button>
      </section>

      <!-- 说明 -->
      <section class="card tip">
        <h2>下一步</h2>
        <ol>
          <li>在 <code>src/</code> 下创建页面组件（如 <code>Home.vue</code>）</li>
          <li>通过 <code>import request from './utils/request'</code> 调用后端接口</li>
          <li>按 <code>Ctrl+C</code> 停止服务</li>
        </ol>
      </section>
    </main>

    <footer class="footer">苏州大学 · 软件工程综合实践 / 大四实习项目</footer>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  max-width: 640px;
  margin: 0 auto;
  padding: 24px 16px 40px;
}

.hero {
  text-align: center;
  padding: 48px 0 32px;
}

.logo {
  font-size: 56px;
  margin-bottom: 12px;
}

.hero h1 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
}

.hero p {
  color: var(--text-light);
  font-size: 14px;
}

.cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
}

.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.card-head h2 {
  font-size: 16px;
  font-weight: 600;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #d1d5db;
}

.dot.ok {
  background: var(--success);
}

.dot.fail {
  background: var(--danger);
}

.dot.checking {
  background: #f59e0b;
}

.desc {
  color: var(--text);
  font-size: 14px;
  line-height: 1.7;
  margin-bottom: 8px;
}

.meta {
  color: var(--text-light);
  font-size: 12px;
  margin-bottom: 8px;
}

.btn {
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 13px;
  margin-top: 4px;
}

.btn:hover {
  background: var(--primary-dark);
}

.tip ol {
  padding-left: 20px;
  font-size: 14px;
  line-height: 2;
  color: var(--text);
}

.tip code {
  background: #f3f4f6;
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 6px;
  font-size: 12px;
}

.footer {
  text-align: center;
  color: var(--text-light);
  font-size: 12px;
  margin-top: 32px;
}
</style>
