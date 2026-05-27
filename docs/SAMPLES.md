# 샘플 영상 확보 가이드

PoC/테스트용 무료 영상 확보 방법.

## 1. 브이로그 모드 테스트용 (긴 영상, 5분 이상)

말하는 사람 + 무음 구간 + 다양한 씬이 섞인 영상이 좋다.

### 추천 소스
- **YouTube 본인 영상** — 본인이 찍은 거 있으면 최고
- **Pexels Videos** — https://www.pexels.com/videos/ (CC0, 무료)
  - 검색어: "interview", "vlog", "talking", "monologue"
- **Pixabay Videos** — https://pixabay.com/videos/ (무료)
- **YouTube Creative Commons** — 검색 필터 → 라이선스 → Creative Commons

### 다운로드 (yt-dlp)
```bash
# yt-dlp 설치 (Windows)
winget install yt-dlp

# 영상 다운로드 (mp4, 720p)
yt-dlp -f "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]" -o "clips/%(title)s.%(ext)s" <URL>
```

## 2. 숏폼 모드 테스트용 (짧고 강렬, 30초~3분)

피크/하이라이트가 있는 영상이 좋다.

### 추천 소스
- **YouTube 게임 하이라이트** — 환호/킬소리 등 피크 명확
- **Pexels: action / sports / dance**

## 3. 폴더 구조

```
C:\tmp\video-auto-editor\
  └─ clips/              ← .gitignore로 제외됨
       ├─ vlog_sample_01.mp4    (긴 영상, 브이로그 테스트용)
       ├─ vlog_sample_02.mp4
       └─ shorts_sample_01.mp4  (짧은 영상, 숏폼 테스트용)
```

## 4. CapCut Draft 스키마 분석용 샘플

이건 별도 작업. 사용자가 직접:

1. CapCut 데스크탑 실행
2. 새 프로젝트 생성 (아무 영상 1개 추가)
3. 자막 1개, 효과 1개, 트랜지션 1개 추가
4. 저장 후 닫기
5. 폴더 경로 확인:
   ```
   C:\Users\ROSSA\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft\
   ```
6. 가장 최근 폴더 이름을 Claude에게 알려주기 → `draft_content.json` 구조 분석

⚠️ **`capcut_samples/` 폴더는 .gitignore로 제외**되어 있음 (개인 경로/메타데이터 포함 가능).

## 5. 라이선스 주의

- Pexels/Pixabay: 상업적 사용 가능, 출처 표기 권장
- YouTube 일반 영상: 다운로드 자체는 약관 위반, **본인 영상만** 권장
- 본인 영상: 무제한
