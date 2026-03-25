import asyncio
import os
import logging
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
    db_url = f"postgres://{os.getenv('DB_USER', 'app_user')}:{os.getenv('DB_PASSWORD', 'app_password')}@{os.getenv('DB_HOST', 'postgres')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'app_db')}"

    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["__main__"]}
    )

    # Создаём таблицы (если их нет)
    await Tortoise.generate_schemas()
    logger.info("База данных инициализирована, таблицы созданы")


async def delete_all_messages():
    """Удалить все сообщения из таблицы"""
    try:
        count = await Message.all().delete()
        logger.info(f"🗑️ Удалено сообщений: {count}")
        return count
    except Exception as e:
        logger.error(f"❌ Ошибка удаления сообщений: {e}")
        return 0


async def write_message(message_text: str):
    """Запись сообщения в БД"""
    try:
        message = await Message.create(text=message_text)
        logger.info(f"✅ Сообщение записано: ID={message.id}, текст='{message_text}'")
        return message
    except Exception as e:
        logger.error(f"❌ Ошибка записи сообщения: {e}")
        return None


async def show_message_count():
    """Показать количество сообщений"""
    try:
        count = await Message.all().count()
        print(f"\n📊 Всего сообщений в базе: {count}\n")
        return count
    except Exception as e:
        logger.error(f"❌ Ошибка получения количества: {e}")
        return 0


async def main():
    # Инициализируем БД (без ожидания, depends_on настроен в docker)
    await init_db()

    print("\n" + "=" * 60)
    print("📝 Консоль управления сообщениями")
    print("=" * 60)
    print("Команды:")
    print("  - Введите любой текст для сохранения в базу данных")
    print("  - !clear - Удалить все сообщения")
    print("  - !show - Показать количество сообщений")
    print("=" * 60 + "\n")

    try:
        while True:
            # Получаем ввод от пользователя
            user_input = input("📝 Введите сообщение (или команду !show / !clear ): \n").strip()

            # Проверяем команды
            if user_input.lower() == '!clear':
                deleted = await delete_all_messages()
                print(f"✅ Удалено сообщений: {deleted}\n")
            elif user_input.lower() == '!show':
                await show_message_count()
            elif user_input:
                # Обычное сообщение - записываем в БД
                await write_message(user_input)
                print(f"✅ Сообщение сохранено!\n")
            else:
                # Пустой ввод - игнорируем
                continue

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
