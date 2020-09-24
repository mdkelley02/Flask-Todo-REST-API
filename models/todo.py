from dynamorm import DynaModel
import datetime
from marshmallow import fields

class Todo(DynaModel):
    class Table:
        name="items"
        hash_key="username"
        sort_key="item_id"
    class Schema:
        username = fields.String()
        item_id = fields.Int()
        dt_created = fields.String()
        text = fields.String()
        title = fields.String()
