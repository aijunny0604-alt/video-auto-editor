"use client";

import { forwardRef, useImperativeHandle, useRef, useState } from "react";

export type VideoTab = {
  key: string;
  label: string;
  src: string;
  ratio?: "16-9" | "9-16";
  caption?: string;
};

export type VideoPlayerHandle = {
  jumpToOriginal: (timeSeconds: number) => void;
};

type Props = { tabs: VideoTab[] };

const VideoPlayer = forwardRef<VideoPlayerHandle, Props>(function VideoPlayer(
  { tabs },
  ref,
) {
  const [active, setActive] = useState(tabs[0]?.key ?? "");
  const videoRefs = useRef<Record<string, HTMLVideoElement | null>>({});

  useImperativeHandle(ref, () => ({
    jumpToOriginal: (t: number) => {
      const originalKey = tabs.find((tab) => tab.ratio === "16-9")?.key ?? tabs[0]?.key;
      if (!originalKey) return;
      setActive(originalKey);
      const v = videoRefs.current[originalKey];
      if (v) {
        v.currentTime = Math.max(0, t);
        v.play().catch(() => undefined);
      }
    },
  }));

  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">영상 미리보기</h3>
        <div className="flex gap-1.5">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActive(tab.key)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${
                active === tab.key
                  ? "bg-emerald-500 text-black"
                  : "bg-neutral-800 text-neutral-300 hover:bg-neutral-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-start justify-center gap-4">
        {tabs.map((tab) => {
          const isActive = active === tab.key;
          const isVertical = tab.ratio === "9-16";
          return (
            <div
              key={tab.key}
              className={`${isActive ? "block" : "hidden"} w-full max-w-md`}
            >
              <div
                className={`overflow-hidden rounded-lg bg-black ${
                  isVertical ? "mx-auto aspect-[9/16] max-w-[240px]" : "aspect-video"
                }`}
              >
                <video
                  ref={(el) => {
                    videoRefs.current[tab.key] = el;
                  }}
                  src={tab.src}
                  controls
                  preload="metadata"
                  playsInline
                  className="h-full w-full"
                />
              </div>
              {tab.caption && (
                <p className="mt-2 text-center text-xs text-neutral-500">{tab.caption}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
});

export default VideoPlayer;
