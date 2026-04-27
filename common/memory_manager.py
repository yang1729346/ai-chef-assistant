import sqlite3
import json
import time
from typing import List, Dict, Optional
from datetime import datetime
from app.common.logger import logger


class MemoryManager:
    """
    多记忆管理器，用于管理不同的对话上下文和记忆
    """
    def __init__(self, db_path: str = "personal_chef.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建记忆上下文表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_contexts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        # 创建记忆标签表（可用于分类记忆）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_id TEXT,
                tag_name TEXT,
                FOREIGN KEY (context_id) REFERENCES memory_contexts(id)
            )
        ''')

        # 创建记忆内容表（可选，用于存储特定记忆内容）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_contents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_id TEXT,
                content_type TEXT,  -- 'recipe', 'ingredient', 'preference', etc.
                content_data TEXT,  -- JSON格式的数据
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (context_id) REFERENCES memory_contexts(id)
            )
        ''')

        conn.commit()
        conn.close()

    def create_context(self, context_id: str, name: str, description: str = "") -> bool:
        """创建新的记忆上下文"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO memory_contexts (id, name, description)
                VALUES (?, ?, ?)
            ''', (context_id, name, description))

            conn.commit()
            conn.close()
            logger.info(f"创建记忆上下文: {context_id} - {name}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"记忆上下文已存在: {context_id}")
            return False
        except Exception as e:
            logger.error(f"创建记忆上下文失败: {str(e)}")
            return False

    def delete_context(self, context_id: str) -> bool:
        """删除记忆上下文"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 删除相关标签
            cursor.execute('DELETE FROM memory_tags WHERE context_id = ?', (context_id,))
            # 删除相关记忆内容
            cursor.execute('DELETE FROM memory_contents WHERE context_id = ?', (context_id,))
            # 删除上下文本身
            cursor.execute('DELETE FROM memory_contexts WHERE id = ?', (context_id,))

            conn.commit()
            conn.close()
            logger.info(f"删除记忆上下文: {context_id}")
            return True
        except Exception as e:
            logger.error(f"删除记忆上下文失败: {str(e)}")
            return False

    def get_context(self, context_id: str) -> Optional[Dict]:
        """获取特定记忆上下文"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, name, description, created_at, updated_at, is_active
            FROM memory_contexts
            WHERE id = ?
        ''', (context_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'created_at': row[3],
                'updated_at': row[4],
                'is_active': bool(row[5])
            }
        return None

    def list_contexts(self) -> List[Dict]:
        """列出所有记忆上下文"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, name, description, created_at, updated_at, is_active
            FROM memory_contexts
            ORDER BY updated_at DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        contexts = []
        for row in rows:
            contexts.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'created_at': row[3],
                'updated_at': row[4],
                'is_active': bool(row[5])
            })

        return contexts

    def add_memory_content(self, context_id: str, content_type: str, content_data: Dict) -> bool:
        """添加记忆内容到特定上下文"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            content_json = json.dumps(content_data, ensure_ascii=False)

            cursor.execute('''
                INSERT INTO memory_contents (context_id, content_type, content_data)
                VALUES (?, ?, ?)
            ''', (context_id, content_type, content_json))

            # 更新上下文更新时间
            cursor.execute('''
                UPDATE memory_contexts SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (context_id,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"添加记忆内容失败: {str(e)}")
            return False

    def get_memory_contents(self, context_id: str, content_type: str = None) -> List[Dict]:
        """获取特定上下文的记忆内容"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if content_type:
            cursor.execute('''
                SELECT content_type, content_data, created_at
                FROM memory_contents
                WHERE context_id = ? AND content_type = ?
                ORDER BY created_at DESC
            ''', (context_id, content_type))
        else:
            cursor.execute('''
                SELECT content_type, content_data, created_at
                FROM memory_contents
                WHERE context_id = ?
                ORDER BY created_at DESC
            ''', (context_id,))

        rows = cursor.fetchall()
        conn.close()

        contents = []
        for row in rows:
            try:
                content_data = json.loads(row[1]) if row[1] else {}
            except json.JSONDecodeError:
                content_data = {'raw_data': row[1]}

            contents.append({
                'content_type': row[0],
                'content_data': content_data,
                'created_at': row[2]
            })

        return contents

    def update_context_description(self, context_id: str, description: str) -> bool:
        """更新记忆上下文描述"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE memory_contexts
                SET description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (description, context_id))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"更新记忆上下文描述失败: {str(e)}")
            return False


# 全局记忆管理实例
memory_manager = MemoryManager()
