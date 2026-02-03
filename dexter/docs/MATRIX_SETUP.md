# Matrix E2EE Setup for DEXTER

## 1. Create Matrix Account

Option A: Use matrix.org (hosted)
- Go to https://app.element.io
- Create account (e.g., @dexter-refinery:matrix.org)

Option B: Self-host (sovereign)
- Deploy Synapse homeserver
- More complex but fully air-gapped

## 2. Create Room

- In Element, create new room
- Name: "DEXTER Refinery"
- Enable encryption (E2EE)
- Invite yourself and the bot account

## 3. Get Access Token

```bash
# Using curl
curl -XPOST -d '{"type":"m.login.password", "user":"dexter-refinery", "password":"YOUR_PASSWORD"}' \
  "https://matrix.org/_matrix/client/r0/login"
```

Response contains `access_token`.

## 4. Get Room ID

- In Element, go to Room Settings > Advanced
- Copy "Internal room ID" (starts with `!`)

## 5. Configure .env

```bash
MATRIX_HOMESERVER=https://matrix.org
MATRIX_USER_ID=@dexter-refinery:matrix.org
MATRIX_ACCESS_TOKEN=syt_xxxxx
MATRIX_ROOM_ID=!AbCdEfG:matrix.org
```

## 6. Install SDK

```bash
pip install matrix-nio
```

## 7. Test

```python
from skills.comms.matrix import send_message
import asyncio

asyncio.run(send_message("DEXTER online. Testing Matrix comms."))
```

## Usage

Bundle alerts auto-push on creation.
Human commands in room:
- `APPROVE B-20260203-143022` -- Mark for promotion
- `REJECT B-20260203-143022` -- Flag issues
- `REVIEW B-20260203-143022` -- Request details
