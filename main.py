import logging
import requests
from decouple import config
from asyncio import sleep

from telegram.ext import (
  Application, 
  CommandHandler, 
  MessageHandler, 
  filters, 
  ContextTypes, 
  ConversationHandler, 
  CallbackQueryHandler, 
  PicklePersistence
)
from telegram import __version__ as TG_VER
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

# from src.commands.commands import *
from src.db.database import *
from src.db.utils import *


try:
  from telegram import __version_info__
except ImportError:
  __version_info__ = (0,0,0,0,0)
  
if __version_info__ < (20, 0, 0, "alpha", 1):
  raise RuntimeError(
    f"This example is not compatible with your current PTB version {TG_VER}. To view the "
    f"{TG_VER} version of this example, "
    f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
  )

logging.basicConfig(
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

logger = logging.getLogger('peewee')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.WARNING)






SELECTING_USERNAME = 10
SELECTING_FEATURE = 11
SELECTING_ACTION = 12
SETTING_USERNAME = 13
SETTING_FEATURE = 14

(
  TRACKS,
  ALBUMS,
  ARTISTS,
) = map(str, range(15, 18))

SHOWING_USERNAME = 200
SHOWING_RESULTS = 201


# PAGE_RANGE = map(str, range(300, 304))

(
  CURRENT_PAGE,
  FIRST_PAGE,
  NEXT_PAGE,
  PREVIOUS_PAGE
) = map(str, range(300, 304))

# PERIOD_RANGE = map(str, range(51, 57))

(
  PERIOD_WEEK,
  PERIOD_MONTH,
  PERIOD_THREE_MONTH,
  PERIOD_HALF_YEAR,
  PERIOD_YEAR,
  PERIOD_OVERALL
) = map(str, range(51, 57))



lastfm_period_dict = {
  PERIOD_WEEK: '7day',
  PERIOD_MONTH: '1month',
  PERIOD_THREE_MONTH: '3month',
  PERIOD_HALF_YEAR: '6month',
  PERIOD_YEAR: '12month',
  PERIOD_OVERALL: 'overall',
}

lastfm_level_dict = {
  TRACKS: 'user.gettoptracks',
  ALBUMS: 'user.gettopalbums',
  ARTISTS: 'user.gettopartists',
}

user_period_dict = {
  PERIOD_WEEK: 'for 7 days',
  PERIOD_MONTH: 'for 1 month',
  PERIOD_THREE_MONTH: 'for 3 months',
  PERIOD_HALF_YEAR: 'for 6 months',
  PERIOD_YEAR: 'for 1 year',
  PERIOD_OVERALL: 'overall',
}

TYPING = 1
SHOWING = 2
START_OVER = 3 
PERIOD = 4
ERROR = 5
END = ConversationHandler.END

USERNAME = str(100)
TOP_LEVEL = str(101)
TOP_PERIOD = str(102)
RESULTS = str(103)

s = requests.Session()
s.params = { 'api_key': config('LAST_FM_API_KEY'), 'format': 'json', 'limit': 20 }


###### utils
def getTotalLevel(user_data):
  def check(item):
    return user_data.get(TOP_LEVEL) == item
  
  result = list(map(check, [TRACKS, ALBUMS, ARTISTS]))
  return result

def getTotalPage(results, user_data):  
  [isTopTracks, isTopAlbums, isTopArtists] = getTotalLevel(user_data)
  
  if isTopTracks:
    return results['toptracks']['@attr']['totalPages']
  elif isTopAlbums:
    return results['topalbums']['@attr']['totalPages']
  elif isTopArtists:
    return results['topartists']['@attr']['totalPages']
  
######

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """Send a message when the command /start is issued."""  
  db.connect(reuse_if_open=True)
  
  username = context.user_data.get(USERNAME)
  
  if username == None:
    text = "What do you want to do?"
  else:
    text = f"What do you want to do, {username}?"    
  
  current_user = update.effective_user
    
  if not user_exists(current_user.id):
    create_user(id=current_user.id, username=current_user.username, first_name=current_user.first_name, last_name=current_user.last_name)

  
  keyboard = [
    [
      InlineKeyboardButton("Last.FM username", callback_data=str(SHOWING_USERNAME)),
      InlineKeyboardButton("Get Top Tracks", callback_data=TRACKS),
    ],
    [
      InlineKeyboardButton("Get Top Albums", callback_data=ALBUMS),
      InlineKeyboardButton("Get Top Artists", callback_data=ARTISTS),
    ]
  ]
    
  reply_markup = InlineKeyboardMarkup(keyboard)
  
  if context.user_data.get(START_OVER):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
  else:
    await update.message.reply_text(text="Hi! I'm Last.fm bot and I can help you get some stats from your account.")
    await update.message.reply_text(text=text, reply_markup=reply_markup)
  
  context.user_data[START_OVER] = False
  return SELECTING_ACTION
  
  
