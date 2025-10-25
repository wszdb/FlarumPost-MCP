#!/usr/bin/env python3
import os
import sys
import json
import requests
from typing import Optional, Dict, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 初始化MCP服务器
app = Server("flarum-mcp")

# 从环境变量获取配置
FLARUM_URL = os.getenv("FLARUM_URL", "")
FLARUM_USERNAME = os.getenv("FLARUM_USERNAME", "")
FLARUM_PASSWORD = os.getenv("FLARUM_PASSWORD", "")
# 兼容旧版 Token 方式
FLARUM_API_TOKEN = os.getenv("FLARUM_API_TOKEN", "")

# TAG 配置
FLARUM_MIN_TAGS = int(os.getenv("FLARUM_MIN_TAGS", "1"))
FLARUM_MAX_TAGS = int(os.getenv("FLARUM_MAX_TAGS", "3"))
FLARUM_DEFAULT_TAGS = os.getenv("FLARUM_DEFAULT_TAGS", "")

# 全局认证信息缓存
_api_token: Optional[str] = None
_available_tags: Optional[List[Dict]] = None


def get_api_token() -> Optional[str]:
    """使用用户名密码获取 API Token"""
    global _api_token
    
    # 如果已经有 token，直接返回
    if _api_token:
        return _api_token
    
    # 如果配置了环境变量 token，直接使用
    if FLARUM_API_TOKEN:
        _api_token = FLARUM_API_TOKEN
        print(f"✅ 使用配置的 API Token", file=sys.stderr)
        return _api_token
    
    if not FLARUM_URL or not FLARUM_USERNAME or not FLARUM_PASSWORD:
        print("⚠️ 警告：未配置用户名密码或 API Token", file=sys.stderr)
        return None
    
    try:
        print(f"🔐 正在获取 API Token: {FLARUM_USERNAME}...", file=sys.stderr)
        
        # 直接调用 /api/token 接口
        token_resp = requests.post(
            f"{FLARUM_URL}/api/token",
            headers={"Content-Type": "application/json"},
            json={
                "identification": FLARUM_USERNAME,
                "password": FLARUM_PASSWORD
            },
            timeout=30
        )
        
        if token_resp.status_code == 200:
            data = token_resp.json()
            _api_token = data.get("token")
            if _api_token:
                print(f"✅ 成功获取 API Token: {_api_token[:10]}...", file=sys.stderr)
                return _api_token
            else:
                print(f"❌ 响应中未找到 token 字段: {data}", file=sys.stderr)
                return None
        else:
            print(f"❌ 获取 Token 失败 ({token_resp.status_code}): {token_resp.text}", file=sys.stderr)
            return None
            
    except Exception as e:
        import traceback
        print(f"💥 获取 Token 异常: {str(e)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return None


def get_auth_headers() -> Dict[str, str]:
    """获取认证 headers"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    token = get_api_token()
    if token:
        headers["Authorization"] = f"Token {token}"
    
    return headers


def fetch_available_tags() -> List[Dict]:
    """获取论坛所有可用标签"""
    global _available_tags
    
    if _available_tags is not None:
        return _available_tags
    
    try:
        headers = get_auth_headers()
        
        tag_resp = requests.get(
            f"{FLARUM_URL}/api/tags",
            headers=headers,
            timeout=30
        )
        
        if tag_resp.status_code == 401:
            # Token 失效，清除缓存重新获取
            print("⚠️ Token 失效，重新获取...", file=sys.stderr)
            global _api_token
            _api_token = None
            headers = get_auth_headers()
            tag_resp = requests.get(
                f"{FLARUM_URL}/api/tags",
                headers=headers,
                timeout=30
            )
        
        tag_resp.raise_for_status()
        
        tags_data = tag_resp.json()["data"]
        _available_tags = [
            {
                "id": t["id"],
                "slug": t["attributes"]["slug"],
                "name": t["attributes"]["name"],
                "description": t["attributes"].get("description", ""),
                "color": t["attributes"].get("color", "")
            }
            for t in tags_data
        ]
        
        print(f"📋 获取到 {len(_available_tags)} 个标签", file=sys.stderr)
        return _available_tags
        
    except Exception as e:
        print(f"💥 获取标签失败: {str(e)}", file=sys.stderr)
        return []


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用工具"""
    
    tags = fetch_available_tags()
    
    tags_desc = "\n".join([
        f"  • {t['slug']} - {t['name']}" + (f" ({t['description']})" if t['description'] else "")
        for t in tags[:20]
    ])
    
    if len(tags) > 20:
        tags_desc += f"\n  ... 还有 {len(tags) - 20} 个标签"
    
    tag_requirement = f"请选择 {FLARUM_MIN_TAGS}-{FLARUM_MAX_TAGS} 个最合适的标签"
    
    default_tags_info = ""
    if FLARUM_DEFAULT_TAGS:
        default_tags_info = f"\n\n⚠️ 注意：已配置默认标签 [{FLARUM_DEFAULT_TAGS}]，将自动使用这些标签，无需选择。"
        tag_requirement = "已配置默认标签，无需选择"
    
    return [
        Tool(
            name="create_discussion",
            description=f"""在Flarum论坛创建新讨论帖。

📝 内容生成规范（重要）：
1. 字数限制：正文默认不超过250字，除非用户明确指定其他数值
2. 语言风格：必须使用口语化表达，像普通网民聊天一样自然
   - ✅ 推荐：「今天看到个新闻，吓我一跳...」「这事儿太离谱了吧」
   - ❌ 避免：「据悉...」「综上所述...」等书面语
3. 表达原则：能用大白话说清楚就别绕弯子，简单直接最好

🏷️ 标签选择规范：
{tag_requirement}

📋 可用标签列表：
{tags_desc}
{default_tags_info}

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
                        "description": f"标签列表，用逗号分隔的 slug（如：shenghuo,xinqing）。{tag_requirement}。如果已配置默认标签则可以留空。"
                    }
                },
                "required": ["title", "content"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """执行工具调用"""
    if name != "create_discussion":
        raise ValueError(f"未知工具: {name}")
    
    if not FLARUM_URL:
        return [TextContent(
            type="text",
            text="❌ 错误：环境变量 FLARUM_URL 未设置"
        )]
    
    if not FLARUM_API_TOKEN and (not FLARUM_USERNAME or not FLARUM_PASSWORD):
        return [TextContent(
            type="text",
            text="❌ 错误：请配置 FLARUM_USERNAME + FLARUM_PASSWORD 或 FLARUM_API_TOKEN"
        )]
    
    try:
        title = arguments.get("title")
        content = arguments.get("content")
        tags_input = arguments.get("tags", "").strip()
        
        content_length = len(content)
        if content_length > 250:
            print(f"⚠️ 提示：正文长度为{content_length}字，建议控制在250字以内", file=sys.stderr)
        
        # 处理标签
        selected_tags = []
        
        if FLARUM_DEFAULT_TAGS:
            selected_tags = [t.strip() for t in FLARUM_DEFAULT_TAGS.split(",") if t.strip()]
            print(f"🏷️ 使用默认标签: {selected_tags}", file=sys.stderr)
        elif tags_input:
            selected_tags = [t.strip() for t in tags_input.split(",") if t.strip()]
        else:
            return [TextContent(
                type="text",
                text="❌ 错误：未配置默认标签且未提供标签参数"
            )]
        
        if len(selected_tags) < FLARUM_MIN_TAGS:
            return [TextContent(
                type="text",
                text=f"❌ 错误：标签数量不足，至少需要 {FLARUM_MIN_TAGS} 个，当前只有 {len(selected_tags)} 个"
            )]
        
        if len(selected_tags) > FLARUM_MAX_TAGS:
            print(f"⚠️ 标签过多，自动截取前 {FLARUM_MAX_TAGS} 个", file=sys.stderr)
            selected_tags = selected_tags[:FLARUM_MAX_TAGS]
        
        # 获取标签映射
        available_tags = fetch_available_tags()
        tag_map = {t["slug"]: t["id"] for t in available_tags}
        
        tag_data = []
        for tag_slug in selected_tags:
            if tag_slug not in tag_map:
                return [TextContent(
                    type="text",
                    text=f"❌ 错误：标签不存在 '{tag_slug}'。可用标签: {', '.join(list(tag_map.keys())[:10])}"
                )]
            tag_data.append({"type": "tags", "id": tag_map[tag_slug]})
        
        # 获取认证信息
        headers = get_auth_headers()
        
        print(f"📤 准备发帖...", file=sys.stderr)
        print(f"   标题: {title}", file=sys.stderr)
        print(f"   标签: {selected_tags}", file=sys.stderr)
        
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
        
        # 处理 Token 失效
        if post_resp.status_code == 401:
            print(f"⚠️ Token 失效，重新获取后重试...", file=sys.stderr)
            global _api_token
            _api_token = None
            headers = get_auth_headers()
            
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
            tags_str = ", ".join(selected_tags)
            return [TextContent(
                type="text",
                text=f"""✅ 发帖成功！
📌 帖子ID: {post_id}
📝 标题: {title}
📊 正文字数: {content_length}字
🏷️ 标签: {tags_str} (共{len(selected_tags)}个)
🔗 链接: {FLARUM_URL}/d/{post_id}"""
            )]
        else:
            error_detail = post_resp.text
            print(f"❌ 发帖失败详情: {error_detail}", file=sys.stderr)
            return [TextContent(
                type="text",
                text=f"❌ 发帖失败 ({post_resp.status_code}): {error_detail}"
            )]
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(error_detail, file=sys.stderr)
        return [TextContent(
            type="text",
            text=f"💥 执行错误: {str(e)}"
        )]


async def main():
    """启动MCP服务器"""
    # 启动时获取 Token
    get_api_token()
    
    # 预加载标签列表
    fetch_available_tags()
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())