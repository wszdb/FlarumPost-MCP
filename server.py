#!/usr/bin/env python3
import os
import sys
import json
import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 初始化MCP服务器
app = Server("flarum-mcp")

# 从环境变量获取配置
FLARUM_URL = os.getenv("FLARUM_URL", "")
API_TOKEN = os.getenv("FLARUM_API_TOKEN", "")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用工具"""
    return [
        Tool(
            name="create_discussion",
            description="""在Flarum论坛创建新讨论帖。

📝 内容生成规范（重要）：
1. 字数限制：正文默认不超过250字，除非用户明确指定其他数值
2. 语言风格：必须使用口语化表达，像普通网民聊天一样自然
   - ✅ 推荐：「今天看到个新闻，吓我一跳...」「这事儿太离谱了吧」
   - ❌ 避免：「据悉...」「综上所述...」等书面语
3. 表达原则：能用大白话说清楚就别绕弯子，简单直接最好

示例对比：
❌ 不好：「近日，某小区发生电梯安全事件，相关部门已介入调查。此事引发社会广泛关注。」
✅ 推荐：「刚看到个新闻，小区电梯钢绳被人割了！太吓人了，幸好及时发现没出事...」""",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "帖子标题（建议简短有吸引力，10-30字）"
                    },
                    "content": {
                        "type": "string",
                        "description": "帖子正文内容（默认≤250字，口语化表达，支持Markdown格式）"
                    },
                    "tags": {
                        "type": "string",
                        "description": "标签列表，用逗号分隔（如：shenghuo,xinqing）"
                    }
                },
                "required": ["title", "content", "tags"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """执行工具调用"""
    if name != "create_discussion":
        raise ValueError(f"未知工具: {name}")
    
    # 验证配置
    if not FLARUM_URL or not API_TOKEN:
        return [TextContent(
            type="text",
            text="❌ 错误：环境变量 FLARUM_URL 或 FLARUM_API_TOKEN 未设置"
        )]
    
    try:
        # 获取参数
        title = arguments.get("title")
        content = arguments.get("content")
        tags = arguments.get("tags", "")
        
        # 内容检查提示（不强制，仅提醒）
        content_length = len(content)
        if content_length > 250:
            print(f"⚠️ 提示：正文长度为{content_length}字，建议控制在250字以内", file=sys.stderr)
        
        # 获取标签映射
        headers = {
            "Authorization": f"Token {API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        tag_resp = requests.get(
            f"{FLARUM_URL}/api/tags",
            headers=headers,
            timeout=30
        )
        tag_resp.raise_for_status()
        
        tag_map = {
            t["attributes"]["slug"]: t["id"] 
            for t in tag_resp.json()["data"]
        }
        
        # 解析标签
        tag_data = []
        for tag_slug in tags.split(","):
            tag_slug = tag_slug.strip()
            if not tag_slug:
                continue
            if tag_slug not in tag_map:
                return [TextContent(
                    type="text",
                    text=f"❌ 错误：标签不存在 '{tag_slug}'"
                )]
            tag_data.append({"type": "tags", "id": tag_map[tag_slug]})
        
        # 创建帖子
        post_resp = requests.post(
            f"{FLARUM_URL}/api/discussions",
            headers=headers,
            json={
                "data": {
                    "type": "discussions",
                    "attributes": {
                        "title": title,
                        "content": content
                    },
                    "relationships": {
                        "tags": {"data": tag_data}
                    }
                }
            },
            timeout=30
        )
        
        if post_resp.status_code in (200, 201):
            post_id = post_resp.json()["data"]["id"]
            return [TextContent(
                type="text",
                text=f"""✅ 发帖成功！
📌 帖子ID: {post_id}
📝 标题: {title}
📊 正文字数: {content_length}字
🏷️ 标签: {tags}"""
            )]
        else:
            return [TextContent(
                type="text",
                text=f"❌ 发帖失败 ({post_resp.status_code}): {post_resp.text}"
            )]
            
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"💥 执行错误: {str(e)}"
        )]

async def main():
    """启动MCP服务器"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())