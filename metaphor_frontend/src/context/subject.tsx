// src/app/subject.tsx
import React, { createContext, useContext, useState } from "react";

type SubjectCtx = {
  subject: string;
  dimensions: string[];  // dimensions 字段
  setSubject: (s: string, dims?: string[]) => void;  // 修改：接受 dimensions 参数
};

const SubjectContext = createContext<SubjectCtx | undefined>(undefined);

export function SubjectProvider({ children }: { children: React.ReactNode }) {
  const [subject, setSubjectState] = useState<string>("");
  const [dimensions, setDimensions] = useState<string[]>([]);  // 添加 dimensions state
  
  // 修改 setSubject 函数，同时更新 subject 和 dimensions
  const setSubject = (s: string, dims?: string[]) => {
    setSubjectState(s);
    setDimensions(dims || []);
    console.log('📌 Subject Context 更新:', s, 'Dimensions:', dims);
  };
  
  return (
    <SubjectContext.Provider value={{ subject, dimensions, setSubject }}>
      {children}
    </SubjectContext.Provider>
  );
}

export function useSubject() {
  const ctx = useContext(SubjectContext);
  if (!ctx) throw new Error("useSubject must be used inside <SubjectProvider>");
  return ctx;
}