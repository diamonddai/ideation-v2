import React, { useEffect, useMemo, useRef, useState } from "react";
import { Slider } from "antd";
import PanelCard from "../../components/PanelCard";
import { forceSimulation, forceManyBody, forceCollide, forceLink } from "d3-force";
import type { Simulation, SimulationNodeDatum, SimulationLinkDatum } from "d3-force";
import "../../App.css";
import { useSubject } from "../../context/subject";
import { useFilter } from "../../context/filter";
import { useMetaphors } from "../../context/metaphors";
import { useSelectedMetaphor } from "../../context/selectedMetaphor";
import type{ Theme, GuidedMethod } from "../../context/metaphors";
// 导入图标
import SemanticIcon from "../../assets/icons/semantic.svg?react";
import FunctionalIcon from "../../assets/icons/functional.svg?react";
import PerceptualIcon from "../../assets/icons/perceptional.svg?react";
import StructuralIcon from "../../assets/icons/structural.svg?react";

type Kind = "semantic" | "functional" | "perceptual" | "structural";
type Category = "Nature" | "Artifact" | "Body" | "Life" | "Others";
type LinkDatumTyped = SimulationLinkDatum<NodeDatum> & { distance: number };

type Capsule = {
  id: string;
  label: string;
  category: Category;
  kind: Kind;
  rNorm: number;
  thumb: string;
  method: string; // 添加 method 字段，用于区分 Guided/Blinded
};

type NodeDatum = SimulationNodeDatum & {
  id: string;
  label: string;
  kind: Kind;
  cat: Category;
  rTarget: number;
  theta: number;
  x?: number; y?: number;
  w: number;
  h: number;
  thumb: string;
  collideR: number;
  method: string; // 添加 method 字段，用于在渲染时区分 Guided/Blinded
};

type Link = {
  source: string;
  target: string;
  distance: number;
};

// 在文件顶部添加API数据类型
type ApiVariation = {
  id: string;
  field: string;
  keyword: string;
  dataFact: string;
  theme: string;
  method: string;
  guidedmethod: string | null;
  guided2ndLevelMethod: string | null;
  rNorm: number;
  thumb: string;
};

type ApiLink = {
  source: string;
  target: string;
  distance: number;
};

type ApiTheme = {
  name: string;
  color: string;
};
// 画布与视觉参数
const VW = 1000;
const VH = 800;
const CX = VW / 2;
const CY = VH / 2;

const ARC_STROKE = 8;
const GAP_DEG = 6;
const LABEL_OUTSET = 15;
const SAFE_PAD = 10;
const INNER_GAP = 70;

const ICON_BOX = 14;
const PILL_H = 22;
const TEXT_BASE_PAD = 16;
const CHAR_W = 7.2;
const THUMB = 44;
const PILL_GAP = 6;
const CENTER_R = 40;

const normDeg = (d: number) => ((d % 360) + 360) % 360;
const toRad = (d: number) => (d * Math.PI) / 180;

const polarToXY = (cx: number, cy: number, r: number, deg: number) => {
  const t = toRad(deg);
  return { x: cx + r * Math.cos(t), y: cy + r * Math.sin(t) };
};

function arcPath(cx: number, cy: number, r: number, startDeg: number, endDeg: number) {
  let s = normDeg(startDeg);
  let e = normDeg(endDeg);
  let sweep = (e - s + 360) % 360;
  if (sweep === 0) sweep = 360;
  const largeArc = sweep > 180 ? 1 : 0;
  const p1 = polarToXY(cx, cy, r, s);
  const p2 = polarToXY(cx, cy, r, s + sweep);
  return `M ${p1.x} ${p1.y} A ${r} ${r} 0 ${largeArc} 1 ${p2.x} ${p2.y}`;
}

function lighten(hex: string, weight = 0.82) {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  const mix = (c: number) => Math.round(c * (1 - weight) + 255 * weight);
  const to2 = (n: number) => n.toString(16).padStart(2, "0");
  return `#${to2(mix(r))}${to2(mix(g))}${to2(mix(b))}`;
}

