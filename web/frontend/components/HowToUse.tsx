export default function HowToUse() {
  const repo = "https://github.com/aijunny0604-alt/video-auto-editor";
  return (
    <section className="rounded-xl border border-neutral-800 bg-neutral-900/40 p-6">
      <h2 className="mb-1 text-xl font-bold">🛠️ 내 영상으로 만들려면?</h2>
      <p className="mb-5 text-sm text-neutral-400">
        이 페이지는 미리보기예요. 실제로 본인 영상으로 돌리려면 로컬에 한 번만 세팅하면 돼요.
      </p>

      <ol className="space-y-5">
        <li>
          <p className="mb-1 text-sm font-semibold text-emerald-400">1. 사전 준비</p>
          <ul className="ml-4 list-disc space-y-1 text-sm text-neutral-300">
            <li>Python 3.10+, Node.js 20+, Git 설치</li>
            <li>
              FFmpeg 설치 (Windows): <code className="rounded bg-black/50 px-1.5">winget install Gyan.FFmpeg</code>
            </li>
            <li>NVIDIA GPU 있으면 Whisper 자막이 5~10배 빨라짐 (선택)</li>
          </ul>
        </li>

        <li>
          <p className="mb-1 text-sm font-semibold text-emerald-400">2. 레포 클론 + 설치</p>
          <pre className="rounded-lg bg-black/60 p-3 font-mono text-xs leading-relaxed text-neutral-300">
{`git clone ${repo}
cd video-auto-editor

# Python 백엔드
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
pip install -r web/backend/requirements.txt

# 프론트엔드
cd web/frontend
npm install`}
          </pre>
        </li>

        <li>
          <p className="mb-1 text-sm font-semibold text-emerald-400">3. 두 서버 띄우기 (터미널 2개)</p>
          <pre className="rounded-lg bg-black/60 p-3 font-mono text-xs leading-relaxed text-neutral-300">
{`# 터미널 1 — 백엔드
$env:PYTHONPATH = "src"
uvicorn web.backend.app:app --host 127.0.0.1 --port 8000 --reload

# 터미널 2 — 프론트
cd web/frontend
npm run dev`}
          </pre>
          <p className="mt-1.5 text-xs text-neutral-500">
            브라우저: <code className="rounded bg-black/50 px-1.5">http://localhost:3000</code> →
            폼에서 입력/출력 폴더 지정 → ▶ 실행
          </p>
        </li>

        <li>
          <p className="mb-1 text-sm font-semibold text-emerald-400">4. 영상 폴더 준비</p>
          <ul className="ml-4 list-disc space-y-1 text-sm text-neutral-300">
            <li>
              원본 영상을 한 폴더에 모아두기 (예:{" "}
              <code className="rounded bg-black/50 px-1.5">C:\Users\내이름\Videos\원본</code>)
            </li>
            <li>지원 포맷: mp4, mov, mkv, avi, webm, wav, mp3, m4a</li>
            <li>출력 폴더는 비어있어도 됨 — 자동 생성</li>
          </ul>
        </li>

        <li>
          <p className="mb-1 text-sm font-semibold text-emerald-400">5. 모드 고르기</p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-neutral-800 bg-neutral-950/60 p-3">
              <p className="text-sm font-semibold">🎒 브이로그 (vlog)</p>
              <p className="mt-1 text-xs text-neutral-400">
                긴 영상에서 무음 자동 제거 + 한국어 자막. 16:9 유지. 강의·일상·튜토리얼.
              </p>
            </div>
            <div className="rounded-lg border border-neutral-800 bg-neutral-950/60 p-3">
              <p className="text-sm font-semibold">⚡ 숏폼 (shorts)</p>
              <p className="mt-1 text-xs text-neutral-400">
                하이라이트 자동 추출 + 9:16 세로 크롭 + 빠른 컷. 쇼츠·릴스·틱톡.
              </p>
            </div>
          </div>
        </li>

        <li>
          <p className="mb-1 text-sm font-semibold text-emerald-400">6. 결과 활용</p>
          <ul className="ml-4 list-disc space-y-1 text-sm text-neutral-300">
            <li>
              <code className="rounded bg-black/50 px-1.5">analysis_report.json</code> — 어디서 어디까지
              잘랐는지 전부 기록 (CapCut에서 수동 미세조정 시 참고)
            </li>
            <li>
              <code className="rounded bg-black/50 px-1.5">subtitles.srt</code> — Whisper STT 켰을 때
              자동 생성. CapCut/Premiere에 드래그&드롭
            </li>
            <li>
              <code className="rounded bg-black/50 px-1.5">capcut_project/draft.json</code> — CapCut
              데스크탑 draft 메타 (스키마 매핑은 v0.2 작업 중)
            </li>
          </ul>
        </li>
      </ol>

      <div className="mt-6 rounded-lg border border-neutral-800 bg-black/40 p-4 text-xs text-neutral-400">
        <p className="mb-1.5 font-semibold text-neutral-300">💡 CLI만 쓰고 싶다면</p>
        <pre className="font-mono text-neutral-300">
{`python -m vae run --mode vlog   --input ./clips --output ./out --stt
python -m vae run --mode shorts --input ./clips --output ./out --shorts-count 3`}
        </pre>
      </div>

      <p className="mt-5 text-center text-xs text-neutral-500">
        문제 생기면 <a href={`${repo}/issues`} className="text-emerald-400 underline">GitHub Issues</a>{" "}
        에 올리거나 <a href={`${repo}/blob/main/web/README.md`} className="text-emerald-400 underline">web/README.md</a>{" "}
        참고
      </p>
    </section>
  );
}
