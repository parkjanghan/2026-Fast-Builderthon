# WebSocket Protocol Specification

Extension과 Server 간의 WebSocket 통신 프로토콜 정의입니다.

## Connection

- **URL**: `wss://your-server.replit.dev/ws`
- **Protocol**: WebSocket (RFC 6455)
- **Data Format**: JSON

---

## Extension → Server (Client to Server)

### 1. Frame Message (화면 캡처 이미지)

비디오 화면을 5초 간격으로 캡처하여 전송합니다.

```json
{
  "type": "frame",
  "timestamp": 1706745600000,
  "videoTime": 123.45,
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "capturedAt": 1706745600000
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | 항상 `"frame"` |
| `timestamp` | number | 전송 시점 Unix timestamp (ms) |
| `videoTime` | number | 현재 비디오 재생 시간 (초) |
| `image` | string | Base64 인코딩된 JPEG 이미지 (data URL 형식) |
| `capturedAt` | number | 캡처 시점 Unix timestamp (ms) |

---

### 2. Transcript Message (STT 결과 텍스트)

비디오 오디오를 5초 단위로 캡처 후, Extension에서 ElevenLabs STT API로 변환한 텍스트를 전송합니다.

```json
{
  "type": "transcript",
  "timestamp": 1706745600000,
  "videoTime": 125.0,
  "videoTimeStart": 120.0,
  "videoTimeEnd": 125.0,
  "text": "안녕하세요, 오늘 강의를 시작하겠습니다."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | 항상 `"transcript"` |
| `timestamp` | number | 전송 시점 Unix timestamp (ms) |
| `videoTime` | number | 현재 비디오 재생 시간 (초) |
| `videoTimeStart` | number | 이 오디오 청크의 시작 시간 (초) |
| `videoTimeEnd` | number | 이 오디오 청크의 종료 시간 (초) |
| `text` | string | ElevenLabs STT 변환 텍스트 |

---

## Server → Extension (Server to Client)

### 1. Connected Message (연결 확인)

클라이언트 연결 시 서버가 보내는 확인 메시지입니다.

```json
{
  "type": "connected",
  "message": "Connection established",
  "timestamp": 1706745600000
}
```

---

### 2. Command Message (제어 명령) - Optional

서버에서 클라이언트에 명령을 보낼 때 사용합니다.

```json
{
  "type": "command",
  "action": "pause",
  "value": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | 항상 `"command"` |
| `action` | string | `"pause"`, `"resume"`, `"seek"` 중 하나 |
| `value` | number \| null | seek 시 이동할 시간 (초) |

---

### 3. Error Message (에러)

```json
{
  "type": "error",
  "code": "INVALID_FORMAT",
  "message": "Invalid message format"
}
```

---

## Example: Replit Server (Node.js)

```javascript
const WebSocket = require('ws');

const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
  console.log('Client connected');

  // 연결 확인 메시지 전송
  ws.send(JSON.stringify({
    type: 'connected',
    message: 'Connection established',
    timestamp: Date.now()
  }));

  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data);

      switch (message.type) {
        case 'frame':
          console.log(`Frame received at video time: ${message.videoTime}s`);
          // message.image 처리 (Base64 JPEG)
          break;

        case 'transcript':
          console.log(`Transcript: ${message.videoTimeStart}s - ${message.videoTimeEnd}s`);
          console.log(`Text: ${message.text}`);
          // 이미 STT 처리된 텍스트를 받음 - 서버에서 추가 처리 가능
          break;

        default:
          console.log('Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('Failed to parse message:', error);
      ws.send(JSON.stringify({
        type: 'error',
        code: 'PARSE_ERROR',
        message: error.message
      }));
    }
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

console.log('WebSocket server running on ws://localhost:8080');
```

---

## Example: Replit Server (Python)

```python
import asyncio
import websockets
import json
import base64
from datetime import datetime

async def handle_client(websocket):
    print("Client connected")

    # 연결 확인 메시지 전송
    await websocket.send(json.dumps({
        "type": "connected",
        "message": "Connection established",
        "timestamp": int(datetime.now().timestamp() * 1000)
    }))

    async for data in websocket:
        try:
            message = json.loads(data)

            if message["type"] == "frame":
                print(f"Frame received at video time: {message['videoTime']}s")
                # Base64 이미지 디코딩
                # image_data = base64.b64decode(message["image"].split(",")[1])

            elif message["type"] == "transcript":
                start = message["videoTimeStart"]
                end = message["videoTimeEnd"]
                text = message["text"]
                print(f"Transcript: {start}s - {end}s")
                print(f"Text: {text}")
                # 이미 STT 처리된 텍스트를 받음 - 서버에서 추가 처리 가능

        except json.JSONDecodeError as e:
            await websocket.send(json.dumps({
                "type": "error",
                "code": "PARSE_ERROR",
                "message": str(e)
            }))

async def main():
    async with websockets.serve(handle_client, "0.0.0.0", 8080):
        print("WebSocket server running on ws://0.0.0.0:8080")
        await asyncio.Future()

asyncio.run(main())
```

---

## Data Flow

```
┌─────────────┐                      ┌─────────────┐
│  Extension  │                      │   Server    │
│  (Client)   │                      │  (Replit)   │
└──────┬──────┘                      └──────┬──────┘
       │                                    │
       │  ──── WebSocket Connect ────>      │
       │                                    │
       │  <──── { type: "connected" } ────  │
       │                                    │
       │  ──── { type: "frame", ... } ────> │  (이미지)
       │                                    │
       │  ── { type: "transcript", ... } ─> │  (STT 텍스트)
       │                                    │
       │  ──── { type: "frame", ... } ────> │  (이미지)
       │                                    │
       │  ── { type: "transcript", ... } ─> │  (STT 텍스트)
       │                                    │
       ▼                                    ▼
```

**Note**: STT(Speech-to-Text) 처리는 Extension에서 ElevenLabs API를 통해 수행됩니다.
서버는 이미 변환된 텍스트만 수신합니다.
