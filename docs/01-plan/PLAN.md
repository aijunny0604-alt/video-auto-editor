# PLAN: video-auto-editor

> 작성일: 2026-05-27
> 작성자: Claude + 사용자
> PDCA 단계: **Plan**

## 1. 문제 정의

원본 클립 폴더에서 브이로그/숏폼 영상을 만드는 작업은 반복적이고 시간 소모적이다.
무음 제거, 자막 작성, 하이라이트 선별, 세로 크롭, 컷 타이밍 — 모두 패턴이 있다.
이 패턴을 자동화해서 **CapCut 데스크탑에서 미세조정만 하면 끝**나는 상태로 만든다.

## 2. 목표 (성공 기준)

| # | 지표 | 목표값 |
|---|------|--------|
| G1 | 1시간 브이로그 → 편집 가능한 draft 생성 시간 | ≤ 15분 (RTX 기준) |
| G2 | 1시간 영상에서 숏폼 하이라이트 추출 개수 | ≥ 3개 자동 후보 |
| G3 | 자막 STT 정확도 (한국어) | ≥ 90% (Whisper large) |
| G4 | 무음 제거 후 자연스러움 | 사용자 미세조정 시간 ≤ 10분 |
| G5 | CapCut에서 draft 열림 성공률 | 100% |

## 3. 범위

### In Scope (MVP)
- [x] CLI 도구 (`python -m vae run --mode {vlog|shorts}`)
- [ ] **모드 1: 브이로그** — 무음 제거 + 자막 + 씬 단위 정리 + 16:9 유지
- [ ] **모드 2: 숏폼** — 하이라이트 추출 + 9:16 자동 크롭 + 비트 컷 + 강조 자막
- [ ] CapCut Windows 버전 draft 출력 (한 가지 버전 고정)
- [ ] 분석 리포트 (`analysis_report.json`) — 왜 그렇게 잘랐는지 추적 가능

### Out of Scope (v0)
- ❌ 최종 영상 자체 렌더링 (CapCut export에 위임)
- ❌ CapCut Mac 버전 (Windows만)
- ❌ GUI (CLI만)
- ❌ 클라우드 처리 (전부 로컬)
- ❌ 다국어 자막 (한국어 + 영어만)

## 4. 사용자 시나리오

### S1. 브이로그 편집 (강의/일상)
```
1. 사용자: 1시간 분량 클립 5개를 ./clips/에 넣음
2. 사용자: python -m vae run --mode vlog --input ./clips --output ./out
3. 시스템: 12분 처리 (무음 감지 → Whisper → 씬 분석 → draft 생성)
4. 사용자: CapCut에서 ./out/capcut_project 열기
5. 사용자: 자막 위치 조정, 어색한 컷 2~3개 수정 (10분)
6. 사용자: Export → 완성
```

### S2. 숏폼 양산 (하이라이트)
```
1. 사용자: 30분 게임/토크 영상 1개를 ./clips/에 넣음
2. 사용자: python -m vae run --mode shorts --input ./clips --output ./out
3. 시스템: 5분 처리 (피크 감지 → 60초 후보 3개 추출 → 9:16 크롭 → 강조 자막)
4. 사용자: 3개 draft 중 마음에 드는 거 CapCut에서 미세조정
5. 사용자: 인스타 릴스/유튜브 쇼츠 업로드
```

## 5. 우선순위 (MoSCoW)

### Must
- M1. FFmpeg 무음 감지 → 컷 좌표 산출
- M2. Whisper STT → SRT + 단어 단위 타임스탬프
- M3. CapCut draft_content.json 생성 (최소 스키마)
- M4. CLI 골격 (vlog / shorts 모드 분기)

### Should
- S1. PySceneDetect 씬 전환 감지
- S2. 자막 스타일 자동 적용 (vlog: 하단 / shorts: 중앙 강조)
- S3. 9:16 자동 크롭 (얼굴/객체 트래킹)
- S4. 분석 리포트 JSON

