# Phase 2 Report — Pipeline End-to-End

> 작성일: 2026-05-27
> 범위: STT 모듈(Codex 위임), Scene 모듈, Pipeline orchestrator, Writers, CLI 완성, E2E 검증

## 완료 항목

### 1. STT 모듈 (Codex 위임)
- `src/vae/analyzers/stt.py` — `transcribe()`, `words_to_subtitles()`
- faster-whisper lazy import (없으면 친절한 ImportError)
- `_resolve_device()` — `auto` 모드 시 CUDA 자동 감지, torch 없으면 cpu 폴백
- 분리 조건 4가지: 문장부호 / max_chars / max_duration / gap_threshold
- 테스트 9개 (unit) 전부 통과, `@pytest.mark.slow` 로 실 모델 호출 분리

### 2. Scene 감지 (`analyzers/scene.py`)
- PySceneDetect ContentDetector 래핑
- 의존성 없으면 클립 전체를 단일 씬으로 폴백
- `min_scene_len` 초 단위 → 프레임 변환

### 3. FFmpeg 유틸 (`utils/ffmpeg.py`)
- `probe_clip()` — ffprobe JSON 파싱 → `ClipMeta`
- `probe_duration()` — 가벼운 duration 전용
- `have_ffmpeg()` — 환경 체크

### 4. Pipeline (`pipeline/`)
- `AnalysisContext` — 분석 결과 dataclass
- `orchestrator.collect_clips()` — 폴더 → 지원 확장자 정렬 리스트
- `orchestrator.analyze()` — 클립별 silence + (옵션)STT
- `orchestrator.run_pipeline()` — mode 분기 + timeline 빌드
- `rules/vlog.py` — `build_vlog_timeline()` — 무음 제거 → 1920x1080 timeline

### 5. Writers (`writers/`)
- `write_srt()` — UTF-8 SRT 파일 (한국어 검증)
- `write_report()` — analysis_report.json (clips/silences/timeline/word_count)
- `write_draft()` — **placeholder** (`_format: vae-placeholder/v0`)
  - 실제 CapCut draft_content.json 생성은 사용자 샘플 확보 후 Phase 3

### 6. CLI 완성 (`__main__.py`)
```bash
python -m vae run --mode vlog --input ./clips --output ./out
python -m vae run --mode vlog --input ./clips --output ./out --stt --whisper-model large-v3
python -m vae inspect-draft
```

### 7. 실제 E2E 동작 확인
```
입력: demo.mp4 (8초, 톤2s/무음2s/톤2s/무음1s/톤1s 패턴)
처리:
  [vae] mode=vlog  input=...  output=...
  [vae] analyzed 1 clip(s)
  [vae] timeline duration: 5.40s
  [vae] wrote analysis_report.json
  [vae] wrote capcut_project\draft.json
출력:
  - 무음 2구간 감지: [2.0, 4.0], [6.0, 7.0]
  - 보존 구간 timeline: 5.4초 (의도대로)
  - report.json 1.7KB
  - draft.json (placeholder) 1.0KB
```

## 실측 데이터

| 지표 | 값 |
|------|---|
| 총 테스트 | **25 passed, 1 deselected** |
| 테스트 실행 시간 | 1.13초 |
| 신규 모듈 | 8개 (stt, scene, ffmpeg, context, orchestrator, vlog, 3 writers) |
| CLI 커맨드 | 2개 (run, inspect-draft) |
| E2E 동작 | ✅ 실제 mp4 → CLI → 정확한 결과 |

## 발견 사항

### 잘된 점
- **모듈 분리 효과**: STT를 Codex에게 위임할 수 있었음. 인터페이스만 정의되어 있었기 때문
- **의존성 격리**: faster-whisper, PySceneDetect 없어도 코어 파이프라인은 동작
- **E2E 한 번에 성공**: 단위 테스트들이 잘 깔려 있어서 통합 시 충돌 없음

### 알려진 한계
1. **CapCut draft writer는 placeholder** — 실제 스키마 분석 대기
2. **Shorts 모드는 vlog 룰 재사용** — 9:16 크롭/하이라이트 추출 미구현 (Phase 3)
3. **얼굴/모션/비트 분석 미통합** — Could 우선순위, 필요 시 추가
4. **subtitle 트랙이 timeline에 안 들어감** — STT 결과는 SRT로만 출력, 향후 timeline에도 반영 필요

## 마일스톤 진행 (PLAN.md 기준)

| M | 산출물 | 상태 |
|---|--------|------|
| M0 | 프로젝트 초기화 + GitHub 푸시 | ✅ 완료 (`a68ee39`) |
| M1 | PDCA Design 완료 | ✅ 완료 (`09015aa`) |
| M2 | CapCut draft 스키마 분석 완료 | ⏳ 사용자 샘플 대기 |
| M3 | 무음 제거 PoC (Codex 위임) | ✅ Phase 1에서 Claude 직접 |
| M4 | Whisper STT 통합 | ✅ Codex 위임 완료 (이번) |
| M5 | 브이로그 모드 E2E 동작 | ✅ 완료 (이번) |
| M6 | 숏폼 모드 E2E 동작 | 🔜 Phase 3 |
| M7 | gap-detector 검증 ≥ 90% | 🔜 Phase 3 |

## 다음 단계 (Phase 3)

### 사용자 액션 필요
1. **CapCut 빈 프로젝트 1개 생성·저장** → 스키마 분석 시작
2. **실제 브이로그 샘플 1개 확보** → 한국어 STT + 자연스러움 검증

### 자동 진행 가능
1. **Shorts 모드 전용 룰** — 하이라이트 추출(volume peak + speech density), 9:16 크롭
2. **subtitle 트랙 timeline 통합** — STT 결과를 timeline에 합류
3. **gap-detector 실행** — 설계 대비 구현 완성도 측정

## 커밋

- `a68ee39` chore: initialize project skeleton
- `d4aa6a9` docs: sample sourcing guide
- `09015aa` feat: phase 1 foundation
- (이번) feat: phase 2 pipeline E2E (stt, scene, orchestrator, writers, CLI)
