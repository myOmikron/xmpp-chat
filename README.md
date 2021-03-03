# XMPP Chat

This project is an HTTP Interface to send messages received via HTTP to a given XMPP server and send received messages 
from XMPP to a callback uri.

## Installation

## API

See [bbb-stream](https://github.com/myOmikron/bbb-stream/blob/master/chat_bridges.md)

### Authentication

See [Random Checksum Protocol](https://github.com/myOmikron/rcp)

In `settings.py`:
```python
SHARED_SECRET = "change_me"
SHARED_SECRET_TIME_DELTA = 5
```
