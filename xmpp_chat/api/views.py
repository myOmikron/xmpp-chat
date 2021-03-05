import json

from django.http import JsonResponse
from django.views.generic import TemplateView
from rc_protocol import validate_checksum

from xmpp_chat import settings
from xmpp_handler import XmppHandler
from xmpp_handler import State
from api.models import RoomModel


class RunningChats(TemplateView):

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            "count": RoomModel.objects.count(),
            "chat_ids": [room.room_jid for room in RoomModel.objects.all()]
        })


class _PostApiPoint(TemplateView):

    required_parameters: list
    endpoint: str

    def post(self, request, *args, **kwargs):
        # Decode json
        try:
            parameters = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Decoding data failed"},
                status=400,
                reason="Decoding data failed"
            )

        # Validate checksum
        try:
            if not validate_checksum(parameters, settings.SHARED_SECRET,
                                     self.endpoint, settings.SHARED_SECRET_TIME_DELTA):
                return JsonResponse(
                    {"success": False, "message": "Checksum was incorrect."},
                    status=400,
                    reason="Checksum was incorrect."
                )
        except ValueError:
            return JsonResponse(
                {"success": False, "message": "No checksum was given."},
                status=400,
                reason="No checksum was given."
            )

        # Check required parameters
        for param in self.required_parameters:
            if param not in parameters:
                return JsonResponse(
                    {"success": False, "message": f"Parameter {param} is mandatory but missing."},
                    status=400,
                    reason=f"Parameter {param} is mandatory but missing."
                )

        # Hand over to subclass
        return self._post(request, parameters, *args, **kwargs)

    def _post(self, request, parameters, *args, **kwargs):
        return NotImplemented


class SendMessage(_PostApiPoint):

    required_parameters = ["chat_id", "message", "user_name"]
    endpoint = "sendMessage"

    def _post(self, request, parameters, *args, **kwargs):
        jid = parameters["chat_id"]
        user = parameters["user_name"]
        msg = parameters["message"]

        if jid in XmppHandler.instance.rooms:
            XmppHandler.instance.send_message(jid, f"{user} wrote:\n{msg}")
            return JsonResponse(
                {"success": True, "message": "Send message successfully."}
            )
        else:
            return JsonResponse(
                {"success": False, "message": "Unknown room, don't forget to start it first."},
                status=404,
                reason="Unknown room, don't forget to start it first."
            )


class StartChat(_PostApiPoint):

    required_parameters = ["chat_id"]  # Optional: "callback_uri", "callback_secret", "callback_id"
    endpoint = "startChat"

    def _post(self, request, parameters: dict, *args, **kwargs):
        callback_params = ["callback_uri", "callback_secret", "callback_id"]
        missing = []
        for param in callback_params:
            if param not in parameters:
                missing.append(param)

        if len(missing) == 1:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Parameter {missing[0]} is mandatory when enabling callbacks, but is missing"
                },
                status=403,
                reason=f"Parameter {missing[0]} is mandatory when enabling callbacks, but is missing"
            )
        elif len(missing) == 2:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Parameters {missing[0]} and {missing[1]} "
                               f"are mandatory when enabling callbacks, but are missing"
                },
                status=403,
                reason=f"Parameters {missing[0]} and {missing[1]} "
                       f"are mandatory when enabling callbacks, but are missing"
            )

        if State.instance.get(parameters["chat_id"]):
            return JsonResponse(
                {"success": False, "message": "Room was already registered."},
                status=304,
                reason="Room was already registered."
            )
        else:
            if len(missing) == 0:
                State.instance.add(
                    room_jid=parameters["chat_id"],
                    callback_uri=parameters["callback_uri"],
                    callback_secret=parameters["callback_secret"],
                    callback_id=parameters["callback_id"],
                )
            else:
                State.instance.add(
                    room_jid=parameters["chat_id"],
                )
            return JsonResponse({"success": True, "message": "Added room successfully."})


class EndChat(_PostApiPoint):

    required_parameters = ["chat_id"]
    endpoint = "endChat"

    def _post(self, request, parameters, *args, **kwargs):
        jid = parameters["chat_id"]

        if State.instance.get(jid):
            State.instance.remove(jid)
            return JsonResponse(
                {"success": True, "message": "Removed room successfully."}
            )
        else:
            return JsonResponse(
                {"success": False, "message": "Room was not found"},
                status=404,
                reason="Room was not found"
            )
