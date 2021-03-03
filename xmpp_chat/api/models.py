from django.db import models
from django.db.models import CharField


class RoomModel(models.Model):
    room_jid = CharField(default="", max_length=255, unique=True)
    callback_uri = CharField(default="", max_length=255)
    callback_secret = CharField(default="", max_length=255)
    callback_id = CharField(default="", max_length=255)
