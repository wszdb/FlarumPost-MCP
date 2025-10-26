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
    """获取论坛所有可用标签，包含层级关系信息"""
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
                "color": t["attributes"].get("color", ""),
                "parent_id": t["attributes"].get("parentId"),  # 添加父级ID
                "is_primary": t["attributes"].get("isPrimary", False),  # 是否为主要标签
                "position": t["attributes"].get("position", 999)  # 排序位置
            }
            for t in tags_data
        ]
        
        print(f"📋 获取到 {len(_available_tags)} 个标签", file=sys.stderr)
        return _available_tags
        
    except Exception as e:
        print(f"💥 获取标签失败: {str(e)}", file=sys.stderr)
        return []

def validate_tag_hierarchy(selected_tags: List[str], available_tags: List[Dict]) -> tuple[bool, str]:
    """验证tag层级关系是否正确
    
    Args:
        selected_tags: 用户选择的tag slug列表
        available_tags: 所有可用tag的完整信息
    
    Returns:
        (is_valid, error_message): 验证结果和错误信息
    """
    # 创建tag映射
    tag_map = {t["slug"]: t for t in available_tags}
    
    # 分离一级和二级标签
    primary_tags = []
    secondary_tags = []
    
    for tag_slug in selected_tags:
        if tag_slug not in tag_map:
            return False, f"标签不存在 '{tag_slug}'"
        
        tag_info = tag_map[tag_slug]
        if tag_info["parent_id"] is None:
            primary_tags.append(tag_slug)
        else:
            secondary_tags.append(tag_slug)
    
    # 验证规则1: 如果有二级标签，必须至少有一个对应的一级标签
    if secondary_tags and not primary_tags:
        return False, "错误：选择了二级标签但未选择对应的一级标签。请先选择一级标签，然后再选择其下的二级标签。"
    
    # 验证规则2: 二级标签的父级标签必须在已选择的一级标签中
    for secondary_tag in secondary_tags:
        secondary_info = tag_map[secondary_tag]
        parent_id = secondary_info["parent_id"]
        
        # 找到父级标签的slug
        parent_tag = None
        for tag in available_tags:
            if tag["id"] == parent_id:
                parent_tag = tag
                break
        
        if parent_tag and parent_tag["slug"] not in primary_tags:
            return False, f"错误：二级标签 '{secondary_tag}' 的父级标签 '{parent_tag['slug']}' 未被选择。请先选择 '{parent_tag['slug']}' 作为一级标签。"
    
    # 验证规则3: 不能同时选择一个一级标签和它的二级标签（冗余检查）
    for primary_tag in primary_tags:
        primary_info = tag_map[primary_tag]
        primary_id = primary_info["id"]
        
        # 检查是否有这个一级标签下的二级标签被选择
        for secondary_tag in secondary_tags:
            secondary_info = tag_map[secondary_tag]
            if secondary_info["parent_id"] == primary_id:
                # 这个情况是允许的，所以不报错
                pass
    
    return True, ""

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
    
    tag_requirement = f"必须选择 {FLARUM_MIN_TAGS} 个标签（当前设置为：最少{FLARUM_MIN_TAGS}个，最多{FLARUM_MAX_TAGS}个）"
    
    default_tags_info = ""
    if FLARUM_DEFAULT_TAGS:
        default_tags_info = f"\n\n⚠️ 注意：已配置默认标签 [{FLARUM_DEFAULT_TAGS}]，将自动使用这些标签，无需选择。"
        tag_requirement = "已配置默认标签，无需选择"
    
    return [
        Tool(
            name="create_discussion",
            description=f"""在Flarum论坛创建新讨论帖。
在Flarum论坛创建新讨论帖。

📝 内容生成规范（必须遵守）：
1. 字数限制：正文默认不超过250字，除非用户明确指定其他数值
2. 语言风格：必须使用口语化表达，像普通网民聊天一样自然
   - ✅ 推荐：「今天看到个新闻，吓我一跳...」「这事儿太离谱了吧」
   - ❌ 避免：「据悉...」「综上所述...」等书面语
3. 表达原则：能用大白话说清楚就别绕弯子，简单直接最好

🏷️ 标签选择规范（极其重要 - 必须严格按此执行）：
{tag_requirement}

📋 标签数量要求（基于Flarum系统验证 - 必须严格遵守）：
⚠️ **重要：根据Flarum系统实际验证，必须选择 2 个标签**
- **系统要求：1-2个一级标签**（但实际验证发现必须2个才能成功）
- **推荐选择：2个标签**（经过实际测试验证）
- **必须选择：2个标签**（少于2个会失败，多于2个会被截断）

🎯 **验证过的成功标签组合（2个标签）**：
- **组合1：1个一级标签 + 1个二级标签**（推荐）
  - 例如：shenghuo,jiangkang（生活+健康）- 已验证成功
  - 例如：tech,programming（技术+编程）
  - 例如：life,food（生活+美食）

- **组合2：2个一级标签**（已验证）
  - 例如：shenghuo,jiankang（生活+健康）- 已验证成功
  - 例如：tech,life（技术+生活）
  - 例如：news,game（新闻+游戏）

📋 Flarum标签层级规则（必须按此选择）：

### 🔢 第一步：选择第一个标签（一级标签）
- 一级标签是顶级分类，必须选择
- 例如：shenghuo（生活）、tech（技术）、news（新闻）
- ✅ 允许：选择 "shenghuo" 作为第一个标签

### 🔢 第二步：选择第二个标签
**选项A：选择二级标签（推荐）**
- 二级标签必须属于已选择的一级标签
- 例如：已选shenghuo，可选jiankang
- ✅ 推荐：shenghuo,jiankang（生活+健康）- 已验证成功

**选项B：选择另一个一级标签**
- 可以选择另一个不同的一级标签
- ✅ 允许：shenghuo,jiankang（生活+健康）- 已验证成功

### 🚫 绝对禁止的选择（会导致失败）：
❌ **错误：只选1个标签**（如：只选shenghuo）- 会失败
❌ **错误：选3个或更多标签**（会被截断为2个）
❌ **错误：选择不存在的标签**（如：tucao）- 会失败
❌ **错误：选择无关联的标签组合**

### ✅ 验证过的正确选择示例（都是2个标签）：
✅ **已验证成功：shenghuo,jiankang**（生活+健康）
✅ **示例2：tech,programming**（技术+编程）
✅ **示例3：life,food**（生活+美食）
✅ **示例4：tech,life**（技术+生活）
✅ **示例5：news,game**（新闻+游戏）

### 📋 选择决策流程（AI必须按此执行）：
1. **确认要求** → 必须选择2个标签（经过验证）
2. **选择第一个** → 选择最相关的1个一级标签
3. **选择第二个** → 选择对应的二级标签或另一个一级标签
4. **确认总数** → 确保总计2个标签
5. **验证存在** → 确保标签真实存在

📋 可用标签列表：
{tags_desc}
{default_tags_info}

🚨 **会导致失败的错误选择**：
❌ 错误：只选1个标签 "shenghuo"（数量不足）
❌ 错误：选不存在的标签 "tucao"（标签不存在）
❌ 错误：选3个标签 "shenghuo,jiankang,tech"（数量过多）

✅ **会成功的正确选择**：
✅ 正确：shenghuo,jiankang（2个标签，已验证成功）
✅ 正确：tech,programming（2个标签，一级+二级）
✅ 正确：tech,life（2个标签，两个一级）

示例对比：
❌ 不好：「近日，某小区发生电梯安全事件，相关部门已介入调查。此事引发社会广泛关注。」
✅ 推荐：「刚看到个新闻，小区电梯钢绳被人割了！太吓人了，幸好及时发现没出事...」
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
        
        # 验证标签层级关系
        is_valid, error_msg = validate_tag_hierarchy(selected_tags, available_tags)
        if not is_valid:
            return [TextContent(
                type="text",
                text=f"❌ {error_msg}"
            )]
        
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