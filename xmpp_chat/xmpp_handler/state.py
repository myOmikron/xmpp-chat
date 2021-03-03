from api.models import RoomModel
from xmpp_handler.xmpp import XmppHandler


class State:
    """
    A cache for the Room model, to decrease db load
    """

    instance = None

    def __init__(self):
        self.rooms = {}
        for room in RoomModel.objects.all():
            self.rooms[room.room_jid] = room
            XmppHandler.instance.add_room(room.room_jid)

    def add(self, room_jid, callback_uri="", callback_secret="", callback_id=""):
        if room_jid in self.rooms:
            raise ValueError("Room already exists")

        room = RoomModel.objects.create(room_jid=room_jid,
                                        callback_uri=callback_uri,
                                        callback_secret=callback_secret,
                                        callback_id=callback_id)
        self.rooms[room_jid] = room
        XmppHandler.instance.add_room(room.room_jid)

    def remove(self, room_jid):
        self.rooms[room_jid].delete()
        del self.rooms[room_jid]
        XmppHandler.instance.remove_room(room_jid)

    def get(self, room_jid):
        try:
            return self.rooms[room_jid]
        except KeyError:
            return None
