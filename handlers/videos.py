import datetime
from typing import List
from etc.keyboards import Keyboards
from etc.texts import BOT_TEXTS
from loader import bot, dp
from aiogram.types import Message, CallbackQuery
from models.etc import LearngingVideo
from models.tg_user import TgUser
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from pymodm.errors import DoesNotExist


@dp.message_handler(Text(BOT_TEXTS.LearningVideos), state="*")
async def start_cmd(m:Message, state:FSMContext=None):
    if state:
        await state.finish()
    videos: List[LearngingVideo] = LearngingVideo.objects.all()
    if list(videos) == []:
        await m.answer("📽️❌ Пока что администрация не добавила видео")
        return
    await m.answer("📽️ Выберите видео", reply_markup=Keyboards.LearningVideo.videos_main_menu(videos))
    

@dp.callback_query_handler(lambda c: c.data.startswith('|video:'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    stateData = {} if state is None else await state.get_data()
    
    if actions[0] == "open":
        videoId = actions[1]
        try:
            video: LearngingVideo = LearngingVideo.objects.get({"id": videoId})
        except DoesNotExist:
            await c.answer("❌ Это видео недоступно")
            return
        
        await c.message.answer_video(video.tg_file_id, caption=f"📽️ {video.title}")