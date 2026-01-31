# WebSocket Protocol Specification

Extension과 Server 간의 WebSocket 통신 프로토콜 정의입니다.

## Connection

- **URL**: `wss://your-server.replit.dev/ws`
- **Protocol**: WebSocket (RFC 6455)
- **Data Format**: JSON

---

## Extension → Server (Client to Server)

### 1. Frame Message (화면 캡처)

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

### 2. Audio Message (오디오 청크)

비디오 오디오를 5초 단위 청크로 전송합니다.

```json
{
  "type": "audio",
  "timestamp": 1706745600000,
  "videoTime": 125.0,
  "videoTimeStart": 120.0,
  "duration": 5,
  "data": "GkXfo59ChoEBQveBAULygQRC84EIQoKEd2VibUKHgQJC...",
  "mimeType": "audio/webm;codecs=opus"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | 항상 `"audio"` |
| `timestamp` | number | 전송 시점 Unix timestamp (ms) |
| `videoTime` | number | 현재 비디오 재생 시간 (초) |
| `videoTimeStart` | number | 이 오디오 청크의 시작 시간 (초) |
| `duration` | number | 청크 길이 (초), 기본값 5 |
| `data` | string | Base64 인코딩된 WebM 오디오 데이터 |
| `mimeType` | string | MIME 타입: `"audio/webm;codecs=opus"` |

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

### 2. Transcript Message (STT 결과)

음성을 텍스트로 변환한 결과를 전송합니다.

```json
{
  "type": "transcript",
  "startTime": 120.0,
  "endTime": 125.0,
  "text": "안녕하세요, 오늘 강의를 시작하겠습니다.",
  "fullContext": "이전 문장들... 안녕하세요, 오늘 강의를 시작하겠습니다."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | 항상 `"transcript"` |
| `startTime` | number | 해당 구간 시작 시간 (초) |
| `endTime` | number | 해당 구간 종료 시간 (초) |
| `text` | string | STT 변환 텍스트 |
| `fullContext` | string | 최근 문맥 (이전 transcript 포함) |

---

### 3. Command Message (제어 명령) - Optional

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

### 4. Error Message (에러)

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

        case 'audio':
          console.log(`Audio chunk: ${message.videoTimeStart}s - ${message.videoTimeStart + message.duration}s`);
          // message.data 처리 (Base64 WebM)
          // STT 처리 후 transcript 전송
          ws.send(JSON.stringify({
            type: 'transcript',
            startTime: message.videoTimeStart,
            endTime: message.videoTimeStart + message.duration,
            text: 'STT 결과 텍스트',
            fullContext: '전체 문맥'
          }));
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

            elif message["type"] == "audio":
                start = message["videoTimeStart"]
                duration = message["duration"]
                print(f"Audio chunk: {start}s - {start + duration}s")

                # Base64 오디오 디코딩
                # audio_data = base64.b64decode(message["data"])

                # STT 처리 후 결과 전송
                await websocket.send(json.dumps({
                    "type": "transcript",
                    "startTime": start,
                    "endTime": start + duration,
                    "text": "STT 결과 텍스트",
                    "fullContext": "전체 문맥"
                }))

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
       │  ──── { type: "frame", ... } ────> │
       │                                    │
       │  ──── { type: "audio", ... } ────> │
       │                                    │
       │  <── { type: "transcript", ... } ──│
       │                                    │
       │  ──── { type: "audio", ... } ────> │
       │                                    │
       │  <── { type: "transcript", ... } ──│
       │                                    │
       ▼                                    ▼
```
