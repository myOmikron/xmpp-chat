# XMPP Chat

This project is an HTTP Interface to send messages received via HTTP to a given XMPP server and send received messages 
from XMPP to a callback uri.

## Installation

## API

### Authentication
In order to have a strong authentication with easy deployment, this project is using a checksum consisting of a shared
secret, and a time factor (unix-epoch). As of the time based component, the use of a NTP Server is highly recommended.

All API calls require this mechanism.

In `settings.py`:
```python
SHARED_SECRET = "change_me"
SHARED_SECRET_TIME_DELTA = 5
```

#### Example

```python
import json
import hashlib
from datetime import datetime

import requests

# Shared secret from bbb-chat
SHARED_SECRET = "change_me"

# Your dictionary with all your parameters
param_dict = {
    "meeting_id": "12345678901234567890-123456789"
}
# Encode as json
json_encoded = json.dumps(param_dict)

# Add API Call
call = "endChatForMeeting" + json_encoded

# Hash with shared secret and current unix epoch
param_dict["checksum"] = hashlib.sha512((call + SHARED_SECRET + str(int(datetime.now().timestamp()))).encode("utf-8")).hexdigest()

# Make request
requests.post("https://example.com/api/endChatForMeeting", data=json.dumps(param_dict))
```

### sendChatMessage/\<jid\>
- Method: `POST`

Sends a message from a user_name to a given meeting_id. startChatForMeeting has to be called before sendMessage can be called.

Parameter        | Required | Type  | Description
:---:            | :---:    | :---: | :---:
user_name        | Yes      | str   | Username from which the message was sent
message          | Yes      | str   | Unformatted message

### startChatForRoom
- Method: `POST`

Parameter        | Required | Type  | Description
:---:            | :---:    | :---: | :---:
jid_room         | Yes      | str   | jid of jabber room
callback_uri     | No       | str   | Only required when callbacks should be enabled. Specifies the uri to which all messages from the bbb chat should be forwarded to.
callback_secret  | No       | str   | Only required when callbacks should be enabled. Specifies the shared secret to use for a specific callback uri.

The callbacks are sent as `POST` calls with the same checksum method as is used in this project. 
The parameter `callback_secret` specifies the shared secret of the given `callback_uri`. 

### endChatForRoom
- Method: `POST`

The chat services for the given internalMeetingId are stopped and all information like `callback_secret`, etc. are
deleted in the db.

Parameter        | Required | Type  | Description
:---:            | :---:    | :---: | :---:
jid_room         | Yes      | str   | jid of jabber room
