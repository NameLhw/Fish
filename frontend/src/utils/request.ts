import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'

/**
 * 请求工具
 *
 * 开发模式 (Vite proxy)：
 *   baseURL 为 '/api'，所有请求经 vite.config.ts 的 proxy 转发到 localhost:8000
 *
 * 生产部署：
 *   在 frontend/.env 中设置 VITE_API_BASE_URL=http://your-server:8000
 *   baseURL 自动切换为该绝对地址
 */
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ---------------- 请求拦截器 ----------------
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ---------------- 响应拦截器 ----------------
request.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    const { response } = error
    if (response) {
      switch (response.status) {
        case 401:
          localStorage.removeItem('token')
          window.location.href = '/login'
          break
        case 403:
          console.error('没有权限访问该资源')
          break
        case 404:
          console.error('请求的资源不存在')
          break
        case 500:
          console.error('服务器内部错误')
          break
      }
    } else {
      console.error('网络异常，请检查网络连接')
    }
    return Promise.reject(error)
  },
)

export default request