function darken(hex: string, weight = 0.22) {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  const mix = (c: number) => Math.round(c * (1 - weight));
  const to2 = (n: number) => n.toString(16).padStart(2, "0");
  return `#${to2(mix(r))}${to2(mix(g))}${to2(mix(b))}`;
}

function inRangeDeg(d: number, a: number, b: number) {
  d = normDeg(d); a = normDeg(a); b = normDeg(b);
  if (a <= b) return d >= a && d <= b;
  return d >= a || d <= b;
}

// 扇区定义
type Sector = {
  key: Category;
  color: string;
  startDeg: number;
  endDeg: number;
  midDeg: number;
};

const sectorColors: Omit<Sector, "startDeg" | "endDeg" | "midDeg">[] = [
  { key: "Nature",     color: "#0C91BE" },
  { key: "Artifact", color: "#87C11A" },
  { key: "Body",   color: "#C183DC" },
  { key: "Life",    color: "#F19A64" },
  { key: "Others",    color: "#E1C769" },
];

function buildSectors(): Sector[] {
  const wedgeDeg = (360 - sectorColors.length * GAP_DEG) / sectorColors.length;
  return sectorColors.map((s, i) => {
    const start = -90 - wedgeDeg / 2 + i * (wedgeDeg + GAP_DEG);
    const end = start + wedgeDeg;
    const sweep = (normDeg(end) - normDeg(start) + 360) % 360 || 360;
    const mid = normDeg(start + sweep / 2);
    return { ...s, startDeg: start, endDeg: end, midDeg: mid };
  });
}

function sectorByCategory(sectors: Sector[], cat: Category) {
  return sectors.find((s) => s.key === cat)!;
}

const R = Math.min(VW, VH) / 2 - (ARC_STROKE / 2 + LABEL_OUTSET + SAFE_PAD);
const INNER_MARGIN = 40;
const R_INNER = CENTER_R + INNER_MARGIN + THUMB / 2;
const STACK_DOWN = THUMB / 2 + PILL_GAP + PILL_H;
const R_OUTER = R - ARC_STROKE / 2 - 6 - STACK_DOWN;

const rFromNorm = (t: number) =>
  R_INNER + Math.max(0, R_OUTER - R_INNER) * Math.min(1, Math.max(0, t));

const pillTextW = (label: string) => Math.max(44, TEXT_BASE_PAD + Math.round(label.length * CHAR_W));
const pillTotalW = (label: string) => pillTextW(label) + ICON_BOX + 6;

// 图标映射
const ICONS: Record<Kind, React.FC<React.SVGProps<SVGSVGElement>> | null> = {
  semantic: SemanticIcon,
  functional: FunctionalIcon,
  perceptual: PerceptualIcon,
  structural: StructuralIcon,
};


const calculateRadiusRange = (nodeCount: number) => {
  // 基础半径
  const baseRInner = CENTER_R + INNER_MARGIN + THUMB / 2;
  const baseROuter = R - ARC_STROKE / 2 - 6 - STACK_DOWN;
  
  // 根据节点数量动态调整
  const densityFactor = Math.min(2.0, Math.sqrt(nodeCount / 15)); // 15个节点为基准
  const expandedROuter = baseROuter * densityFactor;
  
  return {
    rInner: baseRInner,
    rOuter: Math.min(expandedROuter, R - 20) // 确保不超过画布边界
  };
};
// Force 函数
function forceMinRadius(nodes: NodeDatum[], minR: number, strength = 1.0) {
  return () => {
    for (const n of nodes) {
      const dx = (n.x ?? CX) - CX;
      const dy = (n.y ?? CY) - CY;
      const r = Math.hypot(dx, dy) || 1;
      if (r < minR) {
        const k = (minR - r) * strength * 0.003;
        (n.vx as number) = ((n.vx as number) || 0) + (dx / r) * k;
        (n.vy as number) = ((n.vy as number) || 0) + (dy / r) * k;
      }
    }
  };
}

