# CapCut Draft Schema 분석

> 상태: **TODO — 샘플 프로젝트 대기**
> 경로: `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\`

## 현재 상태 (2026-05-27)

폴더 스캔 결과: `root_meta_info.json` 만 존재.
→ CapCut 데스크탑에서 **프로젝트가 한 번도 생성된 적 없음**.

## 분석을 위한 사용자 작업

1. CapCut 데스크탑 실행
2. **새 프로젝트** → 아무 영상 1개 드래그
3. 다음 요소 1개씩 추가:
   - 자막 1개 (텍스트 + 폰트 변경)
   - 효과 1개 (예: 비네팅)
   - 트랜지션 1개 (두 클립 사이)
4. 저장 후 CapCut 종료
5. 위 경로에서 새로 생긴 UUID 폴더 확인 → 그 안의 `draft_content.json` 분석 시작

## 분석 시 채워야 할 항목 (체크리스트)

- [ ] 최상위 키 (`tracks`, `materials`, `canvas_config` 등)
- [ ] 시간 단위 (μs / ms / s?)
- [ ] 트랙 종류 (video / audio / text / effect / sticker / transition)
- [ ] Segment 구조 (start, duration, source_timerange, target_timerange)
- [ ] Material reference 방식 (UUID, 별도 materials 배열?)
- [ ] 자막 스타일 (font, size, color, position, animation)
- [ ] 효과/트랜지션의 ID 체계 (내장 효과 ID 카탈로그 필요?)
- [ ] 캔버스 비율 (16:9, 9:16 설정 위치)
- [ ] 미디어 파일 절대 경로 vs 상대 경로

## 폴백 옵션

스키마가 너무 복잡하거나 자주 바뀌면:
- **템플릿 모드** — 사용자가 만든 템플릿의 미디어 슬롯만 교체
- **OTIO 경유** — OpenTimelineIO로 만들고 CapCut import (지원 확인 필요)
