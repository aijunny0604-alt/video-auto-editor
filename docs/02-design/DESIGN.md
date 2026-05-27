# DESIGN: video-auto-editor

> 작성일: 2026-05-27
> PDCA 단계: **Design**
> 선행: [PLAN.md](../01-plan/PLAN.md)

## 1. 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI (vae)                                │
│         click 기반, run --mode {vlog|shorts}                │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │      Pipeline Orchestrator           │
        │  (vae.pipeline.run_vlog/run_shorts) │
        └──┬───────────────────────────────┬──┘
           │                               │
   ┌───────▼──────┐                ┌──────▼──────────┐
   │  Analyzers   │                │  Decision Layer │
   │ (read-only)  │                │  (mode-aware)   │
   │              │                │                 │
   │ ┌──────────┐ │                │ ┌─────────────┐ │
   │ │  audio   │ │                │ │ vlog_rules  │ │
   │ │  stt     │ │  AnalysisCtx   │ │ shorts_rules│ │
   │ │  scene   │ ├────────────────►│              │ │
   │ │  motion  │ │                │ │  → Timeline │ │
   │ │  faces   │ │                │ │             │ │
   │ └──────────┘ │                │ └──────┬──────┘ │
   └──────────────┘                └────────┼────────┘
                                            │
                                  ┌─────────▼────────┐
                                  │ Output Writers   │
                                  │ ┌──────────────┐ │
                                  │ │ capcut_writer│ │
                                  │ │ srt_writer   │ │
                                  │ │ report_writer│ │
                                  │ └──────────────┘ │
                                  └──────────────────┘
```

## 2. 패키지 구조

```
src/vae/
├─ __init__.py
├─ __main__.py              # CLI entry (click) — implemented inline (no separate cli.py)
│
├─ pipeline/
│   ├─ __init__.py
│   ├─ orchestrator.py      # 모드별 파이프라인 실행
│   ├─ context.py           # AnalysisContext (dataclass)
│   ├─ subtitles.py         # words_on_timeline / attach_subtitle_track  ← Phase 3 추가
│   └─ rules/
│       ├─ vlog.py          # 브이로그 의사결정 룰
│       └─ shorts.py        # 숏폼 의사결정 룰
│
├─ analyzers/               # 입력 영상 → 분석 결과 (순수 함수)
│   ├─ audio.py             # FFmpeg silencedetect
│   ├─ stt.py               # faster-whisper
│   ├─ scene.py             # PySceneDetect
│   └─ loudness.py          # FFmpeg astats RMS  ← Phase 3 추가 (librosa 대체)
│   # motion.py, faces.py  — Could 우선순위, 후속 Phase
│
├─ models/                  # 데이터 모델 (pydantic)
│   ├─ clip.py              # ClipMeta, TimeRange
│   ├─ timeline.py          # Timeline, Track, Segment
│   └─ subtitle.py          # Subtitle, Word
│
├─ writers/                 # 결과 출력
│   ├─ capcut.py            # CapCut draft (현재 placeholder, 스키마 분석 대기)
│   ├─ srt.py               # .srt 파일
│   └─ report.py            # analysis_report.json
│
└─ utils/
    ├─ ffmpeg.py            # FFmpeg 래퍼 (probe_clip, probe_duration)
    └─ paths.py             # CapCut 경로 탐색
    # logging.py — 미구현 (현재 click.echo 사용)
```

## 3. 핵심 데이터 모델

### `ClipMeta` (입력 클립 1개)
```python
class ClipMeta(BaseModel):
    path: Path
    duration: float          # 초
    fps: float
    width: int
    height: int
    has_audio: bool
    codec: str
```

### `TimeRange`
```python
class TimeRange(BaseModel):
    start: float             # 초
    end: float
    @property
    def duration(self) -> float: return self.end - self.start
```

### `AnalysisContext` (분석 결과 모음, **Phase 3 동기화**)
```python
@dataclass
class AnalysisContext:
    clips: list[ClipMeta]
    silences: dict[Path, list[TimeRange]]                  # 무음 구간
    speech_words: dict[Path, list[Word]]                   # STT 단어 (← speech_segments에서 rename)
    scenes: dict[Path, list[TimeRange]]                    # 씬 경계 (vlog mode 시 populated)
    loudness: dict[Path, list[tuple[float, float]]]        # (time, rms_db) (← peaks 대체, librosa 미사용)
    # faces, beats — 후속 Phase (Could 우선순위)
```

### `Timeline` (최종 결정된 편집 결과)
```python
class Segment(BaseModel):
    source: Path
    source_range: TimeRange     # 원본 클립의 어느 구간
    timeline_start: float       # 타임라인의 어느 위치에 배치
    reason: str                 # "speech", "peak", "scene_keep" 등

class Track(BaseModel):
    kind: Literal["video", "audio", "subtitle"]
    segments: list[Segment]

class Timeline(BaseModel):
    width: int                  # 1920 (vlog) / 1080 (shorts)
    height: int                 # 1080 (vlog) / 1920 (shorts)
    fps: float
    tracks: list[Track]
```

## 4. 모듈별 인터페이스 (Codex 위임 단위)

각 analyzer는 **순수 함수**, 외부 의존성 격리, 단위 테스트 가능.

### `analyzers/audio.py` ← **Codex 1번 위임 대상**
```python
def detect_silences(
    path: Path,
    noise_db: float = -30.0,    # 무음 임계
    min_duration: float = 0.5,   # 최소 무음 길이
) -> list[TimeRange]:
    """FFmpeg silencedetect 결과를 파싱해서 무음 구간 리스트 반환."""
