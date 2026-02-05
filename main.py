import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from fastapi import FastAPI, Request
import uvicorn
import os
from dotenv import load_dotenv

from db import db
from handlers.commands import router as commands_router, send_reminders
from handlers.callbacks import router as callbacks_router
from handlers.fsm_handlers import router as fsm_handlers_router

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(
    token=os.getenv("BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрация роутеров
dp.include_router(commands_router)
dp.include_router(callbacks_router)
dp.include_router(fsm_handlers_router)

# FastAPI приложение
app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запуск
    await db.create_pool()
    
    # Установка вебхука
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        webhook_path = "/webhook"
        full_webhook_url = f"{webhook_url}{webhook_path}"
        
        # Удаляем старый вебхук если есть
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Устанавливаем новый вебхук
        await bot.set_webhook(
            url=full_webhook_url,
            drop_pending_updates=True
        )
        logger.info(f"Webhook установлен: {full_webhook_url}")
    else:
        logger.warning("WEBHOOK_URL не указан, используем поллинг")
    
    # Запуск фоновой задачи для напоминаний
    task = asyncio.create_task(send_reminders(bot))
    
    yield
    
    # Завершение
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    await db.close()
    
    # Удаление вебхука
    await bot.delete_webhook()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    """Обработчик вебхука"""
    try:
        update = types.Update(**await request.json())
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"Ошибка обработки обновления: {e}")
    return {"status": "ok"}


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "Telegram Task Planner Bot",
        "status": "running",
        "webhook": "POST /webhook",
        "health": "GET /health"
    }


# Главная функция для запуска
async def main():
    """Главная функция для запуска бота"""
    await db.create_pool()
    
    # Запуск фоновой задачи для напоминаний
    asyncio.create_task(send_reminders(bot))
    
    # Определяем режим работы
    webhook_url = os.getenv("WEBHOOK_URL")
    
    if webhook_url:
        # Режим вебхука
        logger.info("Запуск в режиме вебхука...")
        
        # Запуск FastAPI сервера
        port = int(os.getenv("PORT", 8000))
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    else:
        # Режим поллинга
        logger.info("Запуск в режиме поллинга...")
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
