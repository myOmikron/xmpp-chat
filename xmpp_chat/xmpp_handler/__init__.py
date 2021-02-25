from django.core.exceptions import MiddlewareNotUsed

from xmpp_handler.handler import XmppHandler


class XmppStartupMiddleware:
    def __init__(self):
        XmppHandler.instance = XmppHandler()
        XmppHandler.instance.start_in_thread()
        raise MiddlewareNotUsed("Good.Design")