function forceAngularBounds(nodes: NodeDatum[], startDeg: number, endDeg: number, strength = 0.2) {
  return () => {
    for (const n of nodes) {
      const dx = (n.x ?? CX) - CX;
      const dy = (n.y ?? CY) - CY;
      let theta = normDeg((Math.atan2(dy, dx) * 180) / Math.PI);
      let r = Math.hypot(dx, dy) || n.rTarget;

      if (!inRangeDeg(theta, startDeg, endDeg)) {
        const dToStart = Math.min(Math.abs(theta - startDeg), 360 - Math.abs(theta - startDeg));
        const dToEnd = Math.min(Math.abs(theta - endDeg), 360 - Math.abs(theta - endDeg));
        theta = dToStart < dToEnd ? normDeg(startDeg) : normDeg(endDeg);
      }

      const target = polarToXY(CX, CY, r, theta);
      (n.vx as number) = ((n.vx as number) || 0) + (target.x - (n.x ?? target.x)) * strength * 0.001;
      (n.vy as number) = ((n.vy as number) || 0) + (target.y - (n.y ?? target.y)) * strength * 0.001;
    }
  };
}

function forceRadialTarget(nodes: NodeDatum[], strength = 0.3) {
  return () => {
    for (const n of nodes) {
      const x = (n.x ?? CX) - CX;
      const y = (n.y ?? CY) - CY;
      const r = Math.hypot(x, y) || 1;
      const t = n.rTarget;
      const k = (t - r) * strength * 0.002;
      (n.vx as number) = ((n.vx as number) || 0) + (x / r) * k;
      (n.vy as number) = ((n.vy as number) || 0) + (y / r) * k;
    }
  };
}
// 更新映射函数以处理API数据
function mapApiThemeToCategory(theme: string): Category {
  const mapping: Record<string, Category> = {
    "Nature": "Nature",
    "Artifact": "Artifact", 
    "Body": "Body",
    "Life": "Life",
    "Others": "Others"
  };
  return mapping[theme] || "Others";
}

function mapApiGuidedMethodToKind(guidedmethod: string | null): Kind {
  if (!guidedmethod) return "semantic"; // 默认值
  
  const mapping: Record<string, Kind> = {
    "语义维度": "semantic",
    "功能维度": "functional", 
    "感知维度": "perceptual",
    "结构维度": "structural"
  };
  
  return mapping[guidedmethod] || "semantic";
}

// 修改现有的映射函数以处理字符串类型
function mapThemeToCategory(theme: string): Category {
  const mapping: Record<string, Category> = {
    "Nature": "Nature",
    "Artifact": "Artifact", 
    "Body": "Body",
    "Life": "Life",
    "Others": "Others"
  };
  return mapping[theme] || "Others"; // 添加默认值
}

function mapGuidedMethodToKind(guidedmethod: string | null): Kind {
  if (!guidedmethod || guidedmethod === "null") return "semantic"; // 处理null情况
  
  const mapping: Record<string, Kind> = {
    "semantic": "semantic",
    "functional": "functional", 
    "perceptual": "perceptual",
    "structural": "structural"
  };
  return mapping[guidedmethod.toLowerCase()] || "semantic"; // 添加toLowerCase和默认值
}

