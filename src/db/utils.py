import datetime
from peewee import *

from src.db.database import User, Interaction, db

def create_user(id: int, username: str or None, first_name: str or None, last_name: str or None) -> None:
  User.create(id=id, username=username, first_name=first_name, last_name=last_name, reg_date=datetime.datetime.utcnow())
  
def update_last_fm_username(user_id: id, last_fm_username: str) -> None:  
  res = (User
       .update(last_fm_username=last_fm_username)
       .where(User.id == user_id)
       .execute())
  return res
  
def create_interaction(user_id: int, data_type: str, data_period: str, data_page: int) -> None:
  user = User.get(User.id == user_id)
  Interaction.create(user=user, data_type=data_type, data_period=data_period, data_page=data_page, date=datetime.datetime.utcnow())
  
  
def user_exists(user_id: int) -> bool:
  try:
    User.get_by_id(user_id)
    return True
  except DoesNotExist:
    return False
