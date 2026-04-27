from fastapi import APIRouter
from app.models.schemas import ChatRequest
from app.agents.person_chef import search_recipes,get_messages,clear_messages, get_memory_contents, get_all_memory_contexts
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.post("/chat/stream")
async def chat_endpoint(request: ChatRequest):
    """流式对话"""
    return StreamingResponse(
        search_recipes(request.message, request.image_url, request.thread_id),
        media_type="text/event-stream"
    )
    
    


@router.get("/chat/messages")
async def get_chat_messages(thread_id: str):
    """获取历史消息"""
    messages = get_messages(thread_id)
    return {"messages": messages}


@router.delete("/chat/messages")
async def clear_chat_messages(thread_id: str):
    """清空历史消息"""
    clear_messages(thread_id)
    return {"success": True}


@router.get("/chat/memory-contexts")
async def list_memory_contexts():
    """获取所有记忆上下文列表"""
    contexts = get_all_memory_contexts()
    return {"contexts": contexts}


@router.get("/chat/memory-contents")
async def get_chat_memory_contents(thread_id: str, content_type: str = None):
    """获取特定记忆上下文的内容"""
    contents = get_memory_contents(thread_id, content_type)
    return {"contents": contents}


@router.post("/chat/memory-contexts")
async def create_memory_context(context_id: str, name: str, description: str = ""):
    """创建新的记忆上下文"""
    from app.agents.person_chef import memory_manager
    success = memory_manager.create_context(context_id, name, description)
    if success:
        return {"success": True, "message": "记忆上下文创建成功"}
    else:
        return {"success": False, "message": "记忆上下文已存在或创建失败"}


@router.delete("/chat/memory-contexts/{context_id}")
async def delete_memory_context(context_id: str):
    """删除记忆上下文"""
    from app.agents.person_chef import memory_manager
    success = memory_manager.delete_context(context_id)
    if success:
        return {"success": True, "message": "记忆上下文删除成功"}
    else:
        return {"success": False, "message": "删除记忆上下文失败"}