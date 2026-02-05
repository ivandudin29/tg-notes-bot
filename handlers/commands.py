async def send_reminders(bot):
    """Фоновая задача для отправки напоминаний"""
    while True:
        try:
            tasks = await db.get_upcoming_tasks()
            
            sent_reminders = 0
            for task in tasks:
                try:
                    deadline_str = task['deadline'].strftime('%d.%m.%y %H:%M')
                    reminder_text = (
                        f"❗ Напоминание:\n"
                        f"Задача: «{task['title']}»\n"
                        f"Дедлайн: {deadline_str}"
                    )
                    
                    await bot.send_message(
                        chat_id=task['user_id'],
                        text=reminder_text
                    )
                    sent_reminders += 1
                    
                    # Пауза между отправками, чтобы не превысить лимиты
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Ошибка отправки напоминания пользователю {task.get('user_id')}: {e}")
                    continue
            
            if sent_reminders > 0:
                logger.info(f"Отправлено {sent_reminders} напоминаний")
            
        except Exception as e:
            logger.error(f"Ошибка в задаче напоминаний: {e}")
        
        # Проверяем каждые 5 минут
        await asyncio.sleep(300)
