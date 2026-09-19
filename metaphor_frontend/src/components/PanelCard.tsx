import { Card } from "antd";
import type { PropsWithChildren, ReactNode, CSSProperties  } from "react";

type Props = PropsWithChildren<{
  title?: ReactNode;
  extra?: ReactNode;
  bodyStyle?: CSSProperties;   // ✅ 新增
  style?: CSSProperties;       // ✅ 新增
}>;

export default function PanelCard({ title, extra, children, style, bodyStyle}: Props) {
  return (
    <div className="panel-card">
      <Card title={title} extra={extra}  style={{ width: "100%", ...style }} bodyStyle={bodyStyle} >
        {children}
      </Card>
    </div>
  );
}
