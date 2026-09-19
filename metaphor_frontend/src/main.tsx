// 应用入口 & 全局样式
import React from "react";
import ReactDOM from "react-dom/client";
import './index.css'
import App from './App.tsx'
import "antd/dist/reset.css";

// createRoot(document.getElementById('root')!).render(
//   <StrictMode>
//     <App />
//   </StrictMode>,
// )
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
