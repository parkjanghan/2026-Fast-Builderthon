from aiohttp import web
import json
from datetime import datetime


def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # 연결 성공 즉시 명세서에 따른 Connected Message 전송
    await ws.send_json({
        "type": "connected",
        "message": "Connection established",
        "timestamp": int(datetime.now().timestamp() * 1000)
    })
    print(f"[{get_time()}] ✅ [시스템] 클라이언트와 프로토콜 연결 완료")

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            curr_t = get_time()
            try:
                payload = json.loads(msg.data)
                msg_type = payload.get("type")

                # 1. Frame 데이터 수신 로그
                if msg_type == "frame":
                    v_time = payload.get("videoTime")
                    img_sample = payload.get("image",
                                             "")[:30]  # Base64 앞부분만 추출
                    print(
                        f"[{curr_t}] 🖼️  [Frame 수신] 시간: {v_time}s | 이미지 샘플: {img_sample}..."
                    )

                    # (여기서 처리 로직이나 파일 저장을 수행)

                # 2. Audio 데이터 수신 로그
                elif msg_type == "audio":
                    v_start = payload.get("videoTimeStart")
                    duration = payload.get("duration")
                    audio_sample = payload.get("data", "")[:30]
                    print(
                        f"[{curr_t}] 🎵 [Audio 수신] 구간: {v_start}s ~ {v_start + duration}s | 데이터 샘플: {audio_sample}..."
                    )

                    # 수신 확인을 위해 클라이언트에 Transcript 응답 (명세서 기준)
                    await ws.send_json({
                        "type":
                        "transcript",
                        "startTime":
                        v_start,
                        "endTime":
                        v_start + duration,
                        "text":
                        "데이터 수신 확인됨",
                        "fullContext":
                        f"{v_start}초 구간의 오디오를 서버에서 정상 수신함"
                    })

                else:
                    print(f"[{curr_t}] ❓ [알 수 없는 타입]: {msg_type}")

            except json.JSONDecodeError:
                print(f"[{curr_t}] ⚠️ [에러] JSON 형식이 아닙니다.")
            except Exception as e:
                print(f"[{curr_t}] ❌ [시스템 에러]: {str(e)}")

    print(f"[{get_time()}] ❌ [시스템] 클라이언트 연결 종료")
    return ws


app = web.Application()
app.add_routes([web.get('/ws', websocket_handler)])

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8080)
