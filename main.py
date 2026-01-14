import asyncio
import os
import subprocess
import tempfile
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# ТВОЙ TOKEN от BotFather
BOT_TOKEN = "8586349803:AAG5FgrEtDI1X5PEH_E3jO0bw0K7Wo-Cys0"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class DownloadStates(StatesGroup):
    waiting_url = State()

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "🎥 <b>Video Downloader Bot</b>\n\n"
        "Отправь ссылку на видео:\n"
        "• TikTok\n"
        "• YouTube\n"
        "• Instagram\n"
        "• Twitter/X\n"
        "• Любые другие сайты\n\n"
        "<i>Макс. размер: 50MB</i>",
        parse_mode="HTML"
    )

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "📋 <b>Инструкция:</b>\n\n"
        "1. Отправь ссылку\n"
        "2. Жди обработки (10-60 сек)\n"
        "3. Получи видео\n\n"
        "<b>Поддержка:</b> 2000+ сайтов\n"
        "<b>Формат:</b> MP4 720p max",
        parse_mode="HTML"
    )

@dp.message(F.text.startswith(('https://')))
async def download_video(message: Message):
    await message.answer("⏳ Скачиваю видео...")
    
    # Создаем временную директорию
    with tempfile.TemporaryDirectory() as temp_dir:
        input_file = Path(temp_dir) / "input.txt"
        output_file = Path(temp_dir) / "video.%(ext)s"
        
        # Записываем ссылку в файл (yt-dlp так удобнее)
        input_file.write_text(message.text.strip())
        
        try:
            # Выполняем yt-dlp
            cmd = [
                'yt-dlp',
                '--batch-file', str(input_file),
                '-f', 'best[height<=720][ext=mp4]/best[height<=720]/best',
                '--no-playlist',
                '--embed-subs',
                '-o', str(output_file),
                '--restrict-filenames',
                '--max-filesize', '50M'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=temp_dir
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode()
                if "QUOTA" in error_msg:
                    await message.answer("❌ Видео слишком большое (>50MB)")
                elif "Unable to extract" in error_msg:
                    await message.answer("❌ Не удалось распознать ссылку")
                else:
                    await message.answer(f"❌ Ошибка: {error_msg[:200]}...")
                return
            
            # Ищем скачанный файл
            video_files = list(Path(temp_dir).glob("video.*"))
            if not video_files:
                await message.answer("❌ Файл не найден")
                return
            
            video_file = video_files[0]
            file_size = video_file.stat().st_size
            
            if file_size > 50 * 1024 * 1024:
                await message.answer("❌ Файл слишком большой для Telegram")
                return
            
            # Отправляем видео
            caption = f"✅ <b>Готово!</b>\n📁 {video_file.name}"
            
            with open(video_file, 'rb') as f:
                await message.answer_video(
                    FSInputFile(video_file),
                    caption=caption,
                    parse_mode="HTML",
                    supports_streaming=True
                )
                
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
            logging.error(f"Error: {e}")

@dp.message()
async def unknown(message: Message):
    await message.answer("❓ Отправь <b>ссылку на видео</b>", parse_mode="HTML")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
