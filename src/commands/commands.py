import requests
from decouple import config

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from main import START_ROUTES, SETTING_USERNAME, TYPING, USERNAME
from src.db.database import db
from src.db.utils import *

s = requests.Session()
s.params = { 'api_key': config('LAST_FM_API_KEY'), 'format': 'json' }

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """Send a message when the command /start is issued."""
  # db.connect(reuse_if_open=True)
  
  # chat_id = update.message.chat_id
  # current_user = update.effective_user
    
  # if not user_exists(current_user.id):
  #   create_user(id=current_user.id, username=current_user.username, first_name=current_user.first_name, last_name=current_user.last_name)

  keyboard = [
    [
      InlineKeyboardButton("Last.FM username", callback_data=str(SETTING_USERNAME)),
      InlineKeyboardButton("Get Top Tracks", callback_data=str('asd')),
    ],
    [
      InlineKeyboardButton("Get Top Albums", callback_data=str('dsa')),
      InlineKeyboardButton("Get Top Artists", callback_data=str('sad')),
    ]
  ]
  
  reply_markup = InlineKeyboardMarkup(keyboard)
  await update.message.reply_text("Hi! What do you want to do?", reply_markup=reply_markup)
  
  return START_ROUTES

  # await update.message.reply_text("Hi! Use /set <last_fm_username> to set last fm user name")

  # await context.bot.send_message(
  #   text="", 
  #   chat_id=chat_id
  # )
  

async def set_username_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """Set a username"""
  query = update.callback_query
  text = 'Type in Last.FM username'
  
  await query.answer()
  await query.edit_message_text(text=text)
  
  return TYPING
  
async def save_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_data = context.user_data
  user_data[USERNAME] = update.message.text

  return await start_command(update, context)
  
# async def set_username_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#   """Set a username"""
#   if len(context.args) == 0:
#     await update.message.reply_text(f"You have not provided any username. Use /set <last_fm_username> to set last fm user name")
#     return
    
#   username = context.args[0]
  
#   context.user_data['username'] = username
  
#   await update.message.reply_text(f"Good! Username {username} is set. Now you can get data for this user. Run /toptracks, for example")
  
#   return

async def get_top_tracks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """Get top tracks for a period of time"""
  # period = context.args[0]
  # print(context.args)
  
  user = context.user_data.get('username')
  
  if user == None:
    await update.message.reply_text(f"You have not provided any username. Use /set <last_fm_username> to set last fm user name")
    return
  
  response = s.get(f"{config('LAST_FM_BASE_URL')}", params = { 'user': user, 'method': 'user.gettoptracks', 'period': '7day' } )
  data = response.json()  
  print(data)
  
  
  # context.user_data[username] = username
  
  # await update.message.reply_text(f"Good! Username {username} is set. Now you can get data for this user. Run /toptracks, for example")
  
  return

# async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#   """Send a message when the command /help is issued."""
#   # await update.message.reply_text("Help!")
#   chat_id = update.message.chat_id
  
#   await context.bot.send_message(
#       text="/start -> Активировать бота \n/play -> Активировать игрока \n/throw -> Бросить снежок \n/list -> Список игроков \n/stats -> Статистика\n", 
#       chat_id=chat_id
#     )