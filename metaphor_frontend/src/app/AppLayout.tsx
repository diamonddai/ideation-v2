// AppLayout.tsx

import { Layout, Typography } from "antd";
import UnderstandPanel from "../features/understand/UnderstandPanel";
import DivergePanel from "../features/diverge/DivergePanel";
import ConvergePanel from "../features/converge/ConvergePanel";
import PhaseHeaderRow, { COL_TEMPLATE } from "../components/PhaseHeaderRow";
import { SubjectProvider } from "../context/subject";
import { FilterProvider } from '../context/filter';
import { MetaphorsProvider } from '../context/metaphors';
import { SelectedMetaphorProvider } from '../context/selectedMetaphor'; // 添加这一行

const { Header, Content } = Layout;
const { Title } = Typography;

export default function AppLayout() {
  return (
    <MetaphorsProvider>
      <SubjectProvider>
        <FilterProvider>
          <SelectedMetaphorProvider> {/* 添加这个Provider */}
            <Layout>
              <Content style={{ padding: 5, paddingBottom: 5, paddingTop: 5 }}>
                {/* 顶部三块灰色标题条（与内容区同列模板） */}
                <PhaseHeaderRow />

                {/* 三栏内容：左最窄 / 中最宽 / 右第二宽 */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: COL_TEMPLATE,
                    gap: 10,
                    alignItems: "start",
                  }}
                >
                  <div style={{ marginBottom: 1 }}><UnderstandPanel /></div>
                  <div style={{ marginBottom: 1 }}><DivergePanel /></div>
                  <div style={{ marginBottom: 1 }}><ConvergePanel /></div>
                </div>
              </Content>
            </Layout>
          </SelectedMetaphorProvider> {/* 关闭Provider */}
        </FilterProvider>
      </SubjectProvider>
    </MetaphorsProvider>
  );
}