# Flarum MCP Server

> 🚀 一个用于 Flarum 论坛的 MCP (Model Context Protocol) 服务器，让 AI 助手能够直接在 Flarum 论坛发帖

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-0.9.0+-green.svg)](https://github.com/modelcontextprotocol)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 功能特性

- 🤖 **AI 自动发帖**：通过 AI 助手（如 Claude、AiPy）自动生成并发布论坛帖子
- 📝 **智能内容生成**：内置内容规范约束，自动生成口语化、接地气的帖子内容
- 🏷️ **标签管理**：自动识别和关联论坛标签
- ⚡ **即时发布**：实时调用 Flarum API，秒级完成发帖
- 🔒 **安全可靠**：使用 API Token 认证，支持环境变量配置

## 📋 前置要求

- Python 3.10 或更高版本
- Flarum 论坛（需要管理员权限获取 API Token）
- 支持 MCP 协议的 AI 客户端（如 Claude Desktop、AiPy）

## 🚀 快速开始

### 1️⃣ 克隆项目

```bash
git clone https://github.com/wszdb/FlarumPost-MCP.git
cd FlarumPost-MCP
```

### 2️⃣ 安装依赖

```bash
pip install requests mcp
```

### 3️⃣ 获取 Flarum API Token

1. 登录 Flarum 论坛管理后台
2. 进入 **用户管理** → 选择您的账户
3. 生成 **API 访问令牌**（需要管理员权限）
4. 复制保存 Token（仅显示一次）

### 4️⃣ 配置 MCP 服务器

在您的 MCP 客户端配置文件中添加以下内容：

**Claude Desktop 配置** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "Flarum": {
      "command": "python",
      "args": ["/path/to/FlarumPost-MCP/server.py"],
      "env": {
        "FLARUM_URL": "https://your-forum.com",
        "FLARUM_API_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

**AiPy 配置**：

```json
{
  "mcpServers": {
    "Flarum": {
      "command": "python",
      "args": ["E:\\path\\to\\FlarumPost-MCP\\server.py"],
      "env": {
        "FLARUM_URL": "https://your-forum.com",
        "FLARUM_API_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

### 5️⃣ 重启客户端

重启 Claude Desktop 或 AiPy，服务器将自动加载。

## 📖 使用方法

### 基础用法

直接向 AI 助手发送指令：

```
帮我在论坛发个帖子，标题是"今天的天气真不错"，内容聊聊天气，标签用 shenghuo,xinqing
```

AI 会自动：
1. 生成符合规范的帖子内容（≤250字，口语化）
2. 调用 `create_discussion` 工具
3. 返回发帖结果（帖子ID、字数统计等）

### 高级用法

**指定字数限制**：
```
写个500字的深度分析帖，讨论电梯安全问题，标签用 anquan,taolun
```

**多段落内容**：
```
发个帖子分享今天的经历，分3段写，标签用 shenghuo,fenxiang
```

## 🎯 内容生成规范

本服务内置了以下内容约束（通过工具描述自动传递给 AI）：

### 📏 字数限制
- **默认**：正文不超过 250 字
- **可自定义**：用户可明确指定其他数值（如 500 字、1000 字）

### 💬 语言风格
- **必须口语化**：像普通网民聊天一样自然
- **避免书面语**：不用「据悉」「综上所述」等正式表达

### ✅ 推荐示例
```
今天刷到个新闻，小区电梯钢绳被人割了！太吓人了，
幸好及时发现没出事。听说是物业纠纷导致的，
这也太过分了吧，拿公共安全开玩笑...
```

### ❌ 避免示例
```
近日，某小区发生电梯安全事件，相关部门已介入调查。
此事引发社会广泛关注，值得深入思考。
```

## 🛠️ 工具参数说明

### `create_discussion`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | ✅ | 帖子标题（建议 10-30 字） |
| `content` | string | ✅ | 帖子正文（默认 ≤250 字，支持 Markdown） |
| `tags` | string | ✅ | 标签列表，逗号分隔（如 `shenghuo,xinqing`） |

### 返回示例

**成功**：
```
✅ 发帖成功！
📌 帖子ID: 1234
📝 标题: 今天的天气真不错
📊 正文字数: 185字
🏷️ 标签: shenghuo,xinqing
```

**失败**：
```
❌ 错误：标签不存在 'invalid_tag'
```

## ❓ 常见问题

### Q1: 提示 "环境变量未设置" 怎么办？

**A**: 检查 MCP 配置文件中的 `env` 字段：
- 确认 `FLARUM_URL` 格式正确（如 `https://forum.com`，不要末尾斜杠）
- 确认 `FLARUM_API_TOKEN` 已正确填写
- 重启客户端使配置生效

### Q2: 提示 "标签不存在" 怎么办？

**A**: 标签必须在论坛后台预先创建：
1. 登录 Flarum 管理后台
2. 进入 **标签管理**
3. 创建对应的标签（如 `shenghuo`、`xinqing`）
4. 确保标签的 **Slug** 与您使用的名称一致

### Q3: 如何查看详细错误日志？

**A**: 
- **Claude Desktop**: 查看 `~/Library/Logs/Claude/mcp*.log`
- **AiPy**: 查看应用内的日志面板
- **手动测试**: 直接运行 `python server.py` 查看输出

### Q4: 支持哪些 Markdown 格式？

**A**: 支持 Flarum 的 Markdown 扩展：
- 基础格式：**粗体**、*斜体*、`代码`
- 列表：有序列表、无序列表
- 链接和图片
- 引用块

### Q5: 如何修改默认字数限制？

**A**: 编辑 `server.py` 第 20 行附近的描述文本：
```python
description="""...
1. 字数限制：正文默认不超过250字  # 修改此处数字
...
```

## 📂 项目结构

```
FlarumPost-MCP/
├── server.py          # MCP 服务器主程序（唯一必需文件）
├── requirements.txt   # Python 依赖（可选）
├── LICENSE           # MIT 开源协议
└── README.md         # 本文档
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- [Flarum](https://flarum.org/) - 优雅的论坛软件
- [Model Context Protocol](https://github.com/modelcontextprotocol) - AI 工具集成标准
- [Anthropic Claude](https://www.anthropic.com/) - 强大的 AI 助手

## 📮 联系方式

- 提交 Issue: [GitHub Issues](https://github.com/wszdb/FlarumPost-MCP/issues)
- 项目主页: [https://github.com/wszdb/FlarumPost-MCP](https://github.com/wszdb/FlarumPost-MCP)

---

⭐ 如果这个项目对您有帮助，欢迎给个 Star！
