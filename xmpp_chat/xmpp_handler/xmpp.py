import asyncio
import logging
import queue
from functools import partial
from threading import Thread

import aioxmpp
from django.conf import settings


logger = logging.getLogger(__name__)


def replace_me(*args, **kwargs):
    raise NotImplementedError()


class XmppHandler:

    instance: "XmppHandler" = None

    thread: Thread
    queue: queue.Queue

    jid: aioxmpp.JID
    client: aioxmpp.Client
    muc: aioxmpp.MUCClient

    def __init__(self):
        self.queue = queue.Queue()
        self.on_message = replace_me

        self.jid = aioxmpp.JID.fromstr(settings.XMPP_USER_JID)
        self.client = aioxmpp.Client(self.jid, aioxmpp.make_security_layer(settings.XMPP_USER_PASS))
        self.muc = self.client.summon(aioxmpp.MUCClient)

        self.rooms = {}

    def add_room(self, jid: str):
        self.queue.put(("JOIN", (jid,)))

    async def _add_room(self, jid: str):
        room, future = self.muc.join(aioxmpp.JID.fromstr(jid), settings.XMPP_USER_NICK)
        room.future = future

        def callback(f):
            room.on_message.connect(partial(self.on_message, jid))

        future.add_done_callback(callback)
        self.rooms[jid] = room

    def remove_room(self, jid: str):
        self.queue.put(("LEAVE", (jid,)))

    async def _remove_room(self, jid: str):
        room = self.rooms[jid]
        await room.future
        await room.leave()
        del self.rooms[jid]

    def send_message(self, room_jid: str, msg: str):
        self.queue.put(("SEND", (room_jid, msg)))

    async def _send_message(self, room_jid: str, msg: str):
        room = self.rooms[room_jid]
        await room.future
        stanza = aioxmpp.Message(
            to=room.jid,
            type_=aioxmpp.MessageType.GROUPCHAT
        )
        stanza.body[None] = msg
        await room.send_message(stanza)

    async def run(self):
        async with self.client.connected():
            while True:
                try:
                    type_, data = self.queue.get(block=False)
                    if type_ == "SEND":
                        await self._send_message(*data)
                    elif type_ == "JOIN":
                        await self._add_room(*data)
                    elif type_ == "LEAVE":
                        await self._remove_room(*data)
                except queue.Empty:
                    await asyncio.sleep(0)

    def start_in_thread(self):
        loop = asyncio.get_event_loop()

        def run():
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run())

        self.thread = Thread(target=run)
        self.thread.start()
