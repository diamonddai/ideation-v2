
import { useState } from 'react';
import { Upload, Table, Slider, Tag } from 'antd';
import type { UploadProps, TableColumnsType } from 'antd';
import { FileTextOutlined, BarChartOutlined, FunctionOutlined, EyeOutlined, AppstoreOutlined, DollarOutlined } from '@ant-design/icons';
import SemanticIcon from "../../assets/icons/semantic.svg";
import FunctionalIcon from "../../assets/icons/functional.svg";
import PerceptualIcon from "../../assets/icons/perceptional.svg";
import StructuralIcon from "../../assets/icons/structural.svg";
import { useSubject } from "../../context/subject";
import { useFilter } from "../../context/filter";
import { useMetaphors } from "../../context/metaphors";
import React, { useMemo } from 'react';
import { getApiUrl } from "../../lib/api";

import Papa from 'papaparse';
import { useEffect } from 'react';
import type { RcFile } from 'antd/es/upload/interface';

type Subject = { field: string; dataFact: string;dimensions?: string[]; };

type UploadCsvResp = {
  boundFields?: Subject[];
  contextDescription?: string;
  message?: string;
};

interface TableDataType {
  key: string;
  time: string;
  population: string;
}

// 模拟PanelCard组件
const PanelCard = ({ children }: { children: React.ReactNode }) => (
  <div style={{ 
    background: '#fff', 
    borderRadius: '8px', 
    padding: "0px 10px",
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
  }}>
    {children}
  </div>
);