```

### `analyzers/stt.py` ← **Codex 2번 위임 대상**
```python
def transcribe(
    path: Path,
    model_size: Literal["tiny","base","small","medium","large-v3"] = "large-v3",
    language: str = "ko",
    device: Literal["cuda","cpu"] = "cuda",
) -> list[Word]:
    """faster-whisper로 단어 단위 타임스탬프 추출."""
```

### `analyzers/scene.py` ← **Codex 3번 위임**
```python
def detect_scenes(
    path: Path,
    threshold: float = 27.0,
) -> list[TimeRange]:
    """PySceneDetect ContentDetector."""
```

### `writers/capcut.py` ← **Claude가 직접** (스키마 의존성 높음)
```python
def write_draft(
    timeline: Timeline,
    output_dir: Path,
    template_draft: Path | None = None,
) -> Path:
    """Timeline → draft_content.json. template이 있으면 그 구조 따라감."""
```

## 5. 모드별 의사결정 룰

### `rules/vlog.py`
```
1. 입력 클립들 시간순 정렬
2. 각 클립에서 무음 구간 제거 (단, fade in/out 0.1s 유지)
3. 너무 짧은 세그먼트(<1s) 병합
4. Whisper 단어 단위로 자막 트랙 생성 (하단, 30pt 흰색+검정 외곽선)
5. 씬 경계에서 미세 컷 정리
6. 비율: 16:9 유지 (원본 그대로)
```

### `rules/shorts.py`
```
1. 입력 클립에서 volume_peak + speech_density 높은 60s 구간 N개 추출
2. 각 후보별로:
   - 9:16 크롭 (얼굴 트래킹 기반, 못 찾으면 중앙)
   - 무음 공격적 제거 (0.2s 이상)
   - 자막: 단어 단위 등장, 중앙 배치, 60pt, 강조 키워드 노란색
   - BGM 비트가 있으면 비트마다 컷 전환
3. 후보 N개를 각각 별도 draft로 출력
```

## 6. CapCut Draft 스키마 전략

### 접근 방법
1. **빈 프로젝트 샘플 확보** — 사용자가 CapCut에서 빈 프로젝트 저장
2. **샘플 draft_content.json 구조 분석** — 트랙 구조, 시간 단위, ID 체계 파악
3. **테이블화** — `docs/02-design/capcut-schema.md` 작성
4. **`writers/capcut.py` 구현** — 샘플을 템플릿으로 받아 segments만 치환

### 알려진 사실 (사전 조사)
- 경로: `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\{프로젝트UUID}\`
- 핵심 파일: `draft_content.json` (메인), `draft_meta_info.json` (메타)
- 시간 단위: 마이크로초(μs) 정수
- 트랙 구조: `tracks[].segments[]` (video / audio / text / sticker)
- ID 체계: UUID v4 + 트랙별 카운터

### 폴백 전략
스키마가 너무 복잡하면:
- **CapCut 템플릿 기능** 활용 — 사용자가 템플릿 하나 만들어두고, 미디어 슬롯만 교체
- **OpenTimelineIO** 경유 — OTIO로 만들고 CapCut import (지원 여부 확인 필요)

## 7. 에러 처리 / 폴백

| 상황 | 처리 |
|------|------|
| CUDA 사용 불가 | CPU로 폴백, 경고 출력 |
| Whisper large 메모리 부족 | medium → small 자동 다운그레이드 |
| 얼굴 감지 실패 (shorts 크롭) | 중앙 크롭 폴백 |
| CapCut draft 쓰기 실패 | SRT + 분석 리포트만 출력 (사용자가 수동 import) |
| 입력 클립 손상 | 해당 클립 스킵, 리포트에 기록 |

## 8. 성능 목표 (RTX 기준)

| 입력 | 처리 시간 목표 |
|------|---------------|
| 10분 영상 (vlog) | < 3분 |
| 1시간 영상 (vlog) | < 15분 |
| 1시간 영상 (shorts, 3개 후보) | < 10분 |

병렬화 전략:
- analyzers는 **클립 단위 독립** → `concurrent.futures` 멀티프로세싱
- STT는 GPU 경합 방지 위해 순차 처리

## 9. 테스트 전략

| 레벨 | 도구 | 범위 |
|------|------|------|
| Unit | pytest | 각 analyzer 함수 (작은 샘플 wav/mp4) |
| Integration | pytest | pipeline orchestrator (10초 샘플) |
| E2E | 수동 | 실제 클립으로 CapCut에서 열어보기 |

`tests/fixtures/` 에 10초짜리 합성 영상 1개 보관 (FFmpeg로 생성, 커밋 가능 크기).

## 10. 다음 단계

1. [ ] CapCut draft 스키마 분석 (`docs/02-design/capcut-schema.md`)
2. [ ] `models/` pydantic 모델 정의
3. [ ] Codex 위임: `analyzers/audio.py` 무음 제거 PoC
4. [ ] Codex 위임: `analyzers/stt.py` Whisper 통합
5. [ ] `writers/capcut.py` 초안 (스키마 분석 결과 반영)
6. [ ] `pipeline/orchestrator.py` 통합
7. [ ] `rules/vlog.py` 룰 구현
8. [ ] E2E 검증 → gap-detector
