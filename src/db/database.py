from decouple import config
from peewee import *

db_config = {
  'user': config('DB_USER'),
  'password': config('DB_PWD'),
  'host': config('DB_HOST'),
  'database': config('DB'),
}

db = MySQLDatabase(**db_config)

class BaseModel(Model):
  class Meta:
    database = db
    
class User(BaseModel):
  id = BigAutoField(unique=True)
  username = CharField(null=True)
  last_fm_username = CharField(null=True)
  first_name = CharField(null=True)
  last_name = CharField(null=True)
  reg_date = DateTimeField()
  
  class Meta: 
    table_name = 'User'

class Interaction(BaseModel):
  user = ForeignKeyField(User)
  data_type = CharField()
  data_period = CharField()
  data_page = IntegerField()
  date = DateTimeField()
  
  class Meta:
    table_name = 'Interaction'

# Create Tables
with db:
  db.create_tables([User, Interaction], safe=True)

db.close()