async def showing_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  query = update.callback_query
  user_data = context.user_data
    
  username = user_data.get(USERNAME)
  
  text = ''
  if username == None:
    text += 'You have not provided any username. Edit to add one.'
  else:
    text += f"Great! Your username - {username}"
    
  
  keyboard = [
    [
      InlineKeyboardButton("Edit", callback_data=str(SETTING_USERNAME)), 
      InlineKeyboardButton("Back", callback_data=str(END)), 
    ],
  ]
  
  reply_markup = InlineKeyboardMarkup(keyboard)
  
  if not context.user_data.get(START_OVER):
    await query.answer()
    await query.edit_message_text(text=text, reply_markup=reply_markup)
  else:
    await update.message.reply_text(text=text, reply_markup=reply_markup)
  
  user_data[START_OVER] = False
  return SHOWING

async def setting_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  query = update.callback_query
  user_data = context.user_data
  
  username = context.user_data.get(USERNAME)
  
  if username == None:
    await query.answer()
    await query.edit_message_text(text='Firstly, add username. In 3 seconds you will be redirected back.')
    await sleep(3)
    user_data[START_OVER] = True
    await start_command(update, context)
    
    return END
    
  keyboard = [
    [
      InlineKeyboardButton("Overall", callback_data=PERIOD_OVERALL), 
      InlineKeyboardButton("7 days", callback_data=PERIOD_WEEK), 
      InlineKeyboardButton("1 month", callback_data=PERIOD_MONTH), 
    ],
    [
      InlineKeyboardButton("3 months", callback_data=PERIOD_THREE_MONTH), 
      InlineKeyboardButton("6 months", callback_data=PERIOD_HALF_YEAR), 
      InlineKeyboardButton("1 year", callback_data=PERIOD_YEAR), 
    ],
    [
      InlineKeyboardButton('Back', callback_data=str(END))
    ]
  ]
  
  reply_markup = InlineKeyboardMarkup(keyboard)
    
  user_data[TOP_LEVEL] = query.data
  
  text = 'Select the time period over which to retrieve top tracks for.'
  
  if not context.user_data.get(START_OVER):
    await query.answer()
    await query.edit_message_text(text=text, reply_markup=reply_markup)
  else:
    await update.message.reply_text(text=text, reply_markup=reply_markup)
  
  user_data[START_OVER] = False
  return PERIOD

async def get_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_data = context.user_data
  query = update.callback_query
  
  username = user_data.get(USERNAME)
  user_data[CURRENT_PAGE] = user_data.get(CURRENT_PAGE) or 1
    
  PAGE_RANGE = map(str, range(300, 304))
  PERIOD_RANGE = map(str, range(51, 57))
  is_period = any(item == query.data for item in list(PERIOD_RANGE))
  is_page = any(item == query.data for item in list(PAGE_RANGE))
  
  if is_page:
    page_value = query.data
    if page_value == NEXT_PAGE:
      total = getTotalPage(user_data.get(RESULTS), user_data)
      if int(total) > int(user_data[CURRENT_PAGE]):
        user_data[CURRENT_PAGE] += 1        
    elif page_value == PREVIOUS_PAGE:
      if user_data[CURRENT_PAGE] > 1:
        user_data[CURRENT_PAGE] -= 1
    else:
      user_data[CURRENT_PAGE] = 1
          
  if is_period:
    user_data[TOP_PERIOD] = query.data
    
  response = s.get(
    f"{config('LAST_FM_BASE_URL')}", 
      params = { 
        'user': username, 
        'method': lastfm_level_dict.get(user_data.get(TOP_LEVEL)),
        'period': lastfm_period_dict.get(user_data.get(TOP_PERIOD)),
        'page': user_data[CURRENT_PAGE]
      } 
    )
  
  if not response.ok:
    return await resetting_username(update, context)
    
  data = response.json()
  user_data[RESULTS] = data
  
  # db
  current_user = update.effective_user
  db.connect(reuse_if_open=True)
  
  create_interaction(
    user_id=current_user.id, 
    data_type=lastfm_level_dict.get(user_data.get(TOP_LEVEL)),
    data_period=lastfm_period_dict.get(user_data.get(TOP_PERIOD)),
    data_page=user_data[CURRENT_PAGE]
  )
  
  
  
  return await show_results(update, context)

async def resetting_username(update, context: ContextTypes.DEFAULT_TYPE) -> None:
  query = update.callback_query
  text = 'Seems like a username is wrong. Try to set a correct one.'
  
  keyboard = [
    [
      InlineKeyboardButton('Back to start', callback_data=str(END))
    ]
  ]
  
  reply_markup = InlineKeyboardMarkup(keyboard)
  
  await query.answer()
  await query.edit_message_text(text=text, reply_markup=reply_markup)
  return PERIOD