export default function DivergePanel() {
  const { subject: selectedSubject } = useSubject();
  const [zoomPct, setZoomPct] = useState<number>(100);
  const scale = zoomPct / 100;
  const { selectedTheme, selectedMethod, selectedStrategy } = useFilter();
  // 添加API数据状态
  const [apiVariations, setApiVariations] = useState<ApiVariation[]>([]);
  const [apiLinks, setApiLinks] = useState<ApiLink[]>([]);
  const [apiThemes, setApiThemes] = useState<ApiTheme[]>([]);
  const [hasApiData, setHasApiData] = useState<boolean>(false);

  const sectors = useMemo(() => buildSectors(), []);
  const [nodes, setNodes] = useState<NodeDatum[]>([]);
  const simRef = useRef<Simulation<NodeDatum, undefined> | null>(null);

  const { metaphors } = useMetaphors();
  const { selectedMetaphor, setSelectedMetaphor } = useSelectedMetaphor();
  // 添加存储mapping_spec的state
  const [nodeMetadata, setNodeMetadata] = useState<Map<string, any>>(new Map());
  // 添加state存储完整的variation数据
const [variationDataMap, setVariationDataMap] = useState<Map<string, any>>(new Map());

  // 动态调整节点尺寸
const getNodeScale = (totalNodes: number) => {
  if (totalNodes <= 20) return 1.0;
  if (totalNodes <= 40) return 0.85;
  if (totalNodes <= 60) return 0.7;
  return 0.6;
};
  
 
  const filteredCapsules = useMemo(() => {
    // 优先使用API数据，如果没有则使用context数据
    if (hasApiData && apiVariations.length > 0) {
      let filtered = apiVariations.filter(item => item.field === selectedSubject);
      
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
      // 原有的context数据过滤逻辑
      let filtered = metaphors.capsules.filter(capsule => 
        capsule.field === selectedSubject
      );
      
      // 根据策略过滤 (Guided/Blinded)
      if (selectedStrategy) {
        filtered = filtered.filter(capsule => {
          const capsuleMethod = capsule.method?.toLowerCase() || '';
          const strategyLower = selectedStrategy.toLowerCase();
          return capsuleMethod === strategyLower;
        });
      }
      
      // 根据主题过滤 (Nature, Artifact, Body, Life, Others)
      if (selectedTheme) {
        filtered = filtered.filter(capsule => capsule.theme === selectedTheme);
      }
      
      // 根据方法过滤 (semantic, functional, perceptual, structural)
      if (selectedMethod) {
        filtered = filtered.filter(capsule => 
          capsule.guidedmethod.toLowerCase() === selectedMethod
        );
      }
      
      return filtered;
    }
  }, [hasApiData, apiVariations, metaphors.capsules, selectedSubject, selectedTheme, selectedMethod, selectedStrategy]); 
  // 添加一个全局事件监听器来接收API数据
useEffect(() => {
  const handleApiDataUpdate = (event: CustomEvent) => {
    const { variations, links, themes } = event.detail;
    // 确保每个 variation 都有 dimensions
    const processedVariations = (variations || []).map((v: any) => {
      // 如果 variation 没有 dimensions，尝试从其他字段构建
      if (!v.dimensions || v.dimensions.length === 0) {
        // 根据你的数据结构，可能需要调整这里
        // 例如，如果 dimensions 在其他地方
        console.warn('⚠️ Variation 缺少 dimensions:', v);
        
        // 提供默认值
        v.dimensions = [v.field || "数据", "时间"];
      }
      
      console.log('📦 处理后的 variation:', v.id, 'dimensions:', v.dimensions);
      return v;
    });
    
    setApiVariations(processedVariations);
    setApiLinks(links || []);
    setApiThemes(themes || []);
    setHasApiData(true);
    
    // 存储完整数据
    const dataMap = new Map();
    processedVariations.forEach((v: any) => {
      dataMap.set(v.id, v);
    });
    setVariationDataMap(dataMap);
  };

  window.addEventListener('metaphorDataUpdated', handleApiDataUpdate as EventListener);
  
  return () => {
    window.removeEventListener('metaphorDataUpdated', handleApiDataUpdate as EventListener);
  };
}, []);

// 添加节点点击处理函数
const handleNodeClick = (nodeId: string, nodeLabel: string, nodeThumb: string) => {
  // ✅ 获取完整的variation数据，包括mapping_spec
  const fullData = variationDataMap.get(nodeId);
  console.log('🎯 点击节点，完整数据:', fullData);
  console.log('🎯 Mapping spec:', fullData?.mapping_spec);
  console.log('📐 Dimensions:', fullData?.dimensions);
  console.log('🔧 DefaultPlan:', fullData?.mapping_spec?.defaultPlan);
  
  setSelectedMetaphor({
    id: nodeId,
    keyword: nodeLabel,
    thumb: nodeThumb,
    mapping_spec: fullData?.mapping_spec || null,  // ✅ 传递mapping_spec
    dimensions: fullData?.dimensions || [],  // ✅ 添加 dimensions
    field: fullData?.field,                  // ✅ 添加 field（数据主题）
    dataFact: fullData?.dataFact            // ✅ 添加 dataFact
    
  });
  console.log('Selected metaphor with mapping_spec:', fullData?.mapping_spec);
};

//真实数据
useEffect(() => {
  // 根据数据源选择转换逻辑
  const transformedCapsules: Capsule[] = hasApiData && apiVariations.length > 0
    ? // 转换API数据
      filteredCapsules.map(item => ({
        id: item.id,
        label: item.keyword,
        category: mapApiThemeToCategory(item.theme),
        kind: mapApiGuidedMethodToKind(item.guidedmethod),
        rNorm: item.rNorm,
        thumb: item.thumb,
        method: item.method
      }))
    : // 转换context数据 
      filteredCapsules.map(c => ({
        id: c.id,
        label: c.keyword,
        category: mapThemeToCategory(c.theme),
        kind: mapGuidedMethodToKind(c.guidedmethod),
        rNorm: c.rNorm,
        thumb: c.thumb,
        method: c.method || 'guided'
      }));

      const { rInner, rOuter } = calculateRadiusRange(transformedCapsules.length);
  
      const rFromNormDynamic = (t: number) =>
        rInner + Math.max(0, rOuter - rInner) * Math.min(1, Math.max(0, t));
      const bySector = new Map<Category, Capsule[]>();
  for (const c of transformedCapsules) {
    if (!bySector.has(c.category)) bySector.set(c.category, []);
    bySector.get(c.category)!.push(c);
  }

  // 初始节点逻辑保持不变...
  const initNodes: NodeDatum[] = [];
  for (const [cat, arr] of bySector.entries()) {
    const s = sectorByCategory(sectors, cat);
    const start = normDeg(s.startDeg + 6);
    const end = normDeg(s.endDeg - 6);
    const sweep = (end - start + 360) % 360 || 360;
    const n = arr.length;
    // 在节点创建时应用缩放
const scale = getNodeScale(transformedCapsules.length);
const scaledThumb = THUMB * scale;
const scaledPillH = PILL_H * scale;
const scaledPillGap = PILL_GAP * scale;

    arr.forEach((cp, i) => {
      const theta = n > 1 ? start + (sweep * i) / (n - 1) : s.midDeg;
      const r = rFromNormDynamic(Math.min(Math.max(cp.rNorm, 0), 1));
      const p = polarToXY(CX, CY, r, theta);
    
      // const w = pillTotalW(cp.label);
      // const bboxW = Math.max(THUMB, w);
      // const bboxH = THUMB + PILL_GAP + PILL_H;
      // 计算节点时使用缩放后的尺寸
const w = pillTotalW(cp.label) * scale;
const bboxW = Math.max(scaledThumb, w);
const bboxH = scaledThumb + scaledPillGap + scaledPillH;
      const collideR = 0.5 * Math.hypot(bboxW, bboxH);

      
    
      initNodes.push({
        id: cp.id,
        label: cp.label,
        kind: cp.kind,
        cat: cp.category,
        rTarget: r,
        theta,
        x: p.x,
        y: p.y,
        w,
        h: PILL_H,
        thumb: cp.thumb,
        collideR,
        method: cp.method
      });
    });
  }

  // d3-force 模拟设置保持不变...
  const sim = forceSimulation<NodeDatum>(initNodes)
    .alphaDecay(0.05)
    .velocityDecay(0.4)
    .force("charge", forceManyBody().strength(-15))
    .force("collide", forceCollide<NodeDatum>().radius((d) => d.collideR).strength(0.8))
    .force("radialTarget", forceRadialTarget(initNodes, 0.6))
    .force("centerBarrier", forceMinRadius(initNodes, R_INNER, 1.0));

  // 处理链接 - 优先使用API数据
  const linksData = hasApiData && apiLinks.length > 0 ? apiLinks : metaphors.links;
  
  if (linksData && linksData.length) {
    const linkData: LinkDatumTyped[] = [];
    const id2node = new Map(initNodes.map((n) => [n.id, n]));
    
    for (const lk of linksData) {
      const a = id2node.get(lk.source);
      const b = id2node.get(lk.target);
      if (!a || !b) continue;
      if (a.cat !== b.cat) continue;
      linkData.push({ source: a, target: b, distance: lk.distance });
    }

    if (linkData.length) {
      sim.force(
        "link",
        forceLink<NodeDatum, LinkDatumTyped>(linkData)
          .id((d) => (d as NodeDatum).id)
          .distance((l) => {
            const d = Math.max(20, Math.min(120, l.distance));
            return d;
          })
          .strength(0.2)
      );
    }
  }

  // 其余force设置保持不变...
  const forces = sectors.map((s) => {
    const nodesIn = initNodes.filter((n) => n.cat === s.key);
    return forceAngularBounds(nodesIn, s.startDeg + 3, s.endDeg - 3, 0.8);
  });

  const tick = () => {
    forces.forEach((f) => f());
    setNodes([...initNodes]);
  };

  sim.on("tick", tick);
  simRef.current = sim;

  return () => {
    sim.stop();
    simRef.current = null;
  };
}, [sectors, filteredCapsules, hasApiData, apiLinks, metaphors.links]);


  return (
    <PanelCard bodyStyle={{ padding: 0, overflow: "visible" ,height: "750px"}}>
      <style>{`
        .viz-wrap { position: relative; width: 100%; max-width: 1000px; margin: 0 auto; }
        .board { width: 100%; height: 100%; display: grid; place-items: center; }
        .card { width: 100%; background: #fff; }
        .svg { display: block; width: 100%; height: auto; }
        .legend { fill:#4a5561; font: 600 13px/1.2 Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial; letter-spacing: .2px; }
        .centerShadow { filter: drop-shadow(0 2px 4px rgba(0,0,0,.25)); }
        .pillText { fill:#333; font: 500 12px/1.2 Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial; }
        .zoomHud { position:absolute; left:5px; bottom:5px; background:#fff; padding:5px 5px; border-radius:5px; display:flex; align-items:center; gap:5px; }
      `}</style>

      <div className="board">
        <div className="viz-wrap card">
          <svg className="svg" width={VW} height={VH} viewBox={`0 0 ${VW} ${VH}`} role="img" aria-label="Divergence Map">
            <defs>
              <clipPath id="thumbClip" clipPathUnits="objectBoundingBox">
                <rect x="0" y="0" width="1" height="1" rx="0.2" ry="0.2" />
              </clipPath>
            </defs>
            
            <g transform={`translate(${CX - CX * scale}, ${CY - CY * scale}) scale(${scale})`}>
              {/* 扇区弧 */}
              <g>
                {sectors.map((s) => (
                  <path
                    key={s.key}
                    d={arcPath(CX, CY, R, s.startDeg, s.endDeg)}
                    fill="none"
                    stroke={s.color}
                    strokeWidth={ARC_STROKE}
                    strokeLinecap="round"
                  />
                ))}
              </g>

              {/* 扇区标题 */}
              // 在 DivergePanel.tsx 中修改扇区标题的渲染逻辑
              {sectors.map((s) => {
  const r = R + ARC_STROKE / 2 + LABEL_OUTSET;
  const { x, y } = polarToXY(CX, CY, r, s.midDeg);
  
  // 判断是否是底部扇区（Body 和 Life）
  const isBottomSector = s.key === "Body" || s.key === "Life";
  
  if (isBottomSector) {
    // 底部扇区不旋转文字，直接水平放置
    return (
      <text
        key={s.key}
        x={x}
        y={y} // 向下移动一点，避免与弧线重叠
        textAnchor="middle"
        dominantBaseline="hanging"
        className="legend"
      >
        {s.key}
      </text>
    );
  } else {
    // 其他扇区使用原有的旋转逻辑
    const rot = s.midDeg + 90;
    
    return (
      <text
        key={s.key}
        x={x}
        y={y}
        textAnchor="middle"
        dominantBaseline="middle"
        transform={`rotate(${rot} ${x} ${y})`}
        className="legend"
      >
        {s.key}
      </text>
    );
  }
})}

              {/* 中心主题 */}
              <circle cx={CX} cy={CY} r={40} fill="#49b7aa" stroke="#3A8D8D" strokeWidth={3} className="centerShadow" />
              <text x={CX} y={CY} textAnchor="middle" dominantBaseline="middle" fill="#fff" style={{ font: "500 12px Inter"}}>
                {selectedSubject || " "}
              </text>

              {/* 胶囊节点 */}
              {nodes.map((n) => {
                const sec = sectorByCategory(sectors, n.cat);
                const base = sec.color;
                const fill = lighten(base, 0.86);
                const stroke = lighten(base, 0.64);
                const iconC = darken(base, 0.22);

                const x = n.x ?? CX;
                const y = n.y ?? CY;

                // 判断是否为 blinded 方法
                const isBlinded = n.method?.toLowerCase() === 'blind';

                const Icon = ICONS[n.kind];
                const imgX = x - THUMB / 2;
                const imgY = y - THUMB / 2;
                const pillX = x - n.w / 2;
                const pillY = y + THUMB / 2 + PILL_GAP;

                return (
                  <g key={n.id}
                    style={{ cursor: 'pointer' }}
                    onClick={() => handleNodeClick(n.id, n.label, n.thumb)}>
                     {selectedMetaphor?.id === n.id && (
        <circle
          cx={x}
          cy={y}
          r={n.collideR + 5}
          fill="none"
          stroke="#49b7aa"
          strokeWidth={2}
          strokeDasharray="5,5"
        />
      )}  
                    {/* 缩略图 */}
                    <image
                      x={imgX}
                      y={imgY}
                      width={THUMB}
                      height={THUMB}
                      href={n.thumb || "/placeholder.svg"}
                      preserveAspectRatio="xMidYMid slice"
                      clipPath="url(#thumbClip)"
                      style={{ filter: "drop-shadow(0 1px 2px rgba(0,0,0,.20))" }}
                    />
                    
                    {/* 胶囊背景 - blinded 时使用斜杠纹理 */}
                    {isBlinded ? (
                      <>
                        {/* 定义斜杠纹理 */}
                        <defs>
                          <pattern id={`stripe-${n.id}`} patternUnits="userSpaceOnUse" width="4" height="4">
                            <rect width="4" height="4" fill={fill} />
                            <path d="M0,4 L4,0" stroke={stroke} strokeWidth="1" />
                          </pattern>
                        </defs>
                        {/* 使用纹理填充的胶囊 */}
                        <rect 
                          x={pillX} 
                          y={pillY} 
                          width={n.w} 
                          height={PILL_H} 
                          rx={10} 
                          fill={`url(#stripe-${n.id})`} 
                          stroke={stroke} 
                        />
                      </>
                    ) : (
                      /* 普通胶囊背景 */
                      <rect x={pillX} y={pillY} width={n.w} height={PILL_H} rx={10} fill={fill} stroke={stroke} />
                    )}
                    
                    {/* 图标 - blinded 时显示原点，否则显示对应图标 */}
                    {isBlinded ? (
                      <circle 
                        cx={pillX + 8} 
                        cy={pillY + PILL_H / 2} 
                        r={3.5} 
                        fill={iconC} 
                      />
                    ) : Icon ? (
                      <g transform={`translate(${pillX + 5}, ${pillY + (PILL_H - ICON_BOX) / 2})`} style={{ color: iconC }}>
                        <Icon className="icon-svg" width={ICON_BOX} height={ICON_BOX} />
                      </g>
                    ) : (
                      <circle cx={pillX + 8} cy={pillY + PILL_H / 2} r={3.5} fill={iconC} />
                    )}
                    
                    {/* 文本 */}
                    <text
                      x={pillX + ICON_BOX + 6 + (n.w - ICON_BOX - 6) / 2}
                      y={pillY + PILL_H / 2}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      className="pillText"
                    >
                      {n.label}
                    </text>
                  </g>
                );
              })}
            </g>
          </svg>
        </div>
      </div>

      {/* 缩放控件 */}
      <div className="zoomHud">
        <span style={{ color: "#69737e", fontSize: 12, fontWeight: 500 }}>Zoom</span>
        <strong style={{ color: "#464647", fontSize: 12 }}>{zoomPct}%</strong>
        <div style={{ width: 180 }}>
          <Slider min={25} max={200} value={zoomPct} onChange={(v) => typeof v === "number" && setZoomPct(v)} step={1} tooltip={{ open: false }} />
        </div>
      </div>
    </PanelCard>
  );
}