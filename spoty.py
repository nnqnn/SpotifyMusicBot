import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
import asyncio
import config

BOT_TOKEN = config.BOT_TOKEN
SPOTIPY_CLIENT_ID = config.SPOTIPY_CLIENT_ID
SPOTIPY_CLIENT_SECRET = config.SPOTIPY_CLIENT_SECRET
SPOTIPY_REDIRECT_URI = config.SPOTIPY_REDIRECT_URI
YOUR_CHANNEL = config.YOUR_CHANNEL
USERS = []

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Настройка авторизации Spotify
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                        client_secret=SPOTIPY_CLIENT_SECRET,
                        redirect_uri=SPOTIPY_REDIRECT_URI,
                        scope="user-read-currently-playing")

sp = spotipy.Spotify(auth_manager=sp_oauth)

async def get_current_track():
    """Получение текущего трека из Spotify."""
    try:
        track = sp.currently_playing()
        if track and track['is_playing']:
            track_name = track['item']['name']
            artists = ", ".join(artist['name'] for artist in track['item']['artists'])
            cover_url = track['item']['album']['images'][0]['url']
            track_url = track['item']['external_urls']['spotify']
            return {
                "name": track_name,
                "artists": artists,
                "cover_url": cover_url,
                "track_url": track_url
            }
        return None
    except Exception as e:
        print(f"Ошибка получения трека: {e}")
        return None

async def send_message_every_minute():
    """Отправка обновлений о текущем треке."""
    while True:
        track_info = await get_current_track()
        if track_info:
            message = f"Слушает сейчас: {track_info['artists']} - {track_info['name']}\n[Ссылка на Spotify]({track_info['track_url']})"
            for user in USERS:
                chat_id = user['chat_username']
                message_id = user['message_id']
                try:
                    message_text = f"Слушает сейчас: {track_info['artists']} - {track_info['name']}."
                    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    inline_btn_1 = InlineKeyboardButton(
                        'Песня в Spotify', url=track_info['track_url'])
                    inline_keyboard = InlineKeyboardMarkup(row_width=2).add(
                        inline_btn_1)
                    
                    message_text_with_time = f"{message_text}\nВремя (по Москве): {current_time}"

                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=message_text_with_time,
                        reply_markup=inline_keyboard
                    )
                except Exception as e:
                    print(f"Ошибка отправки сообщения: {e}")
        await asyncio.sleep(10)

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    """Обработка команды /start."""
    pass
    track_info = await get_current_track()
    if track_info:
        message_reply = await message.reply("Получение информации...")
        await bot.send_photo(
            message.chat.id, 
            photo=track_info['cover_url'], 
            caption=f"Слушает сейчас: {track_info['artists']} - {track_info['name']}\n[Ссылка на Spotify]({track_info['track_url']})",
            parse_mode='Markdown'
        )
        await message_reply.delete()
    else:
        await message.reply("Ничего сейчас не играет.")

@dp.message_handler(commands=['subscribe'])
async def subscribe_user(message: types.Message):
    """Подписка пользователя на обновления."""
    USERS.append({'chat_username': message.chat.id, 'message_id': message.message_id})
    await message.reply("Вы подписаны на обновления!")

async def on_startup(dp: Dispatcher) -> None:
    message = await bot.send_message(chat_id=YOUR_CHANNEL, text='Бот запущен')
    USERS.append({'chat_username': YOUR_CHANNEL,
                  'message_id': message.message_id})

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(send_message_every_minute())
    executor.start_polling(dp, on_startup=on_startup, loop=loop)