async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_data = context.user_data
  query = update.callback_query
  
  [isTopTracks, isTopAlbums, isTopArtists] = getTotalLevel(user_data)
    
  results = user_data.get(RESULTS)
    
  text = "Your <b>TOP</b>"
  if isTopTracks:
    text += " <b>TRACKS</b> "
  elif isTopAlbums:
    text += " <b>ALBUMS</b> "
  else:
    text += " <b>ARTISTS</b> "
  
  text += f"<i>{user_period_dict.get(user_data.get(TOP_PERIOD))}</i>:"
  text += '\n\n'
    
  text += f"Page {user_data.get(CURRENT_PAGE)} of"
  text += f" {getTotalPage(results, user_data)}"
    
  text += '\n\n'
  
  def outputResultList(results, user_data):
    [isTopTracks, isTopAlbums, isTopArtists] = getTotalLevel(user_data)
    
    text = ''

    if isTopTracks:
      for item in results['toptracks']['track']:
        value = f"{item.get('artist').get('name')} — {item.get('name')}".replace('"', '').replace('\'', '')
        text += f"<a href=\"https://open.spotify.com/search/{value}\">{value}</a> [{item.get('playcount')} time(s)]"
        text += '\n'
    elif isTopAlbums:
      for item in results['topalbums']['album']:
        value = f"{item.get('artist').get('name')} — {item.get('name')}".replace('"', '').replace('\'', '')

        text += f"<a href=\"https://open.spotify.com/search/{value}\">{value}</a> [{item.get('playcount')} time(s)]"
        text += '\n'
    elif isTopArtists:
      for item in results['topartists']['artist']:
        value = f"{item.get('name')}".replace('"', '').replace('\'', '')

        text += f"<a href=\"https://open.spotify.com/search/{value}\">{value}</a> [{item.get('playcount')} time(s)]"
        text += '\n'
    else:
      text = ''
    return text
  
  text += outputResultList(results, user_data)   
    
  inner_keyboard = [
    InlineKeyboardButton('Back', callback_data=str(END)),
  ]
  
  if not user_data.get(CURRENT_PAGE) == 1:
    inner_keyboard.append(InlineKeyboardButton("To 1️ page", callback_data=FIRST_PAGE))
    inner_keyboard.append(InlineKeyboardButton("⏪️", callback_data=PREVIOUS_PAGE))
    
  if int(user_data.get(CURRENT_PAGE)) < int(getTotalPage(results, user_data)):
    inner_keyboard.append(InlineKeyboardButton("⏩️", callback_data=NEXT_PAGE))
    
    pass
  
  keyboard = [inner_keyboard]
  
  reply_markup = InlineKeyboardMarkup(keyboard)
  
  await query.answer()
  await query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup, disable_web_page_preview=True)
  
  return PERIOD

async def set_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """Set a username"""
  query = update.callback_query
  text = 'Type in your Last.FM username'
  
  await query.answer()
  await query.edit_message_text(text=text)
  
  return TYPING
  
async def save_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_data = context.user_data
  user_data[USERNAME] = update.message.text
  
  current_user = update.effective_user
  
  db.connect(reuse_if_open=True)
  update_last_fm_username(user_id=current_user.id, last_fm_username=update.message.text)
  
  user_data[START_OVER] = True

  return await showing_username(update, context)

async def end_second_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  context.user_data[START_OVER] = True
  context.user_data[CURRENT_PAGE] = 1
  await start_command(update, context)

  return END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  print(context.error)
  pass


def main() -> None:
  """Start the bot."""
  persistence = PicklePersistence(filepath="last-fm-bot")
    
  application = Application.builder().token(config('TOKEN')).persistence(persistence).build()
  
  conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_command)],
    states={
      SELECTING_ACTION: [
        ConversationHandler(
          entry_points=[CallbackQueryHandler(showing_username, pattern="^" + str(SHOWING_USERNAME) + "$" )],
          states={
            SHOWING: [
              CallbackQueryHandler(set_username, pattern="^" + str(SETTING_USERNAME) + "$" ),
              CallbackQueryHandler(end_second_level, pattern="^" + str(END) + "$" )
            ],
            TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_input)],
          },
          fallbacks=[
            CallbackQueryHandler(start_command, pattern="^" + str(END) + "$" )
          ],
          name='Name',
          persistent=True,
          map_to_parent={
            END: SELECTING_ACTION
          }
        ),
        ConversationHandler(
          entry_points=[CallbackQueryHandler(setting_top, pattern=f"^{TRACKS}$|^{ALBUMS}$|^{ARTISTS}$" )],
          states={
            PERIOD: [
              CallbackQueryHandler(get_results, pattern=f"^{PERIOD_OVERALL}$|^{PERIOD_WEEK}$|^{PERIOD_MONTH}$|^{PERIOD_THREE_MONTH}$|^{PERIOD_HALF_YEAR}$|^{PERIOD_YEAR}$"),
              CallbackQueryHandler(get_results, pattern=f"^{FIRST_PAGE}$|^{NEXT_PAGE}$|^{PREVIOUS_PAGE}$"),
              CallbackQueryHandler(end_second_level, pattern="^" + str(END) + "$" )
            ],
          },
          fallbacks=[],
          map_to_parent={
            END: SELECTING_ACTION,
          }
        )
      ],
    },
    fallbacks=[CommandHandler("start", start_command)],
  )

  application.add_handler(conv_handler)
  application.add_error_handler(error_handler)
      
  # Start Bot
  application.run_polling(allowed_updates=Update.ALL_TYPES)
  
if __name__ == "__main__":
  main()

