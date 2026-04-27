import os
import time
import sqlite3
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
# 导入包
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, AIMessageChunk
from langchain_tavily import TavilySearch
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.common.logger import logger
from app.common.memory_manager import memory_manager
# 定义搜索工具
web_search = TavilySearch(
    max_results=5,
    topic="general"
)
# 多模态模型
model = init_chat_model(
     model="qwen3.6-plus-2026-04-02" ,
     model_provider="openai",
     api_key=os.getenv("DASHSCOPE_API_KEY"),
     base_url=os.getenv("DASHSCOPE_BASE_URL")
)
# 系统提示语
system_prompt="""
 你是一名私人厨师。收到用户提供的食材照片或清单后，请按以下流程操作：
1.识别和评估食材：若用户提供照片，首先辨识所有可见食材。基于食材的外观状态，评估其新鲜度与可用量，整理出一份"当前可用食材清单"。
2.智能食谱检索：优先调用 web_search 工具，以"可用食材清单"为核心关键词，查找可行菜谱。
3.多维度评估与排序：从营养价值和制作难度两个维度对检索到的候选食谱进行量化打分，并根据得分排序，制作简单且营养丰富的排名靠前。
4.结构化方案输出：把排序后的食谱整理为一份结构清晰的建议报告，要包含食谱信息、得分、推荐理由、食谱的参考图片，帮助用户快速做出决策。

请严格按照流程，优先调用 web_search 工具搜索食谱，搜索不到的情况下才能自己发挥。
"""

def _create_agent_with_checkpointer(checkpointer):
    """创建带有checkpointer的agent"""
    return create_agent(
        model=model,
        tools=[web_search],
        system_prompt=system_prompt,
        checkpointer=checkpointer
    )

# 流式执行智能体
# 流式对话
async def search_recipes(prompt: str, image: str, thread_id: str):
    """调用agent搜索食谱"""
    logger.info(f"[用户]: {prompt}, image: {image}, thread_id: {thread_id}")
    try:
        # 检查并创建记忆上下文（如果不存在）
        context_info = memory_manager.get_context(thread_id)
        if not context_info:
            memory_manager.create_context(
                context_id=thread_id,
                name=f"烹饪会话_{thread_id[:8]}",
                description=f"食材咨询会话，开始于{time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        # 判断是否有图片，封装不同格式的消息
        if not image or image.strip() == "":
            message = HumanMessage(content=prompt)
        else:
            message = HumanMessage(content=[
                {"type": "image", "url": image},
                {"type": "text", "text": prompt}
            ])

        async with AsyncSqliteSaver.from_conn_string("personal_chief.db") as checkpointer:
            agent = _create_agent_with_checkpointer(checkpointer)

            # 流式调用Agent
            full_response = ""
            async for chunk, metadata in agent.astream(
                {"messages": [message]},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages"
            ):
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    content = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                    full_response += content
                    yield content

            # 存储对话到记忆内容
            if full_response.strip():
                # 存储用户输入
                memory_manager.add_memory_content(
                    context_id=thread_id,
                    content_type="user_input",
                    content_data={"prompt": prompt, "image": image}
                )
                # 存储AI回复
                memory_manager.add_memory_content(
                    context_id=thread_id,
                    content_type="assistant_reply",
                    content_data={"response": full_response}
                )

    except Exception as e:
        logger.error(f"\n[错误]: {str(e)}")
        yield "信息检索失败，试试看手动输入食物列表？"

# 清空会话
def clear_messages(thread_id: str):
    """清空会话"""
    logger.info(f"清空历史消息，thread_id: {thread_id}")
    conn = sqlite3.connect("personal_chief.db")
    conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
    conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
    conn.commit()
    conn.close()

# 查询会话历史
def get_messages(thread_id: str) -> list[dict[str, str]]:
    """获取会话历史"""
    logger.info(f"获取历史消息，thread_id: {thread_id}")
    import msgpack

    def _ext_hook(code, data):
        if code == 5:
            return msgpack.unpackb(data, raw=False, ext_hook=_ext_hook)
        return msgpack.ExtType(code, data)

    conn = sqlite3.connect("personal_chief.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT checkpoint FROM checkpoints WHERE thread_id = ? ORDER BY checkpoint_id DESC LIMIT 1",
        (thread_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        return []

    try:
        data = msgpack.unpackb(row[0], raw=False, ext_hook=_ext_hook)
    except Exception:
        return []

    msgs = data.get("channel_values", {}).get("messages", [])
    if not msgs:
        return []

    result = []
    for m in msgs:
        if not isinstance(m, list) or len(m) < 3:
            continue
        kwargs = m[2]
        if not isinstance(kwargs, dict):
            continue
        content = kwargs.get("content", "")
        msg_type = kwargs.get("type", "")
        if isinstance(content, list):
            content = " ".join(
                c.get("text", "") for c in content
                if isinstance(c, dict) and c.get("type") == "text"
            )
        if content:
            if msg_type == "human":
                result.append({"role": "user", "content": content})
            elif msg_type == "ai":
                result.append({"role": "assistant", "content": content})

    return result


def get_memory_contents(thread_id: str, content_type: str = None) -> list[dict]:
    """获取特定记忆上下文的内容"""
    return memory_manager.get_memory_contents(thread_id, content_type)


def get_all_memory_contexts() -> list[dict]:
    """获取所有记忆上下文"""
    return memory_manager.list_contexts()
