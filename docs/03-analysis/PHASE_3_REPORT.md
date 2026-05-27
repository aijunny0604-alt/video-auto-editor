# Phase 3 Report — Shorts Mode + Gap Closure

> 작성일: 2026-05-27
> 범위: Shorts 룰, 볼륨 피크 분석, Subtitle 트랙 통합, gap-detector, Match Rate 개선

## 완료 항목

### 1. 볼륨 피크 감지 (`analyzers/loudness.py`)
- FFmpeg `astats` 필터 기반 (librosa 미사용, 의존성 경량화)
- `analyze_loudness(path, window=1.0)` — window 단위 (time, rms_db) 샘플
- `find_peak_windows(samples, top_n, min_gap)` — top-N 피크 추출
- `windows_around_peaks(peaks, duration, length)` — 피크 중심 윈도우 생성

### 2. Shorts 룰 (`pipeline/rules/shorts.py`)
- `build_shorts_timelines()` — 클립당 최대 N개 timeline 생성
- 1080×1920 (9:16) 캔버스
- 윈도우 내 무음 공격적 제거 (pad=0.05)
- 피크 없으면 인트로 윈도우 폴백

### 3. Subtitle 트랙 통합 (`pipeline/subtitles.py`)
- `words_on_timeline()` — 원본 클립 시간 → timeline 시간 좌표 변환
- 컷 사이에 떨어지는 단어는 자동 제거
- 컷 경계에서 단어는 클리핑
- `attach_subtitle_track()` — Timeline에 subtitle Track 추가

### 4. Orchestrator 확장
- `run_pipeline()` 시그니처 변경: `Timeline` → `list[Timeline]`
- vlog: 항상 1개, shorts: N개 (`--shorts-count`)
- STT 결과가 있으면 자동으로 subtitle 트랙 부착
- `scenes=True` 옵션으로 vlog 모드에서 PySceneDetect 자동 호출 (gap fix #2)

### 5. CLI 확장
- `--shorts-count` (기본 3) — 클립당 shorts 개수
- `--shorts-length` (기본 30s) — shorts 길이
- 다중 timeline 출력: `capcut_project_01/`, `analysis_report_01.json` …

### 6. gap-detector 실행 (Phase 2 → Phase 3 검증)
- **초기 Match Rate: 77%**
- 즉시 적용한 피드백 3건:
  1. ✅ Scene analyzer를 orchestrator에 wire (vlog 모드에서 자동 호출)
  2. ✅ DESIGN.md 동기화 (loudness, subtitles 모듈 추가, AnalysisContext 필드 갱신)
  3. ✅ loudness 단위 테스트 7개 추가
- **개선 후 예상 Match Rate: ~85% (재실행 시 확인 필요)**

## 실측 데이터

| 지표 | 값 |
|------|---|
| 총 테스트 | **36 passed, 1 deselected** |
| 신규 모듈 | 3개 (loudness, shorts, subtitles) |
| Codex 협업 | STT 모듈 1건 (이전 Phase) |
| 실제 E2E | vlog 1개 + shorts 4개 timeline 동시 생성 확인 |
| CLI 옵션 추가 | 2개 (`--shorts-count`, `--shorts-length`) |

## 실제 동작 검증 (shorts 모드)

```
입력: long.mp4 (20초, 5개 톤+무음 패턴, 880Hz 피크 2개)
명령: vae run --mode shorts --shorts-count 2 --shorts-length 6
출력:
  [vae] analyzed 2 clip(s)
  [vae] produced 4 timeline(s)     ← 2 클립 × 2 후보
  [vae] #1 duration=4.10s  -> capcut_project_01/
  [vae] #2 duration=3.15s  -> capcut_project_02/
  [vae] #3 duration=3.10s  -> capcut_project_03/
  [vae] #4 duration=2.10s  -> capcut_project_04/
파일: 4 × draft.json + 4 × analysis_report.json
```

## 마일스톤 진행

| M | 산출물 | 상태 |
|---|--------|------|
| M0~M5 | (Phase 1~2 완료) | ✅ |
| M6 | 숏폼 모드 E2E 동작 | ✅ **이번 Phase 완료** |
| M7 | gap-detector 검증 ≥ 90% | ⏳ 77% → 85% (gap fix 적용) |

## 발견 사항

### 잘된 점
- **모듈 분리 효과 재확인**: subtitle 통합을 별도 모듈로 빼서 vlog/shorts 양쪽 모두 자동 적용
- **librosa 대체 성공**: 순수 FFmpeg `astats`로 의존성 절약, 동일한 효과
- **gap-detector가 유용**: 77% match rate가 구체적 액션 5개로 변환됨

### 알려진 한계 (Phase 4로)
1. **CapCut draft writer 여전히 placeholder** — 사용자 샘플 대기
2. **Subtitle 스타일 미구현** — Track/Segment에 style 메타데이터 없음 (gap-detector 추천 #5)
3. **9:16 실제 크롭 미구현** — 캔버스만 9:16, face/object tracking 없음 (S3, gap-detector 추천)
4. **shorts 룰 unit test 부재** — E2E smoke만, peak picking 정확도 테스트 없음

## 다음 단계 (Phase 4 후보)

### 사용자 액션 대기
- CapCut 빈 프로젝트 1개 저장 → draft writer 실제 구현 진입

### 자동 진행 가능
1. **Subtitle 스타일 모델** — `SubtitleStyle` (font/size/color/position) + vlog/shorts 별 프리셋
2. **9:16 크롭 좌표 계산** — face/object 없이도 중앙 크롭 좌표를 segment에 부여 (CapCut에서 사용)
3. **gap-detector 재실행** — 90% 이상 도달 확인
4. **report-generator로 완료 보고서 작성**

## 커밋

- `a68ee39` chore: init
- `d4aa6a9` docs: samples guide
- `09015aa` feat: phase 1 foundation
- `80f0972` feat: phase 2 pipeline E2E
- (이번) feat: phase 3 shorts mode + gap closure
