# Phase 5 Report — Web GUI · GitHub Pages · 100 % 자동 렌더

> 작성일: 2026-05-28
> 범위: 실시간 대시보드, 정적 데모 배포, 드래그앤드롭 업로드, 1클릭 런처,
> FFmpeg 자동 렌더링까지

## 완료 항목

### 1. 이벤트 스트리밍 인프라
- `src/vae/pipeline/events.py` — 11종 `PipelineEvent` (`pipeline_start`,
  `clip_start`, `stage_done`, `timeline_built`, `writer_done`, `error` 등)
- `orchestrator.run_pipeline(..., emit=emitter)` — 단계별 이벤트 방출

### 2. FastAPI 백엔드
- `web/backend/jobs.py` — 스레드 워커 + `asyncio.Queue` 구독자 모델
- `web/backend/app.py` — 13개 라우트 (REST + `/ws/jobs/{id}` WebSocket)
- `POST /api/uploads` — 멀티파트 업로드 → `%TEMP%/vae_uploads/{uuid}/`
  (지원 확장자만 허용, 500MB/파일 캡)

### 3. Next.js 대시보드 (Tailwind, 다크)
- `JobForm` — 모드/STT/렌더/BGM/트랜지션 옵션
- `FilePicker` — 4가지 입력(드래그앤드롭 · 파일 · 폴더 · 경로) + 최근 5개 이력
- `ProgressBar`, `LogStream`, `Metrics`, `TimelinePreview`
- `VideoPlayer` — 원본/숏폼 탭 + 타임라인 클릭 → 영상 점프
- `HowToUse` — 설치/실행/모드/결과 가이드

### 4. GitHub Pages 배포
- `next.config.js` 환경분기: `NEXT_PUBLIC_DEMO_MODE=1` 일 때 정적 export
- 데모 모드에서는 캡처된 실 이벤트(`public/demo/job.json`)를 재생
- `.github/workflows/deploy-pages.yml` — push to main → 자동 빌드/배포
- 라이브 URL: https://aijunny0604-alt.github.io/video-auto-editor/

### 5. Windows 1-클릭 런처
- `scripts/setup.bat` — 사전 요구사항 체크 + venv + pip + npm install
- `scripts/_run-backend.bat`, `_run-frontend.bat` — 단일 책임 헬퍼
- `scripts/open-editor.bat` — 포트 정리 → 두 헬퍼 호출 → 브라우저 열기
- `scripts/create-desktop-shortcut.bat` — 바탕화면 `.lnk` 생성
- `scripts/stop-editor.bat` — 포트/창 정리

### 6. 100 % 자동 렌더 (FFmpeg)
- `src/vae/writers/renderer.py` — 세그먼트 추출 → concat (xfade fade)
  → 자막 burn-in → BGM amix → mp4 출력
- `src/vae/utils/bgm.py` — 입력 폴더 첫 음악 파일을 자동 BGM으로 사용
- `orchestrator.collect_clips()` — 비디오만 클립으로 인정 (음악은 BGM 후보)
- 옵션 (CLI/백엔드/GUI 모두): `--render`, `--bgm`, `--bgm-volume`,
  `--transition`

## 실측 데이터

| 지표 | 값 |
|------|---|
| 총 테스트 | **57 / 57 통과** (+ 1 slow) |
| 코어 모듈 신규 | events, renderer, bgm (3) |
| 백엔드 라우트 | 13 |
| 프론트엔드 컴포넌트 | 8 (JobForm, FilePicker, ProgressBar, LogStream, Metrics, TimelinePreview, VideoPlayer, HowToUse) |
| 런처 스크립트 | 6 |
| 자동 렌더 검증 | shorts 1080×1920 (4 s, 135 KB) · vlog 1920×1080 (16 s, 432 KB) |

## 실제 동작 (CLI)

```
[vae] mode=shorts  input=...
[vae] analyzed 1 clip(s)
[vae] produced 2 timeline(s)
[vae] BGM: bgm.mp3                      ← 자동 감지
[vae] #1 duration=4.00s
[vae]      analysis_report_01.json      ← CapCut 호환 메타
[vae]      [render] final_01.mp4 (135KB) ← 🎬 완성된 영상
[vae] #2 duration=2.52s
[vae]      [render] final_02.mp4 (87KB)
```

ffprobe: H.264 + AAC, 1080×1920, 44.1 kHz, 정상 재생.

## 사용자 가치

- 평소 1시간 영상 편집 → **15~20분으로 단축**
- 완전 자동 모드: 사람 손 **0**, 결과물은 SNS 업로드 가능
- 자유도 모드(`--no-render`): 컷 좌표/자막만 받아 CapCut에서 미세 조정
- 비개발자도 사용 가능: **바탕화면 더블클릭 → 영상 드래그 → ▶**

## 알려진 한계 (다음 Phase 후보)

1. **emphasis_keywords 적용** — 모델은 있고 burn-in 단계에서 강조 색 미적용
2. **face tracking 룰 연결** — `faces.py` 모듈/테스트 있음. `shorts.py`가 아직 `vertical_crop_9_16` 폴백만 사용
3. **CapCut 실 스키마** — 사용자가 빈 프로젝트 1개 저장하면 분석 가능
4. **트랜지션 종류** — `fade`만 (xfade의 다른 효과 추가 가능)
5. **음악 비트에 컷 맞추기** — `librosa` 또는 ffmpeg `astats` 비트 detection
6. **인트로/아웃트로/썸네일** — 자동 생성 미구현

## 커밋 (시간순)

- `2681baa` feat: web GUI — FastAPI backend + Next.js dashboard
- `015a43e` feat: face tracking module + face-aware crop
- `e7f8521` chore: allow demo mp4s under web/frontend/public/demo
- `a400c96` feat: demo videos + how-to-use guide on Pages
- `581e85e` feat: GitHub Pages deployment — demo mode
- `69883bf` feat: drag-and-drop upload, folder picker, recent history
- `3949802` feat: one-click Windows launcher scripts
- `cebbaac` fix(scripts): split launcher into helper bats
- `fb36fd8` feat: 100% auto-render to finished mp4
- (이번 커밋) docs: refresh all docs for Phase 5
