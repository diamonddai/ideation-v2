# 图片生成测试

这个模块用于测试DALL-E图片生成功能，并将生成的图片上传到阿里云OSS。

## 功能特性

- 使用DALL-E-3模型生成高质量图片
- 自动上传到阿里云OSS存储
- 支持从prompt.json文件批量测试
- 生成测试报告和结果

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements_image.txt
```

### 2. 配置环境变量

在项目根目录的`.env`文件中添加以下配置：

```bash
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.nbai.art/v1

# 阿里云OSS配置
ALIYUN_OSS_ACCESS_KEY_ID=your_access_key_id
ALIYUN_OSS_ACCESS_KEY_SECRET=your_access_key_secret
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET_NAME=your_bucket_name
ALIYUN_OSS_REGION=cn-hangzhou
```

### 3. 阿里云OSS配置说明

- **Access Key ID/Secret**: 在阿里云控制台 -> RAM访问控制 -> 用户 -> 创建AccessKey
- **Endpoint**: 根据你的Bucket所在地区选择，例如：
  - 华东1（杭州）: `oss-cn-hangzhou.aliyuncs.com`
  - 华北1（青岛）: `oss-cn-qingdao.aliyuncs.com`
  - 华北2（北京）: `oss-cn-beijing.aliyuncs.com`
- **Bucket Name**: 你创建的OSS存储桶名称
- **Region**: 存储桶所在地区

## 使用方法

### 1. 测试配置

首先运行配置测试脚本：

```bash
cd metaphor_backend/experiment/generate_image
python test_config.py
```

### 2. 运行图片生成测试

```bash
python test_image_generation.py
```

### 3. 查看结果

测试完成后会生成`test_results.json`文件，包含：
- 测试ID和元数据
- 生成的OSS图片URL
- 成功/失败状态

## 文件说明

- `test_image_generation.py`: 主要的图片生成测试脚本
- `test_config.py`: 配置验证脚本
- `prompt.json`: 测试用的图片提示词数据
- `requirements_image.txt`: 依赖包列表
- `test_results.json`: 测试结果输出文件

## 注意事项

1. 确保阿里云OSS Bucket已创建并配置了正确的访问权限
2. DALL-E API调用需要消耗OpenAI额度
3. 图片生成可能需要1-2分钟时间
4. 建议先测试少量图片，确认配置正确后再批量生成

## 故障排除

### 常见问题

1. **配置验证失败**
   - 检查.env文件中的配置是否正确
   - 确保所有必需的配置项都已设置

2. **图片生成失败**
   - 检查OpenAI API Key是否有效
   - 确认API Base URL是否正确
   - 查看网络连接是否正常

3. **OSS上传失败**
   - 检查AccessKey权限是否足够
   - 确认Bucket名称和Endpoint是否正确
   - 验证Bucket是否允许上传操作

### 日志查看

测试过程中会输出详细的日志信息，包括：
- 配置验证结果
- 图片生成状态
- 上传进度
- 错误信息 