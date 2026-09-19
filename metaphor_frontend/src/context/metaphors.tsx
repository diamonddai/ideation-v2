import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

// 类型定义
type Theme = "Nature" | "Artifact" | "Body" | "Life" | "Others";
type GuidedMethod = "semantic" | "functional" | "perceptual" | "structural" | "null";
type Guided2ndLevelMethod = "symbol" | "causality" | "taxonomy" | "behavior" | "usage" | "color" | "shape" | "size" | "temporal" | "spatial" | "null";
type Method = "blinded" | "guided";

type Variations = {
  id: string;
  field: string;
  keyword: string;
  theme: Theme;
  method: Method;
  guidedmethod: GuidedMethod;
  guided2ndLevelMethod: Guided2ndLevelMethod;
  rNorm: number;
  thumb: string;
};

export type Link = {
  source: string;
  target: string;
  distance: number;
};

export type BackendPayload = {
  capsules: Variations[];
  links?: Link[];
};

// 初始数据
const payloadDemo: BackendPayload = {
  capsules: [
    { id: "c1", field: "immigrant", keyword: "Moon", theme: "Nature", method: "guided", guidedmethod: "semantic", guided2ndLevelMethod: "causality", rNorm: 0.25, thumb: "/moon.png" },
    { id: "c2", field: "immigrant", keyword: "Tree rings", theme: "Nature", method: "guided", guidedmethod: "semantic", guided2ndLevelMethod: "taxonomy", rNorm: 0.45, thumb: "/treerings.png" },
    { id: "c3", field: "immigrant", keyword: "Tide", theme: "Artifact", method: "blinded", guidedmethod: "null", guided2ndLevelMethod: "null", rNorm: 0.4, thumb: "/tide.png" },
    { id: "c4", field: "immigrant", keyword: "Map", theme: "Artifact", method: "guided", guidedmethod: "functional", guided2ndLevelMethod: "usage", rNorm: 0.6, thumb: "/map.png" },
    { id: "c5", field: "immigrant", keyword: "Bridge", theme: "Artifact", method: "guided", guidedmethod: "functional", guided2ndLevelMethod: "behavior", rNorm: 0.5, thumb: "/bridge.png" },
    { id: "c6", field: "immigrant", keyword: "Village", theme: "Body", method: "guided", guidedmethod: "perceptual", guided2ndLevelMethod: "shape", rNorm: 0.55, thumb: "/village.png" },
    { id: "c7", field: "immigrant", keyword: "Belonging", theme: "Life", method: "guided", guidedmethod: "structural", guided2ndLevelMethod: "spatial", rNorm: 0.35, thumb: "/belonging.png" },
    { id: "c8", field: "immigrant", keyword: "Moonnight", theme: "Others", method: "blinded", guidedmethod: "null", guided2ndLevelMethod: "null", rNorm: 0.42, thumb: "/full-moon-night.png" },
    { id: "c9", field: "immigrant", keyword: "Bird", theme: "Nature", method: "guided", guidedmethod: "structural", guided2ndLevelMethod: "temporal", rNorm: 0.3, thumb: "/bird.png" },
  ],
  links: [
    { source: "c1", target: "c2", distance: 60 },
    { source: "c1", target: "c3", distance: 40 },
    { source: "c2", target: "c3", distance: 30 },
    { source: "c4", target: "c5", distance: 50 },
    { source: "c7", target: "c8", distance: 30 },
  ],
};

// Context 接口
interface MetaphorsContextType {
  metaphors: BackendPayload;
  setMetaphors: (data: BackendPayload) => void;
}

// 创建 Context
const MetaphorsContext = createContext<MetaphorsContextType | undefined>(undefined);

// Provider 组件
export function MetaphorsProvider({ children }: { children: ReactNode }) {
  const [metaphors, setMetaphors] = useState<BackendPayload>(payloadDemo);

  return (
    <MetaphorsContext.Provider value={{ metaphors, setMetaphors }}>
      {children}
    </MetaphorsContext.Provider>
  );
}

// Hook
export function useMetaphors() {
  const context = useContext(MetaphorsContext);
  if (context === undefined) {
    throw new Error('useMetaphors must be used within a MetaphorsProvider');
  }
  return context;
}

// 导出所有类型供其他文件使用
export type { Theme, GuidedMethod, Guided2ndLevelMethod, Method, Variations };

// 声明全局类型扩展（解决 window.payloadDemo 问题）
declare global {
  interface Window {
    payloadDemo?: BackendPayload;
  }
}