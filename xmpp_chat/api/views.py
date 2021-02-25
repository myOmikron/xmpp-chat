import hashlib
import json
from datetime import datetime

from django.http import JsonResponse
from django.views.generic import TemplateView

from api.models import RoomModel
from xmpp_chat import settings


def validate_request(args, method):
    if "checksum" not in args:
        return {"success": False, "message": "No checksum was given."}
    ret = {"success": False, "message": "Checksum was incorrect."}
    current_timestamp = int(datetime.now().timestamp())
    checksum = args["checksum"]
    del args["checksum"]
    for i in range(settings.SHARED_SECRET_TIME_DELTA):
        tmp_timestamp = current_timestamp - i
        call = method + json.dumps(args)
        if hashlib.sha512((call + settings.SHARED_SECRET + str(tmp_timestamp)).encode("utf-8")).hexdigest() == checksum:
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
        room, created = RoomModel.objects.get_or_create(
            room_jid=args["room_jid"],
            callback_uri="" if "callback_uri" not in args else args["callback_uri"],
            callback_secret="" if "callback_secret" not in args else args["callback_secret"]
        )
        if not created:
            return JsonResponse(
                {"success": False, "message": "Room was already registered."},
                status=304,
                reason="Room was already registered."
            )
        room.save()
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
        if "room_jid" not in args:
            return JsonResponse(
                {"success": False, "message": "Parameter room_jid is mandatory but missing."},
                status=403,
                reason="Parameter room_jid is mandatory but missing."
            )
        try:
            room = RoomModel.objects.get(room_jid=args["room_jid"])
            room.delete()
            # TODO Delete listener
        except RoomModel.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Room was not found"},
                status=404,
                reason="Room was not found"
            )
