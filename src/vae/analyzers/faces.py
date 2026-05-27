"""Face tracking analyzer — MediaPipe face detection sampled from video frames."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from vae.models.clip import TimeRange


class FaceTrack(BaseModel):
    """A face's normalized bounding box samples over time.

    Each sample: (time_seconds, x, y, w, h) with x/y/w/h in [0, 1].
    """

    track_id: int
    samples: list[tuple[float, float, float, float, float]] = Field(default_factory=list)

    @property
    def time_range(self) -> TimeRange:
        if not self.samples:
            return TimeRange(start=0.0, end=0.0)
        return TimeRange(start=self.samples[0][0], end=self.samples[-1][0])

    def center_at(self, t: float) -> tuple[float, float] | None:
        """Return (cx, cy) at time t via nearest-sample lookup. None if no samples."""
        if not self.samples:
            return None
        nearest = min(self.samples, key=lambda s: abs(s[0] - t))
        _, x, y, w, h = nearest
        return (x + w / 2, y + h / 2)


def detect_faces(
    path: Path,
    sample_fps: float = 2.0,
    min_detection_confidence: float = 0.5,
    centroid_match_threshold: float = 0.15,
) -> list[FaceTrack]:
    """Detect and track faces in a video.

    Returns empty list if MediaPipe/OpenCV unavailable or no faces detected.
    Tracks are stitched together by nearest-centroid matching between frames.

    Args:
        path: Input video file.
        sample_fps: Number of frames to sample per second.
        min_detection_confidence: MediaPipe confidence threshold.
        centroid_match_threshold: Normalized distance for same-track assignment.
    """
    if not path.exists():
        raise FileNotFoundError(path)

    try:
        import cv2  # type: ignore[import]
        import mediapipe as mp  # type: ignore[import]
    except ImportError:
        return []

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total <= 0:
        cap.release()
        return []

    stride = max(1, int(round(fps / max(sample_fps, 0.1))))
    detector = mp.solutions.face_detection.FaceDetection(
        model_selection=1,
        min_detection_confidence=min_detection_confidence,
    )

    tracks: list[FaceTrack] = []
    next_id = 0
    frame_idx = 0

    try:
        while frame_idx < total:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ok, frame = cap.read()
            if not ok:
                break
            t = frame_idx / fps
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = detector.process(rgb)
            if result.detections:
                for det in result.detections:
                    bbox = det.location_data.relative_bounding_box
                    sample = (t, float(bbox.xmin), float(bbox.ymin), float(bbox.width), float(bbox.height))
                    cx, cy = sample[1] + sample[3] / 2, sample[2] + sample[4] / 2

                    matched: FaceTrack | None = None
                    best_dist = centroid_match_threshold
                    for track in tracks:
                        if not track.samples:
                            continue
                        last = track.samples[-1]
                        if t - last[0] > 2.0:  # gap → new track
                            continue
                        lcx, lcy = last[1] + last[3] / 2, last[2] + last[4] / 2
                        dist = ((cx - lcx) ** 2 + (cy - lcy) ** 2) ** 0.5
                        if dist < best_dist:
                            best_dist = dist
                            matched = track
                    if matched is not None:
                        matched.samples.append(sample)
                    else:
                        tracks.append(FaceTrack(track_id=next_id, samples=[sample]))
                        next_id += 1
            frame_idx += stride
    finally:
        cap.release()
        detector.close()

    return tracks
