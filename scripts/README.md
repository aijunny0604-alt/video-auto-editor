# scripts/

Windows에서 클릭 한 번으로 video-auto-editor를 띄우는 런처들.

## 처음 한 번만

```
scripts\setup.bat
```

- Python 3.10+, Node 20+, FFmpeg가 PATH에 있는지 확인
- `.venv` 가상환경 + Python 의존성 설치
- `web/frontend/node_modules` 설치

## 매번 (편집기 열기)

### 가장 쉬운 방법
바탕화면에 바로가기 만들기 (한 번만):
```
scripts\create-desktop-shortcut.bat
```
→ 그 다음부터는 바탕화면의 **video-auto-editor** 아이콘 더블클릭

### 직접 실행
```
scripts\open-editor.bat
```

`open-editor.bat`이 하는 일:
1. 8000 / 3000 포트 점유 프로세스 자동 종료
2. 백엔드(FastAPI, 포트 8000) 새 창에서 시작
3. 프론트엔드(Next.js, 포트 3000) 새 창에서 시작
4. 6초 후 브라우저로 `http://localhost:3000` 자동 열기

## 종료

두 터미널 창 닫기 OR:
```
scripts\stop-editor.bat
```

## 대안 (PowerShell 선호 시)

```powershell
pwsh -ExecutionPolicy Bypass -File scripts\open-editor.ps1
```

## 트러블슈팅

| 증상 | 원인 / 해결 |
|------|------------|
| "venv not found" | `scripts\setup.bat` 실행 |
| "node_modules missing" | `scripts\setup.bat` 실행 |
| 브라우저는 떴는데 회색 화면 / 에러 | 5~10초 더 기다리기 (Next.js 첫 빌드) → `Ctrl+Shift+R` |
| WebSocket 빨간 점 | 백엔드 창에서 에러 확인 (FFmpeg PATH 등) |
| 8000/3000 이미 사용 중 | `scripts\stop-editor.bat` 한 번 실행 후 재시도 |
