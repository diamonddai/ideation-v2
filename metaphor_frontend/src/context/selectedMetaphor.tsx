// context/selectedMetaphor.tsx

import React, { createContext, useContext, useState } from 'react';

// 定义映射规范的类型
interface MappingSpec {
  mapping_id: string;
  keyword: string;
  dataFact: string;
  contextDescription: string;
  defaultPlan: Array<{
    dataField: string;
    subitemId: string;
    subitemName: string;
    channels: string[];
  }>;
  field1: {
    dataField: string;
    subitemOptions: Array<{
      subitem_id: string;
      name: string;
      geometry: string;
    }>;
    channels: {
      allowed: string[];
      default: string[];
    };
  };
  field2: {
    dataField: string;
    subitemOptions: Array<{
      subitem_id: string;
      name: string;
      geometry: string;
    }>;
    channels: {
      allowed: string[];
      default: string[];
    };
  };
}

// 定义选中隐喻的数据结构
interface SelectedMetaphorData {
  id: string;
  keyword: string;
  thumb: string;
  mapping_spec?: MappingSpec;
  dimensions?: string[];  // ✅ 添加 dimensions 字段
  field?: string;         // ✅ 可选：添加 field 字段（数据主题）
  dataFact?: string;      // ✅ 可选：添加 dataFact 字段
}

// Context类型定义
interface SelectedMetaphorContextType {
  selectedMetaphor: SelectedMetaphorData | null;
  setSelectedMetaphor: (metaphor: SelectedMetaphorData | null) => void;
}

// 创建Context
const SelectedMetaphorContext = createContext<SelectedMetaphorContextType>({
  selectedMetaphor: null,
  setSelectedMetaphor: () => {},
});

// Provider组件
export const SelectedMetaphorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedMetaphor, setSelectedMetaphor] = useState<SelectedMetaphorData | null>(null);

  return (
    <SelectedMetaphorContext.Provider value={{ selectedMetaphor, setSelectedMetaphor }}>
      {children}
    </SelectedMetaphorContext.Provider>
  );
};

// Hook用于使用context
export const useSelectedMetaphor = () => {
  const context = useContext(SelectedMetaphorContext);
  if (!context) {
    throw new Error('useSelectedMetaphor must be used within SelectedMetaphorProvider');
  }
  return context;
};