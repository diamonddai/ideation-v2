// src/components/PhaseHeaderRow.tsx
import React from "react";

const COL_TEMPLATE =
  "minmax(220px, 1fr) minmax(500px, 2.8fr) minmax(360px, 1.6fr)";

const headerBox: React.CSSProperties = {
  background: "#6C757E",     // 灰色标题条
  color: "#FFFFFF",
  borderRadius: 0,
  padding: "10px 16px",
  fontWeight: 600,
  letterSpacing: "0.5px",
};

export default function PhaseHeaderRow() {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: COL_TEMPLATE,
        gap: 16,
        marginBottom: 6,    // 与下方内容区留空隙
      }}
    >
      <div style={headerBox}>Understanding</div>
      <div style={headerBox}>Divergence</div>
      <div style={headerBox}>Convergence</div>
    </div>
  );
}

// 导出列模板，给下方内容区复用，确保对齐
export { COL_TEMPLATE };
