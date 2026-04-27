from fastapi import APIRouter
from app.common.memory_manager import memory_manager

router = APIRouter()


@router.get("/contexts")
async def list_memory_contexts():
    """获取所有记忆上下文列表"""
    contexts = memory_manager.list_contexts()
    return {"contexts": contexts}


@router.get("/contexts/{context_id}")
async def get_memory_context(context_id: str):
    """获取特定记忆上下文"""
    context = memory_manager.get_context(context_id)
    if context:
        return {"context": context}
    return {"context": None, "message": "记忆上下文不存在"}


@router.post("/contexts")
async def create_memory_context(context_id: str, name: str, description: str = ""):
    """创建新的记忆上下文"""
    success = memory_manager.create_context(context_id, name, description)
    if success:
        return {"success": True, "message": "记忆上下文创建成功"}
    return {"success": False, "message": "记忆上下文已存在或创建失败"}


@router.delete("/contexts/{context_id}")
async def delete_memory_context(context_id: str):
    """删除记忆上下文"""
    success = memory_manager.delete_context(context_id)
    if success:
        return {"success": True, "message": "记忆上下文删除成功"}
    return {"success": False, "message": "删除记忆上下文失败"}


@router.put("/contexts/{context_id}/description")
async def update_memory_context_description(context_id: str, description: str):
    """更新记忆上下文描述"""
    success = memory_manager.update_context_description(context_id, description)
    if success:
        return {"success": True, "message": "描述更新成功"}
    return {"success": False, "message": "描述更新失败"}


@router.get("/contents/{context_id}")
async def get_memory_contents(context_id: str, content_type: str = None):
    """获取特定上下文的记忆内容"""
    contents = memory_manager.get_memory_contents(context_id, content_type)
    return {"contents": contents}