export default function UnderstandPanel() {
  const [csvData, setCsvData] = useState<any[]>([]);
  const [columns, setColumns] = useState<any[]>([]);
  const [fileName, setFileName] = useState<string>('');
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const { subject: selectedSubject, setSubject: setSelectedSubject } = useSubject();
  const { 
    selectedTheme, 
    selectedMethod, 
    selectedStrategy,
    setSelectedTheme, 
    setSelectedMethod,
    setSelectedStrategy 
  } = useFilter();
  const { metaphors } = useMetaphors(); // 使用 context 中的数据
// 在现有 useState 声明后添加
const [apiMetaphors, setApiMetaphors] = useState<any[]>([]);
const [apiLinks, setApiLinks] = useState<any[]>([]);
const [apiThemes, setApiThemes] = useState<any[]>([]);
const [isGenerating, setIsGenerating] = useState<boolean>(false);
const [generateError, setGenerateError] = useState<string>('');
const [generateMessage, setGenerateMessage] = useState<string>('');
  // 处理文件上传并解析CSV
  const handleFileUpload = (file: RcFile) => {
    const reader = new FileReader();
    reader.onload = async () => {
      const csv = reader.result as string;

      Papa.parse(csv, {
        header: true,
        skipEmptyLines: 'greedy',
        transformHeader: (h: string) => h.replace(/^\uFEFF/, '').trim(),
        complete: async (result: any) => {
          const rows = (result.data as Record<string, string>[]) || [];
          if (!rows.length) {
            setColumns([]);
            setCsvData([]);
            setFileName(file.name);
            return;
          }
          const headersAll = Object.keys(rows[0] || {});
          const headers = Array.from(
            new Set(headersAll.map(h => (h || '').trim()).filter(h => h.length))
          );
          const cleanRows = rows
            .filter(r => Object.values(r).some(cell => cell))
            .map(r => {
              const o: Record<string, string> = {};
              headers.forEach(h => (o[h] = (r[h] ?? '').toString()));
              return o;
            });

          setColumns(headers.map(col => ({ title: col, dataIndex: col, key: col })));
          setCsvData(cleanRows);
          setFileName(file.name);

          try {
            const fd = new FormData();
            fd.append('file', file);

            // 然后在handleFileUpload函数中：
const res = await fetch(getApiUrl('/v1/module1/upload-csv'), { 
  method: 'POST', 
  body: fd 
});
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data: UploadCsvResp = await res.json();
            // 立即检查原始响应
            console.log('🔴 原始响应 boundFields:');
            console.log(JSON.stringify(data.boundFields, null, 2));

            // 特别检查每个 field 的 dimensions
            data.boundFields?.forEach((bf: any) => {
              console.log(`Field: ${bf.field}`);
              console.log(`  - dimensions 原始值:`, bf.dimensions);
              console.log(`  - typeof dimensions:`, typeof bf.dimensions);
              console.log(`  - Array.isArray:`, Array.isArray(bf.dimensions));
              if (bf.dimensions) {
                console.log(`  - dimensions.length:`, bf.dimensions.length);
                console.log(`  - dimensions[0]:`, bf.dimensions[0]);
                console.log(`  - dimensions[1]:`, bf.dimensions[1]);
              }
            });
            console.log('📥 完整响应数据:', data);
            const list = (data?.boundFields ?? []) as Subject[];
            console.log('📋 BoundFields详情:', list);
            // 检查每个boundField的dimensions
            list.forEach((bf, idx) => {
              console.log(`  - BoundField[${idx}]: field="${bf.field}", dimensions=`, bf.dimensions);
            });
            //const unique = Array.from(new Map(list.map(s => [s.field, s])).values());
            // 改为这样，保留完整的 dimensions
            const unique = list.map(item => ({
              field: item.field,
              dataFact: item.dataFact,
              dimensions: item.dimensions ? [...item.dimensions] : []
            }));
            console.log('🟡 去重后的数据:');
            unique.forEach(u => {
              console.log(`${u.field}: dimensions =`, u.dimensions);
            });

            setSubjects(unique);
          } catch (e) {
            console.error('上传到后端分析失败：', e);
            setSubjects([]);
            setSelectedSubject('');
          }
        },
        error: (err: any) => {
          console.error('CSV 解析失败：', err);
        },
      });
    };

    reader.readAsText(file, 'utf-8');
    return false;
  };
//模拟数据filteredCapsules
  // const filteredCapsules = useMemo(() => {
  //   let filtered = metaphors.capsules.filter(capsule => 
  //     capsule.field === selectedSubject
  //   );
    
  //   // 根据策略过滤 (Guided/Blinded)
  //   if (selectedStrategy) {
  //     filtered = filtered.filter(capsule => {
  //       // 转换为小写进行比较
  //       const capsuleMethod = capsule.method?.toLowerCase() || '';
  //       const strategyLower = selectedStrategy.toLowerCase();
  //       return capsuleMethod === strategyLower;
  //     });
  //   }
    
  //   // 根据主题过滤 (Nature, Artifact, Body, Life, Others)
  //   if (selectedTheme) {
  //     filtered = filtered.filter(capsule => capsule.theme === selectedTheme);
  //   }
    
  //   // 根据方法过滤 (semantic, functional, perceptual, structural)
  //   if (selectedMethod) {
  //     filtered = filtered.filter(capsule => 
  //       capsule.guidedmethod.toLowerCase() === selectedMethod
  //     );
  //   }
    
  //   return filtered;
  // }, [metaphors.capsules, selectedSubject, selectedTheme, selectedMethod, selectedStrategy]);
   
//后端数据filteredCapsules
const filteredCapsules = useMemo(() => {
  // 如果有API数据，优先使用API数据
  if (apiMetaphors.length > 0) {
    let filtered = apiMetaphors.filter(item => item.field === selectedSubject);
    
    // 根据策略过滤 (guided/blind)
    if (selectedStrategy) {
      filtered = filtered.filter(item => {
        if (selectedStrategy === 'Guided') {
          return item.method === 'guided';
        } else if (selectedStrategy === 'Blinded') {
          return item.method === 'blind';
        }
        return true;
      });
    }
    
    // 根据主题过滤
    if (selectedTheme) {
      filtered = filtered.filter(item => item.theme === selectedTheme);
    }
    
    // 根据方法过滤（基于guidedmethod字段）
    if (selectedMethod) {
      filtered = filtered.filter(item => {
        if (item.method === 'guided' && item.guidedmethod) {
          // 建立方法映射关系
          const methodMap = {
            'semantic': '语义维度',
            'functional': '功能维度', 
            'perceptual': '感知维度',
            'structural': '结构维度'
          };
          
          return item.guidedmethod === methodMap[selectedMethod];
        }
        return item.method === 'blind'; // blind模式的项目在选择方法时也显示
      });
    }
    
    return filtered;
  } else {
    // 原有的context数据过滤逻辑保持不变
    let filtered = metaphors.capsules.filter(capsule => 
      capsule.field === selectedSubject
    );
    
    if (selectedStrategy) {
      filtered = filtered.filter(capsule => {
        const capsuleMethod = capsule.method?.toLowerCase() || '';
        const strategyLower = selectedStrategy.toLowerCase();
        return capsuleMethod === strategyLower;
      });
    }
    
    if (selectedTheme) {
      filtered = filtered.filter(capsule => capsule.theme === selectedTheme);
    }
    
    if (selectedMethod) {
      filtered = filtered.filter(capsule => 
        capsule.guidedmethod?.toLowerCase() === selectedMethod
      );
    }
    
    return filtered;
  }
}, [apiMetaphors, metaphors.capsules, selectedSubject, selectedTheme, selectedMethod, selectedStrategy]);

//模拟数据methodCountes
  // const methodCounts = useMemo(() => {
  //   const counts = {
  //     causality: 0, taxonomy: 0, symbol: 0,
  //     behavior: 0, usage: 0,
  //     temporal: 0, spatial: 0,
  //     size: 0, color: 0, shape: 0
  //   };
    
  //   filteredCapsules.forEach(capsule => {
  //     if (capsule.guided2ndLevelMethod && capsule.guided2ndLevelMethod !== 'null') {
  //       counts[capsule.guided2ndLevelMethod] = (counts[capsule.guided2ndLevelMethod] || 0) + 1;
  //     }
  //   });
    
  //   return counts;
  // }, [filteredCapsules]);
  
  //真实数据methhodcounts
  const methodCounts = useMemo(() => {
    const counts = {
      causality: 0, taxonomy: 0, symbol: 0,
      behavior: 0, usage: 0,
      temporal: 0, spatial: 0,
      size: 0, color: 0, shape: 0
    };
    
    if (apiMetaphors.length > 0) {
      // 使用API数据的guided2ndLevelMethod字段进行统计
      filteredCapsules.forEach(item => {
        if (item.method === 'guided' && item.guided2ndLevelMethod) {
          // 建立映射关系（中文到英文）
          const methodMapping: { [key: string]: string } = {
            '因果关系': 'causality',
            '类属关系': 'taxonomy', 
            '象征关系': 'symbol',
            '行为': 'behavior',
            '用途': 'usage',
            '时间': 'temporal',
            '空间': 'spatial',
            '尺寸': 'size',
            '颜色': 'color',
            '形状': 'shape'
          };
          
          // 添加类型检查
          const chineseMethod = item.guided2ndLevelMethod as string;
          if (chineseMethod && methodMapping.hasOwnProperty(chineseMethod)) {
            const englishMethod = methodMapping[chineseMethod];
            if (englishMethod && counts.hasOwnProperty(englishMethod)) {
              (counts as any)[englishMethod]++;
            }
          }
        }
      });
    } else {
      // 原有的context数据统计逻辑
      filteredCapsules.forEach(capsule => {
        if (capsule.guided2ndLevelMethod && capsule.guided2ndLevelMethod !== 'null') {
          (counts as any)[capsule.guided2ndLevelMethod] = ((counts as any)[capsule.guided2ndLevelMethod] || 0) + 1;
        }
      });
    }
    
    return counts;
  }, [filteredCapsules, apiMetaphors]);
    
  const [batchGeneration, setBatchGeneration] = useState<number>(50);
  const [selectedTags, setSelectedTags] = useState<string[]>(['增长']);
  const [selectedStructures, setSelectedStructures] = useState<string[]>(['金字塔']);
  
  // 展开/收起状态管理
  const [isTopicThemeExpanded, setIsTopicThemeExpanded] = useState<boolean>(true);
  const [isStrategyExpanded, setIsStrategyExpanded] = useState<boolean>(true);
  const [isCategoryStatsExpanded, setIsCategoryStatsExpanded] = useState<boolean>(true);

  // 处理主题按钮选择
  const handleThemeSelect = (theme: string) => {
    if (selectedTheme === theme) {
      setSelectedTheme(null);
    } else {
      setSelectedTheme(theme as any);
    }
  };

  // 处理各个区域的展开/收起
  const handleTopicThemeToggle = () => {
    setIsTopicThemeExpanded(prev => !prev);
  };

  const handleStrategyToggle = () => {
    setIsStrategyExpanded(prev => !prev);
  };

  const handleCategoryStatsToggle = () => {
    setIsCategoryStatsExpanded(prev => !prev);
  };

  // 处理策略选择 (Guided/Blinded)
  const handleStrategySelect = (strategy: string) => {
    if (selectedStrategy === strategy) {
      setSelectedStrategy('');
    } else {
      setSelectedStrategy(strategy as 'Guided' | 'Blinded');
    }
  };

  // 处理标签选择
  const handleTagChange = (tag: string, checked: boolean) => {
    const nextSelectedTags = checked 
      ? [...selectedTags, tag]
      : selectedTags.filter(t => t !== tag);
    setSelectedTags(nextSelectedTags);
  };

  // 处理结构选择
  const handleStructureChange = (structure: string, checked: boolean) => {
    const nextSelectedStructures = checked 
      ? [...selectedStructures, structure]
      : selectedStructures.filter(s => s !== structure);
    setSelectedStructures(nextSelectedStructures);
  };

  //模拟数据handleGenerateMetaphor
  // const handleGenerateMetaphor = () => {
  //   console.log('生成喻体', { 
  //     selectedTheme, 
  //     selectedMethod,
  //     selectedStrategy,
  //     batchGeneration, 
  //     selectedTags, 
  //     selectedStructures 
  //   });
    
  //   // 如果当前没有选中的 subject，先设置默认值
  //   if (!selectedSubject) {
  //     setSelectedSubject("immigrant");
  //   }
    
  //   // 触发数据更新（这里先使用默认数据，后续可以调用 API）
  //   // setMetaphors(metaphors); // 确保数据被刷新
  //   console.log('当前选中的主题:', selectedSubject);
  //   console.log('当前过滤后的数据:', filteredCapsules);
    
  //   // 可选：显示成功消息
  //   if (filteredCapsules.length > 0) {
  //     console.log(`生成了 ${filteredCapsules.length} 个喻体`);
  //   } else {
  //     console.log('没有找到匹配的数据，请检查筛选条件');
  //   }
  // };

  //后端handleGenerateMetaphor
  const handleGenerateMetaphor = async () => {
    if (!selectedSubject) {
      setGenerateError('请先选择一个Subject');
      return;
    }
  
    const currentSubject = subjects.find(s => s.field === selectedSubject);
    console.log('📌 Current subject with dimensions:', currentSubject);

    
    if (!currentSubject) {
      setGenerateError('找不到对应的Subject数据');
      return;
    }
  
    setIsGenerating(true);
    setGenerateError('');
    setGenerateMessage('');
    
    try {
      // 根据selectedStrategy调整blindRatio
      let blindRatio = 0.5; // 默认各占一半
      if (selectedStrategy === 'Guided') {
        blindRatio = 0.1; // 主要使用guided
      } else if (selectedStrategy === 'Blinded') {
        blindRatio = 0.9; // 主要使用blind
      }
  
      const requestData = {
        boundField: {
          field: currentSubject.field,
          dataFact: currentSubject.dataFact
        },
        blindRatio: blindRatio,
        totalLimit: batchGeneration
      };
  
      console.log('调用API，请求数据:', requestData);
  
      const response = await fetch(getApiUrl('/v1/module2/generate-metaphors'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });
  
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
  
      const data = await response.json();
      console.log('API返回数据:', data);
  
      // 存储API返回的完整数据
      setApiMetaphors(data.variations || []);
      setApiLinks(data.links || []);
      setApiThemes(data.themes || []);
      setGenerateMessage(data.message || '');
      
      // 在这里添加事件触发代码
    window.dispatchEvent(new CustomEvent('metaphorDataUpdated', {
      detail: {
        variations: data.variations || [],
        links: data.links || [],
        themes: data.themes || []
      }
    }));
      if (data.variations && data.variations.length > 0) {
        console.log(`成功生成 ${data.variations.length} 个隐喻`);
      } else {
        setGenerateError('未生成任何隐喻，请检查输入数据');
      }
      
    } catch (error) {
      console.error('生成隐喻失败:', error);
      setGenerateError(error instanceof Error ? error.message : '生成隐喻时发生未知错误');
      setApiMetaphors([]);
      setApiLinks([]);
      setApiThemes([]);
    } finally {
      setIsGenerating(false);
    }
  };

  // 主题选择color映射
  const topicThemeColors = {
    'Nature': '#0C91BE',
    'Artifact': '#87C11A', 
    'Body': '#C183DC',
    'Life': '#F19A64',
    'Others': '#E1C769'
  };

  const strategyButtons = [
    { name: 'semantic',   label: 'Semantic',   icon: SemanticIcon },
    { name: 'functional',   label: 'Functional', icon: FunctionalIcon },
    { name: 'perceptual', label: 'Perceptual', icon: PerceptualIcon },
    { name: 'structural',  label: 'Structural', icon: StructuralIcon },
  ];
  
  const labels = [
    { label: 'causality', icon: SemanticIcon },
    { label: 'taxonomy', icon: SemanticIcon },
    { label: 'symbol', icon: SemanticIcon },
    { label: 'behavior', icon: FunctionalIcon },
    { label: 'usage', icon: FunctionalIcon },
    { label: 'temporal', icon: StructuralIcon },
    { label: 'spatial', icon: StructuralIcon },
    { label: 'size', icon: PerceptualIcon },
    { label: 'color', icon: PerceptualIcon },
    { label: 'shape', icon: PerceptualIcon },
  ] as const;

  return (
    <PanelCard >
      <div style={{ 
        padding: '0px', 
        height: "750px",  // 固定高度
        overflowY: "auto",  // 添加垂直滚动
        overflowX: "hidden",  // 隐藏水平滚动
        fontFamily: '"Arial Black", "Helvetica Neue", Arial, sans-serif',
        fontWeight: 'bold',
        position:"relative"
      }}>
        
        {/* 1. 选择文件区域 */}
        <div style={{ height:"45px",marginBottom: '15px',marginTop:"15px",display: "flex", flexDirection: "column", alignItems: "center" }}>
          <Upload beforeUpload={handleFileUpload} showUploadList={false} accept=".csv">
            <div style={{ 
              width: '220px', 
              height: '45px',
              border: '1px dashed rgba(35, 75, 103, 0.3)',
              borderRadius: '5px', 
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              background: 'rgba(217, 221, 230, 0.3)',
              cursor: 'pointer',
              transition: 'all 0.3s ease'
            }}>
              <FileTextOutlined style={{ fontSize: '16px', color: '#8c8c8c', marginBottom: '3px' }} />
              <div style={{ color: '#8c8c8c', fontSize: '11px' }}>Select File</div>
            </div>
          </Upload>
        </div>

        {/* 分割线 */}
        <div style={{ 
          display: 'flex',
          justifyContent: 'center',
          // margin: '-2px -24px 12px -24px'
        }}>
          <div style={{ 
            height: '0.4px', 
            background: '#B2A9A9', 
            width: '100%',
          }}></div>
        </div>

        {/* 2. 数据表格 */}
        <div style={{height:"120px", marginBottom: '5px',marginTop:'5px' }}>
          <h4 style={{ marginBottom: '8px', fontSize: '11px', fontWeight: 700, textAlign: 'left' }}>
            {fileName}
          </h4>
          <div
            style={{
              height: "100px",
              borderRadius: 5,
              border: '1px solid #eee',
              overflow: 'auto',
              padding: 2,
              background: '#fff',
              position: 'relative',
            }}
          >
            {csvData.length === 0 ? (
              <div
                style={{
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 10,
                  color: '#999',
                  letterSpacing: 0,
                }}
              >
                The data is empty
              </div>
            ) : (
              <Table
                dataSource={csvData}
                columns={columns.map(col => ({ ...col, ellipsis: true }))}
                size="small"
                pagination={false}
                className="custom-table"
                scroll={{ y: 100, x: 'max-content' }}
                rowKey={(_, idx) => String(idx)}
              />
            )}
          </div>
          
          {/* CSS 样式 */}
          <style>
            {`
              .custom-table .ant-table-thead > tr > th {
                height: 20px !important;
                padding: 2px 6px !important;
                font-size: 7px !important;
                font-weight: 700 !important;
                line-height: 100% !important;
                letter-spacing: 0% !important;
              }
              .custom-table .ant-table-tbody > tr > td {
                height: 20px !important;
                padding: 2px 6px !important;
                font-size: 7px !important;
                font-weight: 700 !important;
                line-height: 100% !important;
                letter-spacing: 0% !important;
              }
              .ant-table-sticky-holder{ display:none !important; }
              .batch-slider {
                background: rgba(231, 232, 233, 0.5) !important;
                border-radius: 6px !important;
                padding: 7px 9px 9px 9px !important;
                margin-bottom: 12px !important;
                box-sizing: border-box !important;
              }
              .batch-slider .ant-slider {
                padding: 2px 0 !important;
              }
              .batch-slider .ant-slider-rail {
                background-color: #D1D1D1 !important;
                height: 3px !important;
                border-radius: 1.5px !important;
              }
              .batch-slider .ant-slider-track {
                background-color: #6B767E !important;
                height: 3px !important;
                border-radius: 1.5px !important;
              }
              .batch-slider .ant-slider-handle {
                border: 1px solid #CCCCCC !important;
                background-color: #FFFFFF !important;
                width: 12px !important;
                height: 12px !important;
                margin-top: -6px !important;
                border-radius: 50% !important;
                box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
                cursor: pointer !important;
                outline: none !important;
                opacity: 1 !important;
              }
              .batch-slider .ant-slider-handle::before,
              .batch-slider .ant-slider-handle::after {
                display: none !important;
                content: none !important;
              }
              .batch-slider .ant-slider-handle:hover,
              .batch-slider .ant-slider-handle:focus,
              .batch-slider .ant-slider-handle:active,
              .batch-slider .ant-slider-handle.ant-slider-handle-dragging {
                border: 1px solid #CCCCCC !important;
                background-color: #FFFFFF !important;
                box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
                transform: none !important;
                outline: none !important;
                opacity: 1 !important;
              }
              .batch-slider .ant-slider:hover .ant-slider-handle:not(.ant-tooltip-open) {
                border: 1px solid #CCCCCC !important;
                transform: none !important;
              }
              .batch-slider .ant-slider-handle:focus-visible {
                outline: none !important;
                border: 1px solid #CCCCCC !important;
                box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
              }
              .batch-slider .ant-tooltip,
              .batch-slider .ant-tooltip-content,
              .batch-slider .ant-tooltip-arrow {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                pointer-events: none !important;
              }
              .batch-slider * .ant-tooltip {
                display: none !important;
              }
              .batch-numbers {
                color: #495058 !important;
                font-weight: 600 !important;
                font-size: 9px !important;
                opacity: 1 !important;
              }
            `}
          </style>
        </div>
        
        {/* 分割线 */}
        <div style={{ 
          display: 'flex',
          justifyContent: 'center',
          margin: '-6px -24px 12px -24px'
        }}>
          <div style={{ 
            height: '0.4px', 
            background: '#B2A9A9', 
            width: '100%',
          }}></div>
        </div>

        {/* 3. 分析数据控制面板 */}
        <div style={{ height:"240px",marginBottom: '10px' }}>
          <h4 style={{ marginBottom: '6px', fontSize: '11px', fontWeight: 700, textAlign: 'left' }}>
            Analyze Data
          </h4>
          
          {/* 主题选择按钮组 */}
          <div style={{ marginBottom: '6px' }}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '9px', color: '#666', textAlign: 'left' }}>
              Subject：
            </label>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'nowrap',overflowX: 'auto',paddingBottom: '2px' }}>
              {subjects.map((subject, idx) => (
                <button
                  key={`${subject.field}-${idx}`}
                  onClick={() => {
                    // 传递 subject 和对应的 dimensions
                    setSelectedSubject(subject.field, subject.dimensions);
                    console.log('✅ 选择 Subject:', subject.field, 'Dimensions:', subject.dimensions);
                  }}
                  style={{
                    padding: '4px 12px',
                    border: selectedSubject === subject.field ? 'none' : '1px solid #d9d9d9',
                    background: selectedSubject === subject.field ? '#495058' : '#fff',
                    color: selectedSubject === subject.field ? '#fff' : '#333',
                    fontSize: '8px',
                    cursor: 'pointer',
                    fontWeight: 500,
                    transition: 'all 0.3s ease',
                    minWidth: '40px',
                    height: '22px', 
                    borderRadius: '11px',
                    
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flex: '0 0 auto', 
                    whiteSpace: 'nowrap',
                  }}
                >
                  {subject.field}
                </button>
              ))}
              <button
                style={{
                  padding: '4px 10px',
                  border: '1px solid #d9d9d9',
                  background: '#fff',
                  color: '#333',
                  fontSize: '9px',
                  cursor: 'pointer',
                  fontWeight: 500,
                  minWidth: '40px',
                  height: '22px', 
                  borderRadius: '11px',
                  
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'all 0.3s ease'
                }}
              >
                +
              </button>
            </div>
          </div>

          {/* 特征标签 */}
          <div style={{ marginBottom: '8px' }}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '9px', color: '#666', textAlign: 'left' }}>
              Feature：
            </label>
            
            <div
              style={{
                minHeight: "30px",
                border: '1px dashed #e5e5e5',
                borderRadius: 5,
                padding: '3px 3px',
                fontSize: 9,
                color: '#333',
                background: '#fff',
                whiteSpace: 'pre-wrap',
              }}
            >
              {selectedSubject
                ? (subjects.find(s => s.field === selectedSubject)?.dataFact ?? '')
                : ''}
            </div>
          </div>

          {/* 批量生成滑块 */}
          <div className="batch-slider" style={{ 
            width: '100%',
            background: 'rgba(231, 232, 233, 0.5)',
            borderRadius: '6px',
            padding: '7px 9px 9px 9px',
            marginBottom: '12px',
            boxSizing: 'border-box'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px' }}>
              <label style={{ fontSize: '9px', color: '#666' }}>
                Batch Generate：
              </label>
              <span style={{ 
                background: '#495058', 
                color: '#fff', 
                padding: '2px 8px', 
                borderRadius: '10px', 
                fontSize: '10px',
                fontWeight: 600,
                minWidth: '30px',
                textAlign: 'center'
              }}>
                {batchGeneration}
              </span>
            </div>
            
            <div style={{ position: 'relative', width: '100%', margin: '0 auto' }}>
              <Slider 
                value={batchGeneration} 
                onChange={setBatchGeneration}
                style={{ width: '100%', margin: '0' }} 
                min={0}
                max={60}
                tooltip={{ open: false, formatter: null }}
              />
              
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                marginTop: '0px'
              }}>
                <span className="batch-numbers" style={{ 
                  color: '#495058',
                  fontSize: '6px',
                  fontWeight: 600,
                  opacity: 1
                }}>0</span>
                <span className="batch-numbers" style={{ 
                  color: '#495058',
                  fontSize: '6px',
                  fontWeight: 600,
                  opacity: 1
                }}>60</span>
              </div>
            </div>
          </div>

          {/* 生成按钮 */}
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <button 
              onClick={handleGenerateMetaphor}
              disabled={isGenerating || !selectedSubject}
              style={{ 
                background: '#495058', 
                borderColor: '#495058',
                border: 'none',
                fontSize: '9px',
                width: '120px',
                height: '30px',
                borderRadius: '5px',
                color: '#fff',
                cursor: (isGenerating || !selectedSubject) ? 'not-allowed' : 'pointer',
                fontWeight: 600,
                transition: 'all 0.3s ease',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                opacity: !selectedSubject ? 0.6 : 1
              }}
            >
              Generate Metaphor
            </button>
          </div>
        </div>

        {/* 分割线 */}
        <div style={{ 
          display: 'flex',
          justifyContent: 'center',
          margin: '12px -24px 12px -24px'
        }}>
          <div style={{ 
            height: '0.4px', 
            background: '#B2A9A9', 
            width: '100%',
          }}></div>
        </div>

        {/* 4. 主题选择 */}
        <div style={{ height:"50px" }}>
          <div 
            onClick={handleTopicThemeToggle}
            style={{ 
              display: 'flex', 
              alignItems: 'center',
              marginBottom: '8px',
              cursor: 'pointer',
              gap: '4px'
            }}
          >
            <h4 style={{ 
              fontSize: '11px', 
              fontWeight: 700, 
              margin: 0
            }}>
              Theme Selection
            </h4>
            <span style={{ 
              fontSize: '6px',
              color: '#B9BABF',
              transform: isTopicThemeExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.3s ease'
            }}>▲</span>
          </div>
          
          {isTopicThemeExpanded && (
            <div style={{ 
              display: 'flex', 
              gap: '6px', 
              flexWrap: 'nowrap', 
              width: '100%',
              animation: 'fadeIn 0.3s ease-in-out',
              overflowX: 'auto', 
            }}>
              {/* {Object.entries(topicThemeColors).map(([theme, color]) => ( */}
              {/* 只有当有喻体数据时才显示主题按钮 */}
   
    {/* {filteredCapsules.length > 0 ? (
      // 从filteredCapsules中提取唯一的主题列表
      Array.from(new Set(metaphors.capsules
        .filter(c => c.field === selectedSubject)
        .map(c => c.theme)))
        .map(theme => (
                <button
                  key={theme}
                  onClick={() => handleThemeSelect(theme)}
                  style={{
                    background: selectedTheme === theme ? topicThemeColors[theme] || '#ccc' : '#fff',
                    color: selectedTheme === theme ? '#fff' : '#333',
                    border: selectedTheme === theme ? 'none' : `1px solid ${topicThemeColors[theme] || '#ccc'}`,
                    borderRadius: '5px',
                    padding: '3px 5px',
                    fontSize: '7px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    flex: '0 0 auto',
                    whiteSpace: 'nowrap',
                    height: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.3s ease'
                  }}
                >
                  {theme}
                </button>

              ))
            ):(
              <div style={{fontSize:'9px',color:'#999',padding:'4px 0'}}>
                
                </div>

            )} */}

            {/* 主题选择区域 - 现在完全支持API数据 */}
{filteredCapsules.length > 0 ? (
  apiMetaphors.length > 0 ? (
    // API数据：使用返回的themes数据和实际的主题分布
    Array.from(new Set(apiMetaphors
      .filter(item => item.field === selectedSubject)
      .map(item => item.theme)))
      .map(theme => {
        // 从apiThemes中获取对应的颜色
        const themeInfo = apiThemes.find(t => t.name === theme);
        const color = themeInfo?.color || '#ccc';
        
        return (
          <button
            key={theme}
            onClick={() => handleThemeSelect(theme)}
            style={{
              background: selectedTheme === theme ? color : '#fff',
              color: selectedTheme === theme ? '#fff' : '#333',
              border: selectedTheme === theme ? 'none' : `1px solid ${color}`,
              borderRadius: '5px',
              padding: '3px 5px',
              fontSize: '7px',
              fontWeight: 600,
              cursor: 'pointer',
              flex: '0 0 auto',
              whiteSpace: 'nowrap',
              height: '24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.3s ease'
            }}
          >
            {theme}
          </button>
        );
      })
  ) : (
    // 原有的context数据逻辑
    Array.from(new Set(metaphors.capsules
      .filter(c => c.field === selectedSubject)
      .map(c => c.theme)))
      .map(theme => (
        <button
          key={theme}
          onClick={() => handleThemeSelect(theme)}
          style={{
            background: selectedTheme === theme ? topicThemeColors[theme] || '#ccc' : '#fff',
            color: selectedTheme === theme ? '#fff' : '#333',
            border: selectedTheme === theme ? 'none' : `1px solid ${topicThemeColors[theme] || '#ccc'}`,
            borderRadius: '5px',
            padding: '3px 5px',
            fontSize: '7px',
            fontWeight: 600,
            cursor: 'pointer',
            flex: '0 0 auto',
            whiteSpace: 'nowrap',
            height: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.3s ease'
          }}
        >
          {theme}
        </button>
      ))
  )
) : (
  <div style={{fontSize:'9px',color:'#999',padding:'0 0'}}>
    {apiMetaphors.length === 0 ? 'Generate first' : '没有匹配的数据'}
  </div>
)}
            </div>
          )}
        </div>

        {/* 5. 发散策略 */}
        <div style={{ height:"75px",marginBottom: '16px' }}>
          <div 
            onClick={handleStrategyToggle}
            style={{ 
              display: 'flex', 
              alignItems: 'center',
              marginBottom: '8px',
              cursor: 'pointer',
              gap: '4px'
            }}
          >
            <h4 style={{ 
              fontSize: '11px', 
              fontWeight: 700, 
              margin: 0
            }}>
              Divergence Strategy
            </h4>
            <span style={{ 
              fontSize: '6px',
              color: '#B9BABF',
              transform: isStrategyExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.3s ease'
            }}>▲</span>
          </div>
          
          {isStrategyExpanded && (
            <div style={{ animation: 'fadeIn 0.3s ease-in-out' }}>
              <div style={{ display: 'flex', gap: '14px', marginBottom: '12px' }}>
                <button
                  onClick={() => handleStrategySelect('Guided')}
                  style={{
                    background: selectedStrategy === 'Guided' ? '#6B767E' : '#495058',
                    color: '#fff',
                    border: '1px solid #495058',
                    borderRadius: '4px',
                    padding: '3px 5px',
                    fontSize: '9px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    width: '100px',
                    height: '22px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.3s ease',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                  }}
                >
                  Guided
                  <span style={{ 
                    marginLeft: '6px',
                    fontSize: '5px',
                    color: '#B9BABF'
                  }}>▼</span>
                </button>

                <button
                  onClick={() => handleStrategySelect('Blinded')}
                  style={{
                    background: selectedStrategy === 'Blinded'  
                      ? 'repeating-linear-gradient(-45deg, #6B767E 0px, #6B767E 3px, #495058 3px, #495058 6px)'
                      : 'repeating-linear-gradient(-45deg, #495058 0px, #495058 3px, #6B767E 3px, #6B767E 6px)',
                    color: '#fff',
                    border: '1px solid #495058',
                    borderRadius: '4px',
                    padding: '1px 5px',
                    fontSize: '9px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    width: '100px',
                    height: '22px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.3s ease',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                  }}
                >
                  Blinded
                </button>
              </div>

              {/* 策略按钮组 */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', width: '100%' }}>
                  {strategyButtons.map((button) => (
                    <button
                      key={button.name}
                      onClick={() => {
                        const methodName = button.name.toLowerCase();
                        if (selectedMethod === methodName) {
                          setSelectedMethod(null);
                        } else {
                          setSelectedMethod(methodName as any);
                        }
                      }}
                      style={{
                        background: selectedMethod === button.name.toLowerCase() ? '#6B767E' : '#495058',
                        color: '#fff',
                        border: '1px solid #BCBCBC',
                        borderRadius: '4px',
                        padding: '4px 8px',
                        fontSize: '7px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        minWidth: '50px',
                        height: '22px',
                        display: 'flex',
                        flexDirection: 'row',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'all 0.3s ease',
                        boxShadow: '1px 3px 3px 0px rgba(0,0,0,0.25)',
                        gap: '4px'
                      }}
                    >
                      <img 
                        src={button.icon} 
                        alt={button.name}
                        style={{ 
                          width: '8px', 
                          height: '8px'
                        }}
                        onError={(e) => {
                          console.log('图标加载失败:', button.icon);
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                      <span>{button.name}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 6. 类别分布统计 */}
        <div style={{ marginBottom: '10px' }}>
          <div 
            onClick={handleCategoryStatsToggle}
            style={{ 
              display: 'flex', 
              alignItems: 'center',
              marginBottom: '5px',
              cursor: 'pointer',
              gap: '4px'
            }}
          >
            <h4 style={{ 
              fontSize: '11px', 
              fontWeight: 700, 
              margin: 0
            }}>
              Distribution Statistics
            </h4>
            <span style={{ 
              fontSize: '6px',
              color: '#B9BABF',
              transform: isCategoryStatsExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.3s ease'
            }}>▲</span>
          </div>
          
          {isCategoryStatsExpanded && (
            <div style={{ position: 'relative', animation: 'fadeIn 0.3s ease-in-out', height: '85px',paddingTop:'15px' }}>
              <div style={{ overflowX: 'auto',  height: '100%' }}>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: '12px', width: 'max-content', height: '100%' }}>
                  <div style={{
                    position: 'absolute',
                    bottom: '20px',
                    left: 0,
                    right: 0,
                    height: '0.5px',
                    background: '#000',
                    zIndex: 1
                  }} />

                  {(() => {
                    const items = [
                      { label: 'causality', icon: SemanticIcon,   value: methodCounts.causality },
                      { label: 'taxonomy', icon: SemanticIcon,   value: methodCounts.taxonomy },
                      { label: 'symbol', icon: SemanticIcon,   value: methodCounts.symbol },
                      { label: 'behavior', icon: FunctionalIcon, value: methodCounts.behavior },
                      { label: 'usage', icon: FunctionalIcon, value: methodCounts.usage },
                      { label: 'temporal', icon: StructuralIcon, value: methodCounts.temporal },
                      { label: 'spatial', icon: StructuralIcon, value: methodCounts.spatial },
                      { label: 'size', icon: PerceptualIcon, value: methodCounts.size },
                      { label: 'color', icon: PerceptualIcon, value: methodCounts.color },
                      { label: 'shape', icon: PerceptualIcon, value: methodCounts.shape },
                    ] as const;

                    const max = Math.max(...items.map(item => item.value), 1);
                    return items.map((it, index) => {
                      const maxBarHeight = 35;  // 增加最大高度，从 24px 改为 35px
                      const barHeight = (it.value / max) * maxBarHeight;
                      return (
                        <div 
                          key={index} 
                          style={{ 
                            display: 'flex', 
                            flexDirection: 'column', 
                            alignItems: 'center',
                            position: 'relative',
                            height: '100%',
                            minWidth: '36px'
                          }}
                        >
                          <span style={{ 
                            fontSize: '8px', 
                            color: '#333', 
                            fontWeight: 600,
                            position: 'absolute',
                            top: `${30 - barHeight + 6}px`
                          }}>
                            {it.value}
                          </span>

                          <div 
                            style={{ 
                              width: '20px', 
                              height: `${barHeight}px`, 
                              background: '#D9D9D9',
                              transition: 'all 0.3s ease',
                              position: 'absolute',
                              bottom: '20px'
                            }} 
                          />

                          <div style={{ 
                            position: 'absolute',
                            bottom: '6px',
                            left:'50%',
                            transform: 'translateX(-50%)',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '1px',
                            whiteSpace: 'nowrap',
                          }}>
                            <img
                              src={it.icon}
                              alt={it.label}
                              style={{
                                width: 8,
                                height: 8,
                                filter: 'invert(0.6)',
                              }}
                            />
                            <span style={{ 
                              fontSize: '7px', 
                              color: '#666',
                              display: 'block'
                            }}>
                              {it.label}
                            </span>
                          </div>
                        </div>
                      );
                    });
                  })()}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 添加淡入动画 */}
        <style>
          {`
            @keyframes fadeIn {
              from {
                opacity: 0;
                transform: translateY(-8px);
              }
              to {
                opacity: 1;
                transform: translateY(0);
              }
            }
          `}
        </style>
      </div>
    </PanelCard>
  );
}