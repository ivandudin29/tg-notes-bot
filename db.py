import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def create_pool(self):
        """Создание пула подключений к БД"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        # Конвертируем URL для asyncpg если нужно
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        self.pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        await self.init_tables()
    
    async def init_tables(self):
        """Инициализация таблиц в БД"""
        async with self.pool.acquire() as conn:
            # Создание таблицы проектов
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Создание таблицы задач
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    description TEXT,
                    deadline TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                    status TEXT DEFAULT 'активно',
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Создание индексов для оптимизации
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline)
            """)
    
    # Методы для работы с проектами
    async def create_project(self, user_id: int, name: str, description: Optional[str] = None) -> int:
        """Создание нового проекта"""
        async with self.pool.acquire() as conn:
            project_id = await conn.fetchval("""
                INSERT INTO projects (user_id, name, description)
                VALUES ($1, $2, $3)
                RETURNING id
            """, user_id, name, description)
            return project_id
    
    async def get_user_projects(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение всех проектов пользователя"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name, description
                FROM projects
                WHERE user_id = $1
                ORDER BY created_at DESC
            """, user_id)
            return [dict(row) for row in rows]
    
    async def get_project(self, project_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение проекта по ID с проверкой пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, name, description
                FROM projects
                WHERE id = $1 AND user_id = $2
            """, project_id, user_id)
            return dict(row) if row else None
    
    async def update_project(self, project_id: int, user_id: int, name: str, description: Optional[str] = None) -> bool:
        """Обновление проекта"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE projects
                SET name = $1, description = $2
                WHERE id = $3 AND user_id = $4
            """, name, description, project_id, user_id)
            return "UPDATE 1" in result
    
    async def delete_project(self, project_id: int, user_id: int) -> bool:
        """Удаление проекта"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM projects
                WHERE id = $1 AND user_id = $2
            """, project_id, user_id)
            return "DELETE 1" in result
    
    # Методы для работы с задачами
    async def create_task(self, project_id: int, title: str, description: Optional[str],
                         deadline: datetime, comment: Optional[str] = None) -> int:
        """Создание новой задачи"""
        async with self.pool.acquire() as conn:
            task_id = await conn.fetchval("""
                INSERT INTO tasks (project_id, title, description, deadline, comment)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, project_id, title, description, deadline, comment)
            return task_id
    
    async def get_project_tasks(self, project_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Получение всех задач проекта с проверкой владельца"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT t.id, t.title, t.description, t.deadline, t.status, t.comment
                FROM tasks t
                JOIN projects p ON t.project_id = p.id
                WHERE t.project_id = $1 AND p.user_id = $2
                ORDER BY t.deadline ASC
            """, project_id, user_id)
            return [dict(row) for row in rows]
    
    async def get_task(self, task_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение задачи по ID с проверкой пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT t.id, t.project_id, t.title, t.description, 
                       t.deadline, t.status, t.comment
                FROM tasks t
                JOIN projects p ON t.project_id = p.id
                WHERE t.id = $1 AND p.user_id = $2
            """, task_id, user_id)
            return dict(row) if row else None
    
    async def update_task_status(self, task_id: int, user_id: int, status: str) -> bool:
        """Обновление статуса задачи"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE tasks
                SET status = $1
                WHERE id = $2 AND project_id IN (
                    SELECT id FROM projects WHERE user_id = $3
                )
            """, status, task_id, user_id)
            return "UPDATE 1" in result
    
    async def update_task_deadline(self, task_id: int, user_id: int, deadline: datetime) -> bool:
        """Обновление дедлайна задачи"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE tasks
                SET deadline = $1
                WHERE id = $2 AND project_id IN (
                    SELECT id FROM projects WHERE user_id = $3
                )
            """, deadline, task_id, user_id)
            return "UPDATE 1" in result
    
    async def update_task_comment(self, task_id: int, user_id: int, comment: str) -> bool:
        """Обновление комментария задачи"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE tasks
                SET comment = $1
                WHERE id = $2 AND project_id IN (
                    SELECT id FROM projects WHERE user_id = $3
                )
            """, comment, task_id, user_id)
            return "UPDATE 1" in result
    
    async def delete_task(self, task_id: int, user_id: int) -> bool:
        """Удаление задачи"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM tasks
                WHERE id = $1 AND project_id IN (
                    SELECT id FROM projects WHERE user_id = $2
                )
            """, task_id, user_id)
            return "DELETE 1" in result
    
    # Методы для напоминаний
    async def get_upcoming_tasks(self) -> List[Dict[str, Any]]:
        """Получение задач с дедлайном в ближайшие 24 часа"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT t.id, t.title, t.deadline, p.user_id
                FROM tasks t
                JOIN projects p ON t.project_id = p.id
                WHERE t.status = 'активно'
                AND t.deadline > NOW()
                AND t.deadline <= NOW() + INTERVAL '24 hours'
            """)
            return [dict(row) for row in rows]
    
    async def close(self):
        """Закрытие пула подключений"""
        if self.pool:
            await self.pool.close()


# Глобальный экземпляр базы данных
db = Database()
