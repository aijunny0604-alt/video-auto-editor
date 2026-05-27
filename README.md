# video-auto-editor

브이로그 · 숏폼(쇼츠 · 릴스) **자동 컷편집 + 자동 렌더링** 파이프라인.
영상 폴더만 넘기면 분석부터 자막 burn-in · BGM · 페이드 트랜지션까지
한 번에 처리해 **업로드 가능한 mp4**를 떨궈줍니다.

> 🌐 **데모 페이지**: <https://aijunny0604-alt.github.io/video-auto-editor/>
> (실제 파이프라인 실행 결과를 재생합니다 — 백엔드 없이 동작)

## 핵심 기능

- **100 % 자동 렌더** — `▶` 한 번이면 `final.mp4`가 출력 폴더에 떨어집니다.
- **모드 분기** — 16 : 9 브이로그 / 9 : 16 숏폼 (자동 크롭)
- **무음 자동 제거** + **한국어 STT 자막** (Whisper, CUDA 가속)
- **자막 burn-in**, **BGM 자동 믹싱**, **fade 트랜지션**
- 실시간 로그/메트릭/타임라인 미리보기 **웹 대시보드**
- 결과물은 CapCut 등 외부 편집기에서도 미세 조정 가능 (`report.json` · `subtitles.srt` 동시 출력)

## 무엇을 해 주나 / 무엇은 못하나

| 자동 ✅ | 사람 몫 ⚠️ |
|---------|------------|
| 무음/씬/음량/얼굴 분석 | 창의적 컷 감각 |
| 컷 좌표 결정, 9 : 16 크롭 | 자막 디자인 자유 변경 |
| Whisper STT → 자막 burn-in | 트랜지션 종류 확장 |
| BGM 자동 믹싱 (`bgm_volume` 조절) | "신나는 곡" 같은 무드 매칭 |
| 페이드 트랜지션 | 비트에 맞춰 컷 |
| 최종 mp4 인코딩 (H.264 + AAC) | 인트로 · 아웃트로 · 썸네일 |

## 빠른 시작 (Windows)

> Python 3.10+, Node 20+, FFmpeg(`winget install Gyan.FFmpeg`) 설치 필수.

```powershell
git clone https://github.com/aijunny0604-alt/video-auto-editor
cd video-auto-editor

# 1) 한 번만 — 의존성 설치
scripts\setup.bat

# 2) 한 번만 — 바탕화면 바로가기 만들기
scripts\create-desktop-shortcut.bat

# 3) 매번 — 바탕화면 [video-auto-editor] 아이콘 더블클릭
#    혹은 scripts\open-editor.bat
```

브라우저가 자동으로 `http://localhost:3000`을 열어 줍니다.

### GUI에서 영상 넣는 4가지 방법

1. **드래그 앤 드롭** — 파일/폴더를 페이지로 끌어다 놓기
2. **📄 파일 선택** — 클릭 → 다중 선택 다이얼로그
3. **📁 폴더 선택** — 하위 폴더 전체 (Chrome/Edge/Firefox)
4. **💻 로컬 경로** — `C:\Users\...\Videos\원본` 같이 직접 입력
5. (보너스) **최근 5개 자동 기억** — 한 번 쓴 폴더는 1 클릭 재사용

## CLI (선호 시)

```powershell
# 가장 단순한 경우 - 전부 자동
python -m vae run --mode vlog --input ./clips --output ./out

# STT 자막 + BGM 자동 + 페이드
python -m vae run --mode shorts --input ./clips --output ./out --stt --shorts-count 3

# CapCut만 쓰고 싶으면 렌더 끄기
python -m vae run --mode vlog --input ./clips --output ./out --no-render
```

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--mode {vlog\|shorts}` | (필수) | 16:9 또는 9:16 |
| `--input` / `--output` | (필수) | 입력 폴더 / 출력 폴더 |
| `--stt` / `--no-stt` | `--no-stt` | Whisper 자막 (느림, GPU 권장) |
| `--whisper-model` | `large-v3` | tiny/base/small/medium/large-v3 |
| `--shorts-count` | 3 | 클립당 숏폼 개수 |
| `--shorts-length` | 30.0 | 숏폼 길이(초) |
| `--render` / `--no-render` | `--render` | 최종 mp4 자동 렌더 |
| `--bgm` | (자동 감지) | 입력 폴더 첫 음악 파일이 자동 BGM |
| `--bgm-volume` | 0.18 | 0.0~1.0 |
| `--transition` | `fade` | `fade` 또는 `none` |

## 출력물

```
out/
├─ final.mp4                       ← 🎬 업로드 가능한 완성 영상
├─ final_01.mp4, final_02.mp4      ← (shorts 모드: timeline 수만큼)
├─ analysis_report.json            ← 컷/크롭/스타일 좌표 일체
├─ subtitles.srt                   ← (--stt 옵션 시)
└─ capcut_project/
    └─ draft.json                  ← CapCut 미세조정용 메타
```

## 아키텍처

```
[입력 폴더] ─┐
             │  ┌──────────────────────┐
             ├─►│ analyzers (read-only) │
             │  │  audio · stt · scene │
             │  │  loudness · faces    │
             │  └──────────┬───────────┘
             │             │ AnalysisContext
             │             ▼
             │  ┌──────────────────────┐
             │  │  rules / mode        │
             │  │   vlog or shorts     │
             │  └──────────┬───────────┘
             │             │ Timeline(+style, +crop, +mode)
             │             ▼
             │  ┌──────────────────────┐
             │  │ writers              │
             │  │   report.json        │
             │  │   capcut/draft.json  │
             │  │   subtitles.srt      │
             │  │   renderer → mp4 🎬  │
             │  └──────────────────────┘
             │
[BGM mp3] ───┘  (선택, 자동 감지)
```

세부 사양: [`docs/02-design/DESIGN.md`](docs/02-design/DESIGN.md)

## 폴더 구조

```
video-auto-editor/
├─ src/vae/                  # 코어 라이브러리
│   ├─ analyzers/             # FFmpeg / Whisper / OpenCV
│   ├─ pipeline/              # 오케스트레이션 + 모드 룰
│   ├─ writers/               # report, draft, srt, renderer
│   ├─ models/, utils/
│   └─ __main__.py            # CLI
├─ web/
│   ├─ backend/               # FastAPI + WebSocket + JobManager
│   └─ frontend/              # Next.js 14 + Tailwind 대시보드
├─ scripts/                   # Windows 더블클릭 런처
├─ tests/                     # 57 + 1 slow 테스트
└─ docs/
    ├─ 01-plan/PLAN.md
    ├─ 02-design/DESIGN.md
    └─ 03-analysis/PHASE_N_REPORT.md
```

## 테스트

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "src"
python -m pytest -q -m "not slow"   # 57 / 57 통과
python -m pytest -q                  # +1 slow (faster-whisper 실제 호출)
```

## 협업

- **Claude Code** — 아키텍처 · 통합 · 검증 · PDCA 운영
- **Codex** — STT 모듈 위임 구현
- 사용자 — 의사 결정 · 영상 제공 · 결과 검증

## 라이선스

개인 프로젝트 (Private 시작 → 데모 공개를 위해 Public 전환).
