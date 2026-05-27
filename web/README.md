# video-auto-editor — Web GUI

FastAPI 백엔드 + Next.js 프론트엔드. 실시간 로그/진행률/타임라인 모니터링.

## 실행 방법

### 한 번만: 의존성 설치

**백엔드** (Python venv는 이미 있다고 가정)
```powershell
cd C:\tmp\video-auto-editor
.\.venv\Scripts\Activate.ps1
pip install -r web\backend\requirements.txt
```

**프론트엔드**
```powershell
cd web\frontend
npm install
```

### 매번 실행 (두 개 터미널 필요)

**터미널 1 — 백엔드**
```powershell
cd C:\tmp\video-auto-editor
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "src"
uvicorn web.backend.app:app --host 127.0.0.1 --port 8000 --reload
```

**터미널 2 — 프론트엔드**
```powershell
cd C:\tmp\video-auto-editor\web\frontend
npm run dev
```

브라우저: <http://localhost:3000>

## 아키텍처

```
[브라우저]
  ├─ REST  /api/*       ──┐
  │   (Next.js rewrites)  │
  │                       ▼
  └─ WS   ws://:8000/ws/jobs/{id}
                          │
                          ▼
                  [FastAPI :8000]
                          │
                          ▼
                  [vae.pipeline (스레드)]
                          │ emit(PipelineEvent)
                          ▼
                  [JobManager 구독자 큐]
                          │
                          └─ WebSocket으로 푸시
```

## API

| 메서드 | 경로 | 용도 |
|--------|------|------|
| GET    | `/api/health` | 헬스 체크 |
| GET    | `/api/folders/list?path=...` | 폴더 미디어 파일 목록 |
| GET    | `/api/capcut/projects` | CapCut draft 프로젝트 폴더 목록 |
| POST   | `/api/jobs` | 새 작업 생성 (mode/input_dir/output_dir 등) |
| GET    | `/api/jobs` | 전체 작업 목록 |
| GET    | `/api/jobs/{id}` | 작업 상세 + 이벤트 |
| GET    | `/api/jobs/{id}/artifact?name=...` | 생성된 JSON 파일 내용 |
| WS     | `/ws/jobs/{id}` | 실시간 PipelineEvent 스트림 |

## PipelineEvent 종류

- `pipeline_start` / `pipeline_done` — 시작/끝
- `clip_start` / `clip_done` — 클립별 (index/total 포함)
- `stage_start` / `stage_done` — 단계별 (silence/loudness/scenes/stt/probe)
- `timeline_built` — 타임라인 1개 완성 (duration, segment_count)
- `writer_done` — report.json / draft.json 작성
- `error` — 실패
