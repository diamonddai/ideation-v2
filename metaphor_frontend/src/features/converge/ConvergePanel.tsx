

import React, { useMemo, useState, useEffect } from "react";
import PanelCard from "../../components/PanelCard";
import { Row, Col, Card, Button, Typography, Space, Dropdown, Divider, message, Spin } from "antd";
import type { MenuProps } from "antd";
import { CaretDownFilled, ArrowRightOutlined, LoadingOutlined } from "@ant-design/icons";
import { useSubject } from "../../context/subject";
import { useSelectedMetaphor } from "../../context/selectedMetaphor";
import axios from 'axios';
// import {api} from "../../lib/api";
import { getApiUrl } from "../../lib/api";


const { Title, Text } = Typography;

// 定义图片历史记录项
interface ImageHistory {
  id: string;
  url: string;
  timestamp: Date;
  mappingSpec: any;
  isOriginal?: boolean;
}

export default function ConvergePanel() {
  const { selectedMetaphor } = useSelectedMetaphor();
  const { subject: selectedSubject,dimensions: subjectDimensions } = useSubject();
  const [currentDimensions, setCurrentDimensions] = useState<string[]>([]);
  
  // 第一个映射项相关状态
  const [firstMappingItem, setFirstMappingItem] = useState<string>("");
  const [firstMappingItemName, setFirstMappingItemName] = useState<string>("");
  const [firstMappingOptions, setFirstMappingOptions] = useState<any[]>([]);
  const [firstChannelSelected, setFirstChannelSelected] = useState<string[]>([]);
  const [firstChannelAllowed, setFirstChannelAllowed] = useState<string[]>([]);
  
  // 第二个映射项相关状态
  const [secondMappingItem, setSecondMappingItem] = useState<string>("");
  const [secondMappingItemName, setSecondMappingItemName] = useState<string>("");
  const [secondMappingOptions, setSecondMappingOptions] = useState<any[]>([]);
  const [secondChannelSelected, setSecondChannelSelected] = useState<string[]>([]);
  const [secondChannelAllowed, setSecondChannelAllowed] = useState<string[]>([]);

  // 新增状态
  const [currentImage, setCurrentImage] = useState<string>("");
  const [imageHistory, setImageHistory] = useState<ImageHistory[]>([]);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [currentMappingSpec, setCurrentMappingSpec] = useState<any>(null);
  const [hasChanges, setHasChanges] = useState<boolean>(false);

  // 格式化函数
  const formatDimension = (dimension: string): string => {
    if (!dimension) return "";
    // 移除 "$m" 后缀并美化显示
    return dimension
      .replace(/\s*\$m$/i, '')  // 移除 $m
      .replace(/_/g, ' ')        // 替换下划线为空格
      .replace(/([A-Z])/g, ' $1') // 在大写字母前加空格
      .trim();
  };

  useEffect(() => {
    console.log('📊 ConvergePanel dimensions 详细信息:');
    console.log('  - 原始数组:', subjectDimensions);
    console.log('  - 数组长度:', subjectDimensions?.length);
    console.log('  - [0]:', subjectDimensions?.[0]);
    console.log('  - [1]:', subjectDimensions?.[1]);
    console.log('  - JSON.stringify:', JSON.stringify(subjectDimensions));
    
    if (subjectDimensions && subjectDimensions.length > 0) {
      setCurrentDimensions([...subjectDimensions]); // 使用展开运算符确保创建新数组
    }
  }, [subjectDimensions]);

// 监听 selectedMetaphor 变化，初始化数据
useEffect(() => {
  console.log('🎨 ConvergePanel收到selectedMetaphor:', selectedMetaphor);
  
  if (selectedMetaphor) {
    // 打印所有可用字段
    console.log('📋 可用字段:', {
      dimensions: selectedMetaphor.dimensions,
      mapping_spec: selectedMetaphor.mapping_spec,
      field: selectedMetaphor.field,
      keyword: selectedMetaphor.keyword,
      dataFact: selectedMetaphor.dataFact
    });
    
    const spec = selectedMetaphor.mapping_spec;
    
    // 不再从 selectedMetaphor 获取 dimensions，因为已经从 subject 获取了
    // 只处理 mapping_spec 相关的状态
    if (spec) {
      setCurrentMappingSpec(spec);
      
      // 处理defaultPlan和field1
      if (spec.defaultPlan?.[0] && spec.field1) {
        setFirstMappingItem(spec.defaultPlan[0].subitemId || "");
        setFirstMappingItemName(spec.defaultPlan[0].subitemName || "");
        setFirstChannelSelected(spec.defaultPlan[0].channels || []);
        setFirstMappingOptions(spec.field1.subitemOptions || []);
        setFirstChannelAllowed(spec.field1.channels?.allowed || []);
      } else {
        console.log('⚠️ field1数据不完整');
      }
      
      // 处理defaultPlan和field2
      if (spec.defaultPlan?.[1] && spec.field2) {
        setSecondMappingItem(spec.defaultPlan[1].subitemId || "");
        setSecondMappingItemName(spec.defaultPlan[1].subitemName || "");
        setSecondChannelSelected(spec.defaultPlan[1].channels || []);
        setSecondMappingOptions(spec.field2.subitemOptions || []);
        setSecondChannelAllowed(spec.field2.channels?.allowed || []);
      } else {
        console.log('⚠️ field2数据不完整');
      }
    }
    
    // 设置当前图片并添加到历史记录
    if (selectedMetaphor.thumb) {
      setCurrentImage(selectedMetaphor.thumb);
      
      // 清空历史记录并添加原始图片
      setImageHistory([{
        id: `original-${Date.now()}`,
        url: selectedMetaphor.thumb,
        timestamp: new Date(),
        mappingSpec: spec,
        isOriginal: true
      }]);
    }
    
    setHasChanges(false);
  } else {
    console.log('❌ selectedMetaphor为空，清空映射相关状态');
    // 只重置映射相关的状态，不重置 dimensions
    resetMappingStates();
  }
}, [selectedMetaphor]);

// 重置所有状态（包括 dimensions）
const resetStates = () => {
  setCurrentDimensions([]);
  resetMappingStates();
};

// 只重置映射相关状态（不重置 dimensions）
const resetMappingStates = () => {
  setFirstMappingItem("");
  setFirstMappingItemName("");
  setFirstMappingOptions([]);
  setFirstChannelSelected([]);
  setFirstChannelAllowed([]);
  setSecondMappingItem("");
  setSecondMappingItemName("");
  setSecondMappingOptions([]);
  setSecondChannelSelected([]);
  setSecondChannelAllowed([]);
  setCurrentImage("");
  setImageHistory([]);
  setCurrentMappingSpec(null);
  setHasChanges(false);
};

  // 第一个映射项的下拉菜单
  const firstMappingMenu: MenuProps = {
    items: firstMappingOptions.map((opt) => ({ 
      key: opt.subitem_id, 
      label: opt.name 
    })),
    onClick: ({ key }) => {
      const selected = firstMappingOptions.find(opt => opt.subitem_id === key);
      if (selected) {
        setFirstMappingItem(selected.subitem_id);
        setFirstMappingItemName(selected.name);
        setHasChanges(true);
      }
    },
  };

  // 第二个映射项的下拉菜单
  const secondMappingMenu: MenuProps = {
    items: secondMappingOptions.map((opt) => ({ 
      key: opt.subitem_id, 
      label: opt.name 
    })),
    onClick: ({ key }) => {
      const selected = secondMappingOptions.find(opt => opt.subitem_id === key);
      if (selected) {
        setSecondMappingItem(selected.subitem_id);
        setSecondMappingItemName(selected.name);
        setHasChanges(true);
      }
    },
  };

  // 第一个channel的下拉菜单
  const firstChannelMenu: MenuProps = {
    items: firstChannelAllowed.map((channel) => ({ 
      key: channel, 
      label: channel 
    })),
    onClick: ({ key }) => {
      setFirstChannelSelected([String(key)]);
      setHasChanges(true);
    },
  };

  // 第二个channel的下拉菜单
  const secondChannelMenu: MenuProps = {
    items: secondChannelAllowed.map((channel) => ({ 
      key: channel, 
      label: channel 
    })),
    onClick: ({ key }) => {
      setSecondChannelSelected([String(key)]);
      setHasChanges(true);
    },
  };

  // 构建修改后的mapping_spec
  const buildModifiedMappingSpec = () => {
    if (!currentMappingSpec) return null;
    
    const modifiedSpec = JSON.parse(JSON.stringify(currentMappingSpec));
    
    // 更新defaultPlan[0]
    if (modifiedSpec.defaultPlan?.[0]) {
      modifiedSpec.defaultPlan[0].subitemId = firstMappingItem;
      modifiedSpec.defaultPlan[0].subitemName = firstMappingItemName;
      modifiedSpec.defaultPlan[0].channels = firstChannelSelected;
    }
    
    // 更新defaultPlan[1]
    if (modifiedSpec.defaultPlan?.[1]) {
      modifiedSpec.defaultPlan[1].subitemId = secondMappingItem;
      modifiedSpec.defaultPlan[1].subitemName = secondMappingItemName;
      modifiedSpec.defaultPlan[1].channels = secondChannelSelected;
    }
    
    return modifiedSpec;
  };

  // Generate按钮点击事件
  const handleGenerate = async () => {
    if (!selectedMetaphor || !hasChanges) {
      message.info('请先修改映射配置');
      return;
    }
    
    setIsGenerating(true);
    
    try {
      const modifiedSpec = buildModifiedMappingSpec();
      
      // 调用后端API生成新图片
      const response = await axios.post(getApiUrl('/v1/module3/generate-visualization-one'), {
        field: selectedMetaphor.keyword,
        field1: modifiedSpec.field1?.dataField || selectedSubject,
        field2: modifiedSpec.field2?.dataField || "时间",
        keyword: selectedMetaphor.keyword,
        data_fact: modifiedSpec.dataFact || "",
        method: 1,
        context_description: modifiedSpec.contextDescription || "",
        mapping_override: modifiedSpec
      });
      
      if (response.data.success) {
        const newImageUrl = response.data.image_url;
        
        // 将当前图片加入历史记录
        if (currentImage) {
          setImageHistory(prev => [...prev, {
            id: `gen-${Date.now()}`,
            url: newImageUrl,
            timestamp: new Date(),
            mappingSpec: modifiedSpec,
            isOriginal: false
          }]);
        }
        
        // 更新当前显示的图片
        setCurrentImage(newImageUrl);
        setCurrentMappingSpec(modifiedSpec);
        setHasChanges(false);
        
        message.success('新图片生成成功！');
      } else {
        message.error(response.data.error || '生成失败');
      }
    } catch (error) {
      console.error('生成图片失败:', error);
      message.error('生成图片失败，请重试');
    } finally {
      setIsGenerating(false);
    }
  };

  // Regenerate按钮点击事件
  const handleRegenerate = async () => {
    if (!currentMappingSpec) {
      message.info('请先选择一个喻体');
      return;
    }
    
    setIsGenerating(true);
    
    try {
      const response = await axios.post(getApiUrl('/v1/module3/generate-visualization-one'), {
        field: selectedMetaphor?.keyword,
        field1: currentMappingSpec.field1?.dataField || selectedSubject,
        field2: currentMappingSpec.field2?.dataField || "时间",
        keyword: selectedMetaphor?.keyword,
        data_fact: currentMappingSpec.dataFact || "",
        method: 1,
        context_description: currentMappingSpec.contextDescription || "",
        mapping_override: currentMappingSpec
      });
      
      if (response.data.success) {
        const newImageUrl = response.data.image_url;
        
        // 添加到历史记录
        setImageHistory(prev => [...prev, {
          id: `regen-${Date.now()}`,
          url: newImageUrl,
          timestamp: new Date(),
          mappingSpec: currentMappingSpec,
          isOriginal: false
        }]);
        
        setCurrentImage(newImageUrl);
        message.success('重新生成成功！');
      }
    } catch (error) {
      message.error('重新生成失败');
    } finally {
      setIsGenerating(false);
    }
  };

  // 切换历史图片
  const switchToHistoryImage = (historyItem: ImageHistory) => {
    setCurrentImage(historyItem.url);
    setCurrentMappingSpec(historyItem.mappingSpec);
    
    // 更新显示的映射配置
    if (historyItem.mappingSpec?.defaultPlan) {
      const spec = historyItem.mappingSpec;
      
      if (spec.defaultPlan[0]) {
        setFirstMappingItem(spec.defaultPlan[0].subitemId);
        setFirstMappingItemName(spec.defaultPlan[0].subitemName);
        setFirstChannelSelected(spec.defaultPlan[0].channels);
      }
      
      if (spec.defaultPlan[1]) {
        setSecondMappingItem(spec.defaultPlan[1].subitemId);
        setSecondMappingItemName(spec.defaultPlan[1].subitemName);
        setSecondChannelSelected(spec.defaultPlan[1].channels);
      }
    }
    
    setHasChanges(false);
  };


  return (
    <PanelCard bodyStyle={{ padding: 5, height: "750px", maxHeight: "750px", overflow: "hidden",position: "relative"}}>
      <div style={{
        borderRadius: 10,
        background: "#FFFFFF",
        padding: 3,
        width: "100%",
        height: "100%",
        overflow: "hidden",
      }}>
        {/* 顶部三列栏目标题 */}
        <Row style={{ marginBottom: 0,paddingTop:0 }}>
          <Col span={7}>
            <Text style={{ fontSize:12, fontWeight:600, margin: 0,marginLeft:40, textAlign: "center", color: "#21252b" }}>
              Tenor
            </Text>
          </Col>
          <Col span={8}>
          <Text style={{ fontSize:12, fontWeight:600, margin: 0,marginLeft:40, textAlign: "center", color: "#21252b" }}>
              Vehicle
            </Text>
          </Col>
          <Col span={8}>
          <Text style={{ fontSize:12, fontWeight:600, margin: 0,marginLeft:0, textAlign: "center", color: "#21252b" }}>
              Visual Channel
            </Text>
          </Col>
        </Row>

        {/* 内层浅灰内容区 */}
        <div style={{
          background: "#F3F3F4",
          borderRadius: 14,
          padding: "20px 20px 20px 20px",
          height:"665px"
        }}>
          <Row gutter={1} align="top" wrap={false}>
            {/* 左列：本体 */}
            <Col flex="90px">
              <Card
                
                style={{ borderRadius: 5, overflow: "hidden", background: "#fbfbfc", border: "1px solid #BABFC6" }}
                bodyStyle={{ padding: 0 }}
              >
                <div style={{
                  background: "#343a41",
                  color: "#fff",
                  textAlign: "center",
                  padding: "6px 10px"
                }}>
                  <Text strong style={{
                    color: "#fff",
                    fontSize: 12,
                    display: "inline-block",
                    minWidth: 60,
                    textAlign: "center",
                  }}>
                    {selectedSubject || " "}
                  </Text>
                </div>

                <div style={{ padding: 5 }}>
                  <Space direction="vertical" style={{ width: "100%", paddingTop: 20, paddingBottom: 20 }} size={40}>
                    <Card bodyStyle={{ padding: 5 }} style={{ 
                      background: "#EEEFF3", 
                      borderRadius: 5, 
                      textAlign: "center", 
                      margin: 0,
                      borderLeft: "2px solid #CDD5DF" ,
                      minHeight: 26
                    }}>
                      <Text style={{ fontSize: 10 }}>  {formatDimension(currentDimensions[0]) || "\u00A0"}
                      </Text>
                    </Card>
                    <Card bodyStyle={{ padding: 5 }} style={{ 
                      background: "#EEEFF3", 
                      borderRadius: 5, 
                      textAlign: "center", 
                      margin: 0,
                      borderLeft: "2px solid #CDD5DF" ,
                      minHeight: 26
                    }}>
                      <Text style={{ fontSize: 10 }}> {formatDimension(currentDimensions[1]) || "\u00A0"}</Text>
                    </Card>
                  </Space>
                </div>
              </Card>
            </Col>

            {/* 箭头列 */}
            <Col flex="15px" style={{
              display: "flex",
              flexDirection: "column",
              gap: 56,
              paddingTop: 12,
              alignItems: "center",
            }}>
              <ArrowRightOutlined style={{ color: "#464647" }} />
              <ArrowRightOutlined style={{ color: "#464647" }} />
              <ArrowRightOutlined style={{ color: "#464647" }} />
            </Col>
            
            {/* 右侧：喻体映射面板 */}
            <Col flex="auto">
              <Card
                
                style={{
                  borderRadius: 8,
                  overflow: "hidden",
                  border: "1px solid #dbe1ea",
                  background: "#fff",
                }}
                bodyStyle={{ padding: 0 }}
              >
                {/* 喻体名称标题 */}
                <div style={{ background: "#343a41", padding: "6px 10px", width: "100%", textAlign: "center" ,minHeight: 34}}>
                  <Text strong style={{ color: "#fff", fontSize: 12 }}>
                    {selectedMetaphor?.keyword || " "}
                  </Text>
                </div>

                <div style={{ padding: "20px 10px" }}>
                  {/* 行1：第一个映射 */}
                  <div style={{
                    background: "#EEEFF3",
                    borderTop: "1px solid #EEEFF3",
  borderRight: "1px solid #EEEFF3",
  borderBottom: "1px solid #EEEFF3",
                    borderRadius: 5,
                    padding: "10px 10px",
                    marginBottom: 10,
                    borderLeft: "2px solid #CDD5DF",
                  }}>
                    <Row gutter={12} align="middle" wrap={false}>
                      <Col flex="140px">
                        <Dropdown menu={firstMappingMenu} trigger={["click"]} disabled={!firstMappingOptions.length}>
                          <div style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: 3,
                            cursor: firstMappingOptions.length ? "pointer" : "default",
                            paddingBottom: 2,
                            borderBottom: "1px solid #B9BABF",
                            whiteSpace: "nowrap",
                            width: "100%",
                            justifyContent: "center",
                          }}>
                            <span style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: 4,
                              lineHeight: 1,
                            }}>
                              <Text style={{ fontSize: 10, color: "#464647" }}>
                                {firstMappingItemName || ""}
                              </Text>
                              {firstMappingOptions.length > 0 && (
                                <CaretDownFilled style={{ fontSize: 6, color: "#464647" }} />
                              )}
                            </span>
                          </div>
                        </Dropdown>
                      </Col>

                      <Col flex="auto">
                        <div style={{
                          background: "#D8DCE4",
                         
                          borderTop: "1px solid #D8DCE4",
  borderRight: "1px solid #D8DCE4",
  borderBottom: "1px solid #D8DCE4",
                          borderLeft: "2px solid #919AA5",
                          borderRadius: 5,
                          padding: 10,
                        }}>
                          <Dropdown menu={firstChannelMenu} trigger={["click"]} disabled={!firstChannelAllowed.length}>
                            <div style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: 3,
                              cursor: firstChannelAllowed.length ? "pointer" : "default",
                              paddingBottom: 0,
                              borderBottom: "1px solid #B9BABF",
                            }}>
                              <span style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: 4,
                                lineHeight: 1,
                              }}>
                                <Text style={{ fontSize: 10, color: "#464647" }}>
                                  {firstChannelSelected.join(", ") || " "}
                                </Text>
                                {firstChannelAllowed.length > 0 && (
                                  <CaretDownFilled style={{ fontSize: 6, color: "#464647" }} />
                                )}
                              </span>
                            </div>
                          </Dropdown>
                        </div>
                      </Col>
                    </Row>
                  </div>

                  {/* 行2：第二个映射 */}
                  <div style={{
                    background: "#f1f3f6",
                    
                    borderTop: "1px solid #dbe1ea",
  borderRight: "1px solid #dbe1ea",
  borderBottom: "1px solid #dbe1ea",
                          
                    borderRadius: 10,
                    padding: 12,
                    borderLeft: "2px solid #CDD5DF",
                  }}>
                    <Row gutter={12} align="middle" wrap={false}>
                      <Col flex="140px">
                        <Dropdown menu={secondMappingMenu} trigger={["click"]} disabled={!secondMappingOptions.length}>
                          <div style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: 3,
                            cursor: secondMappingOptions.length ? "pointer" : "default",
                            paddingBottom: 2,
                            borderBottom: "1px solid #B9BABF",
                            whiteSpace: "nowrap",
                            width: "100%",
                            justifyContent: "center",
                          }}>
                            <span style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: 4,
                              lineHeight: 1,
                            }}>
                              <Text style={{ fontSize: 10, color: "#464647" }}>
                                {secondMappingItemName || ""}
                              </Text>
                              {secondMappingOptions.length > 0 && (
                                <CaretDownFilled style={{ fontSize: 6, color: "#464647" }} />
                              )}
                            </span>
                          </div>
                        </Dropdown>
                      </Col>

                      <Col flex="auto">
                        <div style={{
                          background: "#D8DCE4",
                          border: "1px solid #D8DCE4",
                          borderTop: "1px solid #D8DCE4",
  borderRight: "1px solid #D8DCE4",
  borderBottom: "1px solid #D8DCE4",
                          borderLeft: "2px solid #919AA5",
                          borderRadius: 5,
                          padding: 10,
                        }}>
                          <Dropdown menu={secondChannelMenu} trigger={["click"]} disabled={!secondChannelAllowed.length}>
                            <div style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: 3,
                              cursor: secondChannelAllowed.length ? "pointer" : "default",
                              paddingBottom: 2,
                              borderBottom: "1px solid #B9BABF",
                            }}>
                              <span style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: 4,
                                lineHeight: 1,
                              }}>
                                <Text style={{ fontSize: 10, color: "#464647" }}>
                                  {secondChannelSelected.join(", ") || ""}
                                </Text>
                                {secondChannelAllowed.length > 0 && (
                                  <CaretDownFilled style={{ fontSize: 6, color: "#464647" }} />
                                )}
                              </span>
                            </div>
                          </Dropdown>
                        </div>
                      </Col>
                    </Row>
                  </div>
                </div>
              </Card>
            </Col>   
          </Row>

          {/* 画布 */}
          <div style={{ marginTop: 0, display: "flex", flexDirection: "column", alignItems: "center"   }}>
            <Text style={{ fontSize: 12, fontWeight: 600, color: "#21252b", marginBottom: 0, display: "block",alignSelf: "flex-start"  }}>
              Preview
            </Text>
          <Card
            style={{
              background: "#fff",
              borderRadius: 5,
              marginTop: 0,
              border: "1px solid #D8DCE4",
              width: 350,
              height: 350,
              overflow: "hidden",
              
            }}
            bodyStyle={{ 
              padding: 5,
                width: "100%",
                height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}
          >
            {isGenerating ? (
    <Spin indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />} />
  ) : currentImage || selectedMetaphor?.thumb ? (
    <img 
      src={currentImage || selectedMetaphor?.thumb}  // ✅ 优先显示currentImage，回退到selectedMetaphor.thumb
      alt={selectedMetaphor?.keyword}
      style={{ 
        maxWidth: "100%", 
        maxHeight: "100%",
        objectFit: "contain"
      }}
    />
  ) : (
    <Text style={{ color: "#999" }}>Please select a metaphor</Text>
  )}
          </Card>
          </div>

        {/* 历史记录 */}
        {imageHistory.length > 0 && (
          <div style={{ marginTop: -5 ,minHeight:50,marginLeft:25}}>
            
            <Space size={8} style={{ width: "100%", overflowX: "auto", paddingBottom: 0 }}>
              {imageHistory.map((item) => (
                <Card
                  key={item.id}
                  hoverable
                  style={{ 
                    width: 35, 
                    height: 35, 
                    padding: 0,
                    cursor: "pointer",
                    border: currentImage === item.url ? "2px solid #49b7aa" : "1px solid #ddd",
                    position: "relative"  // ✅ 添加这个让原始标记正确定位
                  }}
                  bodyStyle={{ padding: 0 }}
                  onClick={() => switchToHistoryImage(item)}
                >
                  <img 
                    src={item.url} 
                    alt="history"
                    style={{ 
                      width: "100%", 
                      height: "100%", 
                      objectFit: "cover",
                      borderRadius: 4
                    }}
                  />
                  {item.isOriginal && (
                    <div style={{
                      position: "absolute",
                      top: 2,
                      right: 2,
                      background: "#49b7aa",
                      color: "#fff",
                      fontSize: 8,
                      padding: "1px 3px",
                      borderRadius: 2
                    }}>
                      Initial
                    </div>
                  )}
                </Card>
              ))}
            </Space>
          </div>
        )}
       
      </div>  {/* ✅ 内层浅灰区域结束 */}

      {/* 底部按钮 - 移到正确位置 */}
      <Row align="middle" justify="space-between" style={{ marginTop: 5 }}>
        <Col>
          <Button 
            onClick={handleRegenerate}
            disabled={!selectedMetaphor || isGenerating}
            style={{ 
              height: 40, 
              padding: "0 16px",
              width: 180,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              borderRadius: 5
            }}
          >
            Regenerate
          </Button>
        </Col>
        <Col>
          <Button
            type="primary"
            onClick={handleGenerate}
            disabled={!selectedMetaphor || !hasChanges || isGenerating}
            loading={isGenerating}
            style={{
              height: 40,
              width: 180,
              padding: "0 16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              borderRadius: 5,
              background: hasChanges ? "#343A41" : "#999",
              borderColor: hasChanges ? "#343A41" : "#999",
              color: "#fff",
            }}
          >
            Generate
          </Button>
        </Col>
      </Row>
    </div>  {/* ✅ 外层白色区域结束 */}
  </PanelCard>
);
}