# bot.py — создаёт экземпляры бота и диспетчера, не запускает их
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN

# Создаём экземпляры
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())  # FSM-хранилище