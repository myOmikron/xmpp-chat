import asyncio
import json
import time
import logging
from queue import Queue
from threading import Thread

import requests
from django.apps import apps
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed, AppRegistryNotReady
from rc_protocol import get_checksum

from xmpp_handler.xmpp import XmppHandler
from xmpp_handler.state import State


logger = logging.getLogger(__name__)


class XmppStartupMiddleware:
    def __init__(self, *args, **kwargs):
        logging.basicConfig(level=logging.INFO)

        asyncio.set_event_loop(asyncio.new_event_loop())
        XmppHandler.instance = XmppHandler()
        XmppHandler.instance.on_message = on_message
        XmppHandler.instance.start_in_thread()

        threads = [RequestThread() for _ in range(1)]
        for thread in threads:
            thread.start()

        StateLoader().start()

        raise MiddlewareNotUsed("Good.Design")


class StateLoader(Thread):
    def run(self):
        while True:
            try:
                apps.check_models_ready()
                State.instance = State()
                break
            except AppRegistryNotReady:
                time.sleep(1)


def on_message(room_jid, message, member, source, **kwargs):
    if member.nick == settings.XMPP_USER_NICK:
        return
    else:
        user = member.nick
        text = message.body.any()

        try:  # TODO Experimental
            timestamp = message.xep0203_delay[0].stamp
            logger.info("Skipping old message")
            return
        except IndexError:
            pass

        room = State.instance.get(room_jid)
        if not room or not room.callback_secret or not room.callback_uri or not room.callback_id:
            return

        params = {
            "char_id": room.callback_id,
            "user_name": user,
            "message": text
        }
        params["checksum"] = get_checksum(params, room.callback_secret, "sendMessage")

        RequestThread.queue.put((f"{room.callback_uri}/sendMessage", json.dumps(params)))


class RequestThread(Thread):

    queue = Queue()
    running: bool

    def run(self):
        self.running = True
        while self.running:
            uri, data = self.queue.get()
            requests.post(uri, data=data, headers={"user-agent": "xmpp-chat"}, verify=settings.VERIFY_SSL_CERTS)

    def stop(self):
        self.running = False
