import asyncio
import logging
import queue
from threading import Thread

import aioxmpp
from django.conf import settings

logging.basicConfig(level=logging.INFO)


class XmppHandler:

    instance: "XmppHandler" = None

    thread: Thread
    _loop: asyncio.AbstractEventLoop
    msg_queue: queue.Queue

    jid: aioxmpp.JID
    client: aioxmpp.Client
    muc: aioxmpp.MUCClient

    def __init__(self):
        self.msg_queue = queue.Queue()

        self.jid = aioxmpp.JID.fromstr(settings.XMPP_USER_JID)
        self.client = aioxmpp.Client(self.jid, aioxmpp.make_security_layer(settings.XMPP_USER_PASS))
        self.muc = self.client.summon(aioxmpp.MUCClient)

        self.rooms = {}
        self.add_room("d49579fc-0f89-4a6a-98dd-a86282edee54@conference.stream.zfn.schule")

    @property
    def loop(self):
        if not self._loop:
            self._loop = asyncio.get_event_loop()
        return self._loop

    def add_room(self, jid: str):
        room, future = self.muc.join(aioxmpp.JID.fromstr(jid), settings.XMPP_USER_NICK)
        room: aioxmpp.muc.Room
        room.future = future
        self.rooms[jid] = room

    def remove_room(self, jid):
        return NotImplemented

    def send_message(self, room_jid: str, msg: str):
        self.msg_queue.put((room_jid, msg))

    async def _send_to_room(self, room_jid: str, msg: str):
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
                    room, msg = self.msg_queue.get(block=False)
                    await self._send_to_room(room, msg)
                except queue.Empty:
                    await asyncio.sleep(0)

    def start_in_thread(self):
        self._loop = asyncio.get_event_loop()

        def run():
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self.run())

        self.thread = Thread(target=run)
        self.thread.start()
