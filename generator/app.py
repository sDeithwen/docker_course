import asyncio
import os
import logging
from datetime import datetime
from tortoise import Tortoise, fields
from tortoise.models import Model

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  # убрали %(name)s
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


# Определяем модель сообщения
class Message(Model):
    id = fields.IntField(pk=True)
    text = fields.CharField(max_length=500)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "messages"

    def __str__(self):
        return f"Message(id={self.id}, text={self.text}, created_at={self.created_at})"


async def init_db():
    """Инициализация подключения к БД и создание таблиц"""
    db_url = f"postgres://{os.getenv('DB_USER', 'app_user')}:{os.getenv('DB_PASSWORD', 'app_password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'app_db')}"

    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["__main__"]}
    )

    # Создаём таблицы (если их нет)
    await Tortoise.generate_schemas()
    logger.info("Database initialized and tables created")


async def write_message(message_text: str):
    """Запись сообщения в БД"""
    try:
        message = await Message.create(text=message_text)
        logger.info(f"✅ Message written: ID={message.id}, text='{message_text}'")
        return message
    except Exception as e:
        logger.error(f"❌ Failed to write message: {e}")
        return None


async def get_message_count():
    """Получить количество сообщений в БД"""
    return await Message.all().count()


async def main():
    # Инициализируем БД
    await init_db()

    logger.info("Starting message writer loop...")
    counter = 1

    try:
        while True:
            # Формируем сообщение с timestamp
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message_text = f"Message #{counter} - {current_time}"

            # Пишем в БД
            await write_message(message_text)

            # Показываем статистику
            total = await get_message_count()
            logger.info(f"📊 Total messages in DB: {total}")

            # Ждём 5 секунд
            await asyncio.sleep(5)
            counter += 1


    except KeyboardInterrupt:
        print("\n\n👋 Работа завершена. До свидания!")
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка: {e}")
    finally:
        try:
            # Закрываем соединения с базой данных
            await Tortoise.close_connections()
            logger.info("Соединение с базой данных закрыто")
        except Exception as e:
            # Игнорируем ошибки при закрытии, особенно CancelledError
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Дополнительная защита от KeyboardInterrupt на верхнем уровне
        pass