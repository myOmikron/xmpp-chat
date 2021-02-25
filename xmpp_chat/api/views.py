import hashlib
import json
from datetime import datetime

from django.http import JsonResponse
from django.views.generic import TemplateView

from xmpp_chat import settings


def validate_request(args, method):
    if "checksum" not in args:
        return {"success": False, "message": "No checksum was given."}
    ret = {"success": False, "message": "Checksum was incorrect."}
    current_timestamp = int(datetime.now().timestamp())
    for i in range(settings.SHARED_SECRET_TIME_DELTA):
        tmp_timestamp = current_timestamp - i
        call = method + json.dumps(args)
        if hashlib.sha512((call + settings.SHARED_SECRET + str(tmp_timestamp)).encode("utf-8")).hexdigest() == args["checksum"]:
            ret["success"] = True
            ret["message"] = "Checksum is correct"
            break
    return ret


class SendChatMessage(TemplateView):
    def post(self, request, jid="", *args, **kwargs):
        try:
            args = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Decoding data failed"},
                status=400,
                reason="Decoding data failed"
            )
        validated = validate_request(args, "sendChatMessage")
        if not validated["success"]:
            return JsonResponse(validated, status=400, reason=validated["message"])
        if "user_name" not in args:
            return JsonResponse(
                {"success": False, "message": "Parameter user_name is mandatory but missing."},
                status=400,
                reason="Parameter user_name is mandatory but missing."
            )
        if "message" not in args:
            return JsonResponse(
                {"success": False, "message": "Parameter message is mandatory but missing."},
                status=400,
                reason="Parameter message is mandatory but missing."
            )
        # TODO Send message via bridge


class StartChatForRoom(TemplateView):

    def post(self, request, *args, **kwargs):
        try:
            args = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Decoding data failed"},
                status=400,
                reason="Decoding data failed"
            )
        validated = validate_request(args, "startChatForRoom")
        if not validated["success"]:
            return JsonResponse(validated, status=400, reason=validated["message"])
        if "room_jid" not in args:
            return JsonResponse(
                {"success": False, "message": "Parameter room_jid is mandatory but missing."},
                status=403,
                reason="Parameter room_jid is mandatory but missing."
            )
        if "callback_uri" not in args:
            if "callback_secret" in args:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Parameter callback_uri is mandatory when specifying callback_secret, but missing"
                    },
                    status=403,
                    reason="Parameter callback_uri is mandatory when specifying callback_secret, but missing"
                )
        if "callback_secret" not in args:
            if "callback_uri" in args:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Parameter callback_secret is mandatory when specifying callback_uri, but missing"
                    },
                    status=403,
                    reason="Parameter callback_secret is mandatory when specifying callback_uri, but missing"
                )
        # TODO Start listener


class EndChatForRoom(TemplateView):

    def post(self, request, *args, **kwargs):
        try:
            args = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Decoding data failed"},
                status=400,
                reason="Decoding data failed"
            )
        validated = validate_request(args, "endChatForRoom")
        if not validated["success"]:
            return JsonResponse(validated, status=400, reason=validated["message"])
        if "jid_room" not in args:
            return JsonResponse(
                {"success": False, "message": "Parameter jid_room is mandatory but missing."},
                status=403,
                reason="Parameter jid_room is mandatory but missing."
            )
        # TODO Delete listener
