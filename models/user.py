import datetime
from dynamorm import DynaModel, GlobalIndex, ProjectAll
from marshmallow import fields

class User(DynaModel):
    
    class Table:
        name = "users"
        hash_key = "username"

    class Schema:
        username = fields.String()
        password = fields.String()
        last_token = fields.String()
#print(str(User.get(username="mdkelley02").last_token))


