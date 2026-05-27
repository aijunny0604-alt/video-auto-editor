# 개발 환경 세팅

> 🖱️ **그냥 쓰기만 한다면** `scripts/setup.bat` 한 번 → 바탕화면 바로가기 더블클릭으로 끝.
> 이 문서는 코드를 만질 때 필요한 정보입니다.

## 1. 사전 요구사항

| 도구 | 버전 | 설치 |
|------|------|------|
| Python | 3.10+ | https://www.python.org/ |
| Node.js | 20+ (Web GUI) | https://nodejs.org/ |
| FFmpeg | 6.0+ (8.1.1 검증) | `winget install Gyan.FFmpeg` |
| Git | 최신 | https://git-scm.com/ |
| (선택) CUDA | 12.x | NVIDIA 드라이버 + CUDA Toolkit |

### FFmpeg PATH

winget 설치 후 새 셸에서 자동으로 잡히지만, 안 되면 직접 추가:

```
C:\Users\<USER>\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-<버전>-full_build\bin
```

확인:
```bash
ffmpeg -version
```

## 2. 가상환경 + 의존성

```bash
cd C:\tmp\video-auto-editor

# venv 생성
python -m venv .venv

# 활성화 (PowerShell)
.\.venv\Scripts\Activate.ps1

# 활성화 (Git Bash)
source .venv/Scripts/activate

# 최소 의존성 (모델 + CLI + 테스트)
pip install pydantic pytest click

# 전체 의존성 (Whisper, OpenCV 등 포함)
pip install -r requirements.txt
```

### CUDA 가속 Whisper (RTX 보유 시)

```bash
# faster-whisper용 CUDA 빌드된 ctranslate2 자동 설치됨
pip install faster-whisper

# 또는 torch 기반 openai-whisper
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install openai-whisper
```

## 3. 테스트 실행

```bash
# PYTHONPATH 설정 후 pytest
PYTHONPATH=src python -m pytest -q

# 특정 테스트
PYTHONPATH=src python -m pytest tests/test_audio.py -v
```

현재 상태: **11/11 통과** ✅

## 4. CLI 실행

```bash
# 100 % 자동 (기본)
python -m vae run --mode vlog --input ./clips --output ./out

# STT 자막 + 숏폼 3개 추출
python -m vae run --mode shorts --input ./clips --output ./out --stt --shorts-count 3

# 렌더 끄고 CapCut만 (예전 방식)
python -m vae run --mode vlog --input ./clips --output ./out --no-render
```

전체 옵션은 README 참고.

## 4b. Web GUI 실행 (두 터미널)

```powershell
# 터미널 1
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "src"
uvicorn web.backend.app:app --host 127.0.0.1 --port 8000 --reload

# 터미널 2
cd web\frontend
npm install   # 한 번만
npm run dev
```

자동화: `scripts/open-editor.bat` 또는 바탕화면 바로가기.

## 5. 디렉터리 관례

```
./clips/          ← 입력 영상 (gitignored)
./out/            ← 출력 (gitignored)
./samples/        ← 테스트용 영상 (gitignored)
./capcut_samples/ ← CapCut draft 분석용 (gitignored)
./.venv/          ← Python 가상환경 (gitignored)
```

## 6. 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `ffmpeg: command not found` | PATH 미적용 | 새 셸 열거나 PATH 수동 추가 |
| `Cannot find an unused audio input stream` | FFmpeg filter graph 라벨링 누락 | `[a0][a1]...concat` 형태로 명시 |
| Whisper OOM | GPU 메모리 부족 | `model_size="medium"` 또는 `"small"` |
| `ModuleNotFoundError: vae` | PYTHONPATH 미설정 | `PYTHONPATH=src` 추가 또는 `pip install -e .` |
| GUI: 회색 화면 / 자산 404 | Next.js 첫 빌드 8~12초 대기 | `Ctrl+Shift+R` 강력 새로고침 |
| GUI: WebSocket 빨간 점 | 백엔드 죽음 | "vae backend" cmd 창 에러 확인 |
| `bat` 실행 시 "지정된 경로 찾을 수 없다" | 중첩 따옴표 / 옛 버전 | `cebbaac` 이후 수정됨 → 최신 pull |
| 8000 / 3000 포트 점유 | 옛 인스턴스 살아있음 | `scripts/stop-editor.bat` |