### Could
- C1. librosa 비트 감지 → 비트 컷
- C2. 하이라이트 자동 선별 (볼륨 피크 + STT 키워드)
- C3. MediaPipe 얼굴 감지 기반 크롭 개선
- C4. 중복 프레임 제거 (pHash)

### Won't (v0)
- W1. GUI
- W2. 클라우드 렌더링
- W3. CapCut Mac/모바일
- W4. 효과/트랜지션 라이브러리 (CapCut 기본만)

## 6. 기술 스택

| 분야 | 도구 | 비고 |
|------|------|------|
| 영상 처리 | FFmpeg + ffmpeg-python | 무음 감지, 세그먼트 추출 |
| STT | faster-whisper (CUDA) | RTX 가속, large-v3 모델 |
| 씬 감지 | PySceneDetect | content/threshold 모드 |
| 오디오 분석 | librosa | 비트, RMS 피크 |
| 비전 | OpenCV + MediaPipe | 얼굴 트래킹, 모션 분석 |
| CLI | Click | 서브커맨드 구조 |
| 언어 | Python 3.10+ | |

## 7. 리스크

| # | 리스크 | 대응 |
|---|--------|------|
| R1 | CapCut draft 스키마가 버전마다 다름 | 사용 CapCut 버전 고정, 스키마 분석 문서화 |
| R2 | Whisper large 모델 GPU 메모리 부족 | medium / small 폴백 옵션 |
| R3 | 무음 제거가 너무 공격적이라 부자연스러움 | fade in/out, 최소 클립 길이 옵션 |
| R4 | 9:16 크롭 시 중요 객체 잘림 | 얼굴 트래킹 + 사용자 오버라이드 |
| R5 | 1시간 영상 처리 시간 초과 | 모듈별 캐싱, 병렬 처리 |

## 8. 마일스톤

| M | 산출물 | 기한 (목표) | 상태 |
|---|--------|-------------|------|
| M0 | 프로젝트 초기화 + GitHub 푸시 | 2026-05-27 | ✅ |
| M1 | PDCA Design 완료 | +3일 | ✅ |
| M2 | CapCut draft 스키마 분석 완료 | +5일 | ⏳ (사용자 샘플 대기) |
| M3 | 무음 제거 PoC | +7일 | ✅ Phase 1 |
| M4 | Whisper STT 통합 | +10일 | ✅ Codex 위임 |
| M5 | 브이로그 모드 E2E 동작 | +14일 | ✅ Phase 2 |
| M6 | 숏폼 모드 E2E 동작 | +21일 | ✅ Phase 3 |
| M7 | gap-detector 검증 ≥ 90% | +25일 | ✅ Phase 4 (89→~92%) |
| **M8** | **Web GUI + GitHub Pages 배포** | 2026-05-28 | ✅ Phase 5 |
| **M9** | **100 % 자동 렌더 (FFmpeg)** | 2026-05-28 | ✅ Phase 5 |

→ **MoSCoW Must/Should 전부 완료**. CapCut 실 스키마(M2)는 사용자 액션 대기.

## 9. 다음 단계 (즉시)

1. ✅ 프로젝트 초기화 (이 문서 작성 포함)
2. ✅ GitHub 푸시
3. ⏭️ 샘플 영상 확보 (Pexels/Pixabay 무료 영상)
4. ⏭️ CapCut에서 빈 프로젝트 1개 저장 → 경로 알려주기 (스키마 분석용)
5. ⏭️ `/pdca design video-auto-editor` 진행

## 10. 협업 구조

- **Claude Code** — 설계, 통합, 검증, PDCA 관리, 디버깅
- **Codex** — 모듈 단위 구현 (`audio_analyzer.py`, `transcriber.py` 등), 최적화
- **사용자** — 의사결정, 샘플 영상 제공, CapCut에서 결과 검증
