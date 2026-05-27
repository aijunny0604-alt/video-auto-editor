# video-auto-editor

브이로그/숏폼(쇼츠·릴스)용 자동 컷편집 파이프라인.
폴더의 원본 클립을 분석해서 무음 제거·자막·하이라이트 컷·세로 크롭까지 처리한 뒤,
CapCut 데스크탑에서 바로 열 수 있는 draft 프로젝트로 출력합니다.

## 흐름

```
[원본 클립 폴더]
    ↓ FFmpeg silencedetect      (무음 구간)
    ↓ Whisper (CUDA)            (STT, 자막)
    ↓ PySceneDetect             (씬 전환)
    ↓ librosa / OpenCV          (비트, 모션, 얼굴)
    ↓ 모드별 룰 적용             (vlog / shorts)
[CapCut draft_content.json]
    ↓ CapCut 열기 → 미세조정 → Export
```

## 모드

| 모드 | 길이 | 비율 | 컷 길이 | 자막 스타일 |
|------|------|------|--------|------------|
| `vlog` | 5~15분 | 16:9 | 3~10s | 하단 깔끔 |
| `shorts` | 15~60s | 9:16 (자동 크롭) | 0.5~2s | 중앙 강조 |

## 사용 예 (계획)

```bash
python -m vae run --mode shorts --input ./clips --output ./out
python -m vae run --mode vlog   --input ./clips --output ./out
```

## 상태

- [x] 프로젝트 초기화
- [ ] PDCA Plan / Design
- [ ] 모듈 구현 (audio / stt / scene / crop / capcut_writer)
- [ ] CapCut draft 스키마 분석
- [ ] E2E 검증

## 협업

- **Claude Code** — 설계, 통합, 검증, PDCA 관리
- **Codex** — 모듈 단위 구현, 최적화
