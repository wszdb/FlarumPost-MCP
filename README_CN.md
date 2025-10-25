# Flarum MCP Server

> 🚀 一个用于 Flarum 论坛的 MCP (Model Context Protocol) 服务器，让 AI 助手能够直接在 Flarum 论坛发帖

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-0.9.0+-green.svg)](https://github.com/modelcontextprotocol)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

中文文档 | [English](README.md)

## ✨ 功能特性

- 🤖 **AI 自动发帖**：通过 AI 助手（如 Claude、AiPy）自动生成并发布论坛帖子
- 🔐 **灵活认证**：支持用户名密码自动获取 Token，或直接配置 API Token
- 🏷️ **智能标签**：AI 自动分析内容并匹配最合适的标签
- 📊 **标签控制**：可配置标签数量范围和默认标签
- 📝 **智能内容生成**：内置内容规范约束，自动生成口语化、接地气的帖子内容
- ⚡ **高性能**：Token 缓存、标签缓存，性能优化

## 📋 前置要求

- Python 3.10 或更高版本
- Flarum 论坛账户
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

### 3️⃣ 配置 MCP 服务器

在您的 MCP 客户端配置文件中添加以下内容：

**方式1：Claude Desktop 配置方法**

```json
{
  "mcpServers": {
    "Flarum": {
      "command": "python",
      "args": ["/path/to/FlarumPost-MCP/server.py"],
      "env": {
        "FLARUM_URL": "https://your-forum.com",
        "FLARUM_USERNAME": "your_username",
        "FLARUM_PASSWORD": "your_password",
        "FLARUM_MIN_TAGS": "1",
        "FLARUM_MAX_TAGS": "3",
        "FLARUM_DEFAULT_TAGS": "shenghuo,xinqing"
      }
    }
  }
}
```

**方式2：AiPy Pro配置示例**

```text
1、名称：Flarum MCP
2、类型：studio
3、命令：python
4、参数：E:\code\FlarumPost-MCP\server.py
5、环境变量：
FLARUM_URL=https://bbs.a.com
FLARUM_USERNAME=admin
FLARUM_PASSWORD=password
FLARUM_MIN_TAGS=2
FLARUM_MAX_TAGS=2
```

<img width="529"  alt="局部截取_20251025_174838" src="https://github.com/user-attachments/assets/79b9a2f2-d7e8-4eff-886f-b3bddd89b1ce" />


### 4️⃣ 重启客户端

重启 Claude Desktop 或 AiPy，服务器将自动加载。

## 📖 使用方法

### 基础用法

直接向 AI 助手发送指令：

```
帮我在论坛发个帖子，标题是"今天的天气真不错"，聊聊天气
```

AI 会自动：
1. 生成符合规范的帖子内容（≤250字，口语化）
2. 分析内容主题，自动选择合适的标签
3. 调用 `create_discussion` 工具
4. 返回发帖结果（帖子ID、链接等）

### 高级用法

```
发个帖子，标题"周末去哪玩"，聊聊周末出游计划，内容500字左右
```

AI 会：
- 根据"周末、出游"等关键词自动匹配标签（如：lvyou, xiuxian）
- 生成 500 字左右的口语化内容
- 自动发布

### 最高级用法

```
根据联网搜索自动获取素材自动发贴
```

<img width="963" alt="局部截取_20251025_180347" src="https://github.com/user-attachments/assets/445d9457-6081-48b8-8a07-39705a374a37" />



## ⚙️ 环境变量说明

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `FLARUM_URL` | ✅ | - | 论坛地址（如：https://forum.example.com） |
| `FLARUM_USERNAME` | 🔄 | - | 用户名（与密码配合使用） |
| `FLARUM_PASSWORD` | 🔄 | - | 密码（与用户名配合使用） |
| `FLARUM_API_TOKEN` | 🔄 | - | API Token（优先级高于用户名密码） |
| `FLARUM_MIN_TAGS` | ❌ | 1 | 最少标签数量 |
| `FLARUM_MAX_TAGS` | ❌ | 3 | 最多标签数量 |
| `FLARUM_DEFAULT_TAGS` | ❌ | 空 | 默认标签（逗号分隔），设置后不再 AI 自动匹配 |

**说明：**
- 🔄 表示二选一：必须配置 `USERNAME + PASSWORD` 或 `API_TOKEN`
- ❌ 表示可选配置

## 🎯 使用场景

### 场景 1：AI 自动选择标签（推荐）

**配置：**
```json
{
  "FLARUM_URL": "https://forum.example.com",
  "FLARUM_USERNAME": "admin",
  "FLARUM_PASSWORD": "password123",
  "FLARUM_MIN_TAGS": "2",
  "FLARUM_MAX_TAGS": "4"
}
```

**效果：** AI 会根据帖子内容自动选择 2-4 个最合适的标签

### 场景 2：固定标签发帖

**配置：**
```json
{
  "FLARUM_URL": "https://forum.example.com",
  "FLARUM_USERNAME": "admin",
  "FLARUM_PASSWORD": "password123",
  "FLARUM_DEFAULT_TAGS": "gonggao,zhongyao"
}
```

**效果：** 所有帖子都使用 "gonggao" 和 "zhongyao" 标签，适合批量发公告

## 🔧 工作原理

### 认证流程

```
启动服务器
    ↓
检查配置
    ↓
有 API_TOKEN？
    ↓ 是               ↓ 否
使用 Token      调用 /api/token 获取 Token
    ↓                   ↓
    └─────→ 缓存 Token ←┘
            ↓
        发帖时使用 Token
            ↓
        401 错误？
            ↓ 是
    清除缓存，重新获取 Token
```

### 标签匹配流程

```
启动服务器
    ↓
获取论坛所有标签
    ↓
缓存到内存
    ↓
在工具描述中展示标签列表
    ↓
用户发起发帖请求
    ↓
检查是否配置默认标签？
    ↓ 是              ↓ 否
使用默认标签    AI 查看标签列表并选择
    ↓                   ↓
    └─────→ 验证标签 ←┘
            ↓
        发布帖子
```

## 🐛 故障排查

### 问题 1：获取 Token 失败

**错误：** `❌ 获取 Token 失败 (401)`

**解决：**
- 检查用户名密码是否正确
- 确认账户是否有发帖权限
- 检查论坛是否支持 `/api/token` 接口

### 问题 2：标签不存在

**错误：** `❌ 错误：标签不存在 'xxx'`

**解决：**
- 检查标签 slug 拼写（区分大小写）
- 在论坛后台确认标签存在
- 重启 MCP 服务器刷新标签缓存

### 问题 3：Token 失效

**提示：** `⚠️ Token 失效，重新获取...`

**说明：** 程序会自动重新获取 Token，无需手动处理

## 📊 技术特性

- ✅ **自动 Token 管理**：用户名密码自动获取 Token，失效自动刷新
- ✅ **标签缓存**：启动时获取标签列表并缓存，避免重复请求
- ✅ **智能匹配**：AI 根据内容自动选择最合适的标签
- ✅ **灵活配置**：支持标签数量范围和默认值配置
- ✅ **向后兼容**：完全兼容旧版 API Token 配置
- ✅ **错误处理**：完善的异常处理和重试机制


## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License

## 🙏 致谢

感谢所有使用和支持本项目的用户！

---

**项目地址：** https://github.com/wszdb/FlarumPost-MCP

**问题反馈：** 请在 GitHub 提交 Issue







