# Flarum MCP Server

> 🚀 A Model Context Protocol (MCP) server for Flarum forums, enabling AI assistants to post directly to Flarum

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-0.9.0+-green.svg)](https://github.com/modelcontextprotocol)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[中文文档](README_CN.md) | English

## ✨ Features

- 🤖 **AI Auto-Posting**: Automatically generate and publish forum posts via AI assistants (Claude, AiPy, etc.)
- 🔐 **Flexible Authentication**: Support username/password auto-login or direct API Token configuration
- 🏷️ **Smart Tags**: AI automatically analyzes content and matches the most suitable tags
- 📊 **Tag Control**: Configurable tag quantity range and default tags
- 📝 **Smart Content Generation**: Built-in content specifications for natural, conversational post generation
- ⚡ **High Performance**: Token caching, tag caching, optimized performance

## 📋 Requirements

- Python 3.10 or higher
- Flarum forum account
- MCP-compatible AI client (Claude Desktop, AiPy, etc.)

## 🚀 Quick Start

### 1️⃣ Clone the Project

```bash
git clone https://github.com/wszdb/FlarumPost-MCP.git
cd FlarumPost-MCP
```

### 2️⃣ Install Dependencies

```bash
pip install requests mcp
```

### 3️⃣ Configure MCP Server

Add the following to your MCP client configuration file:

**Method 1: Claude Desktop Configuration**

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
        "FLARUM_DEFAULT_TAGS": "general,discussion"
      }
    }
  }
}
```

**Method 2: AiPy Pro Configuration Example**

```text
1. Name: Flarum MCP
2. Type: studio
3. Command: python
4. Arguments: E:\code\FlarumPost-MCP\server.py
5. Environment Variables:
FLARUM_URL=https://bbs.a.com
FLARUM_USERNAME=admin
FLARUM_PASSWORD=password
FLARUM_MIN_TAGS=2
FLARUM_MAX_TAGS=2
```

<img width="529" alt="Configuration Screenshot" src="https://github.com/user-attachments/assets/79b9a2f2-d7e8-4eff-886f-b3bddd89b1ce" />


### 4️⃣ Restart Client

Restart Claude Desktop or AiPy to load the server.

## 📖 Usage

### Basic Usage

Simply send instructions to your AI assistant:

```
Help me post on the forum, title "Beautiful Weather Today", talk about the weather
```

AI will automatically:
1. Generate content following specifications (≤250 words, conversational)
2. Analyze content theme and select appropriate tags
3. Call the `create_discussion` tool
4. Return post results (post ID, link, etc.)

### Advanced Usage

```
Post something, title "Weekend Plans", talk about weekend travel plans, about 500 words
```

AI will:
- Match tags based on keywords like "weekend, travel" (e.g., travel, leisure)
- Generate ~500 words of conversational content
- Auto-publish

### Expert Usage

```
Automatically fetch materials from web search and auto-post
```

<img width="963" alt="Auto-posting Screenshot" src="https://github.com/user-attachments/assets/445d9457-6081-48b8-8a07-39705a374a37" />



## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLARUM_URL` | ✅ | - | Forum URL (e.g., https://forum.example.com) |
| `FLARUM_USERNAME` | 🔄 | - | Username (use with password) |
| `FLARUM_PASSWORD` | 🔄 | - | Password (use with username) |
| `FLARUM_API_TOKEN` | 🔄 | - | API Token (higher priority than username/password) |
| `FLARUM_MIN_TAGS` | ❌ | 1 | Minimum number of tags |
| `FLARUM_MAX_TAGS` | ❌ | 3 | Maximum number of tags |
| `FLARUM_DEFAULT_TAGS` | ❌ | empty | Default tags (comma-separated), skips AI matching if set |

**Notes:**
- 🔄 Either/Or: Must configure `USERNAME + PASSWORD` or `API_TOKEN`
- ❌ Optional configuration

## 🎯 Use Cases

### Case 1: AI Auto-Select Tags (Recommended)

**Configuration:**
```json
{
  "FLARUM_URL": "https://forum.example.com",
  "FLARUM_USERNAME": "admin",
  "FLARUM_PASSWORD": "password123",
  "FLARUM_MIN_TAGS": "2",
  "FLARUM_MAX_TAGS": "4"
}
```

**Effect:** AI selects 2-4 most suitable tags based on post content

### Case 2: Fixed Tags Posting

**Configuration:**
```json
{
  "FLARUM_URL": "https://forum.example.com",
  "FLARUM_USERNAME": "admin",
  "FLARUM_PASSWORD": "password123",
  "FLARUM_DEFAULT_TAGS": "announcement,important"
}
```

**Effect:** All posts use "announcement" and "important" tags, ideal for batch announcements

## 🔧 How It Works

### Authentication Flow

```
Start Server
    ↓
Check Configuration
    ↓
Has API_TOKEN?
    ↓ Yes              ↓ No
Use Token       Call /api/token to get Token
    ↓                   ↓
    └─────→ Cache Token ←┘
            ↓
    Use Token for Posting
            ↓
        401 Error?
            ↓ Yes
    Clear Cache, Re-get Token
```

### Tag Matching Flow

```
Start Server
    ↓
Fetch All Forum Tags
    ↓
Cache in Memory
    ↓
Display Tag List in Tool Description
    ↓
User Initiates Post Request
    ↓
Default Tags Configured?
    ↓ Yes              ↓ No
Use Default Tags   AI Views Tag List & Selects
    ↓                   ↓
    └─────→ Validate Tags ←┘
            ↓
        Publish Post
```

## 🐛 Troubleshooting

### Issue 1: Token Retrieval Failed

**Error:** `❌ Token retrieval failed (401)`

**Solution:**
- Check if username/password is correct
- Confirm account has posting permissions
- Verify forum supports `/api/token` endpoint

### Issue 2: Tag Not Found

**Error:** `❌ Error: Tag 'xxx' not found`

**Solution:**
- Check tag slug spelling (case-sensitive)
- Confirm tag exists in forum admin
- Restart MCP server to refresh tag cache

### Issue 3: Token Expired

**Message:** `⚠️ Token expired, re-getting...`

**Note:** Program automatically re-gets token, no manual action needed

## 📊 Technical Features

- ✅ **Auto Token Management**: Username/password auto-gets token, auto-refreshes on expiry
- ✅ **Tag Caching**: Fetches tag list on startup and caches, avoiding repeated requests
- ✅ **Smart Matching**: AI selects most suitable tags based on content
- ✅ **Flexible Configuration**: Supports tag quantity range and default values
- ✅ **Backward Compatible**: Fully compatible with legacy API Token configuration
- ✅ **Error Handling**: Comprehensive exception handling and retry mechanisms


## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

MIT License

## 🙏 Acknowledgments

Thanks to all users who use and support this project!

---

**Project URL:** https://github.com/wszdb/FlarumPost-MCP

**Issue Reporting:** Please submit issues on GitHub
