# Metaphor Generation Frontend
基于表格数据生成隐喻性图像提示词的多 Agent 前端系统
- 三栏工作流：**理解阶段（数据/字段） → 发散阶段（隐喻候选） → 收敛阶段（映射与预览）**
- 与 FastAPI 后端对接（/api/v1/...）
- 前端框架为React + TypeScript + Vite

## 项目结构

```
metaphor-frontend/
├── node_modules/ #第三方依赖，记得放在.gitgnore,不要同步到github上了
├── public/       #静态资源（favicon、静态图片）
├── src/          #
│   ├──app/
│   │   ├──AppLayout.tsx          # 页面骨架与三栏布局（只做排版）
│   ├──components/                #放纯通用组件（PanelCard、PhaseHeaderRow）
│   │   ├──PanelCard.tsx          # 通用卡片外壳（样式统一）
│   │   ├──PhaseHeaderRow.tsx
│   ├──features/
│   │   ├──understand/
│   │   │   ├──UnderstandPanel.tsx  # 左：理解阶段（当前只放占位）
│   │   ├──diverge/
│   │   │   ├──DivergePanel.tsx     # 中：发散阶段（当前只放占位）
│   │   ├──converge/
│   │   │   ├──ConvergePanel.tsx    # 右：收敛阶段（当前只放占位）
│   ├── assets    # 项目用到的图片/图标/样式等
│   ├── lib
│   │   ├──api.ts # 统一的 Axios 实例与 API 封装（只写最小接口）
│   ├── types
│   │   ├──contracts.ts  # 轻量 TypeScript 类型：Task/Idea/Mapping 等公共结构 放跨模块的接口定义
├── App.css       #App 局部样式（可选）
├── App.tsx       ## 入口只负责拼装 AppLayout
├── index.css     #全局样式（含 AntD reset）
├── main.tsx      #入口文件，挂载 React、引入全局样式
├── vite-env.d.ts      # Vite 的 TS 环境声明（自动生成）
├── .gitignore         #
├── eslint.config.js   # ESLint 配置（如使用）
├── index.html         #单页应用模板（root 容器在这里）
├── package-lock.json  #包信息与脚本（dev/build/preview） 
├── package.json       # 锁文件（保证大家安装到一致版本）                 
├── tsconfig.app.json  # TS - 应用构建配置（Vite 生成）
├── tsconfig.json      #TypeScript 基础配置（轻量：可关闭 strict）
├── tsconfig.node.json # TS - Node/Vite 配置（Vite 生成）
├── README.md          # 项目说明
└── vite.config.ts     #Vite 配置（含代理，将 /api 指到 FastAPI）
```

## 快速开始
1. 安装依赖：
```bash
cd metaphor-frontend
npm i antd axios react-router-dom
```

2. 启动服务：
```bash
npm run dev
```


3.前后端接口测试

[举例：前端写个Button 点击]
```bash
const [loading, setLoading] = useState(false) // 控制按钮 loading
const [text, setText] = useState('尚未测试')   // 展示“后端状态：xxx”

const handlePing = async () => {
  try {
    setLoading(true)              // 点击后，先让按钮转起来
    const data = await pingApi()  // 等待网络请求返回 { ok, service, raw }

    if (data.ok) {                // 统一用 data.ok 判断成功/失败
      setText(`✅ 已连接：${data.service}`)
      message.success('后端联通成功')  // AntD 的成功气泡
    } else {
      setText('⚠️ 返回非 ok')        // 200 但返回体不符合判定条件
    }
  } catch (e: any) {              // 例如 404/500/网络断开会进入这里
    setText(`❌ 失败：${e?.message ?? '未知错误'}`)
    message.error('后端联通失败')
  } finally {
    setLoading(false)             // 无论成功失败，都结束 loading
  }
}
```
   ↓
handlePing()（前端事件处理）
   ↓  await
pingApi()（封装好的网络请求）
   ↓  axios 发起 GET /api/health
Vite 代理把 /api/* → http://localhost:8000/api/*
   ↓
FastAPI 命中路由 /api/health，返回 JSON
   ↓
axios 把 JSON 放到 res.data
   ↓
pingApi 整理结果 { ok, service, raw }
   ↓
handlePing 收到结果，更新 React state
   ↓
组件重新渲染，显示“已连接/失败”文字与提示
```
