import time
from threading import Thread

from django.apps import apps
from django.core.exceptions import MiddlewareNotUsed, AppRegistryNotReady

from xmpp_handler.xmpp import XmppHandler
from xmpp_handler.state import State


class XmppStartupMiddleware:
    def __init__(self):
        XmppHandler.instance = XmppHandler()
        XmppHandler.instance.start_in_thread()
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
