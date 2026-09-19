import axios from "axios";
import type { Task } from "../types/contracts";

const baseURL = import.meta.env.VITE_API_BASE || "/api";

export const api = axios.create({ 
  baseURL,
  timeout: 15000,
});

// 🔥 新增：统一获取API路径的函数
export function getApiUrl(path: string): string {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseURL}${cleanPath}`;
}

export async function pingApi() {
  const res = await api.get('/health')
  const d = res.data
  const ok = d?.ok === true || d?.status === 'healthy'
  return { ok, service: d?.service ?? 'metaphor-backend', raw: d }
}

export async function analyzeHeader(headers: string[]) {
  const { data } = await api.post("/v1/module1/analyze/header", { headers });
  return data as unknown;
}

export async function getTask(taskId: string) {
  const { data } = await api.get<Task>(`/v1/tasks/${taskId}`);
  return data;
}