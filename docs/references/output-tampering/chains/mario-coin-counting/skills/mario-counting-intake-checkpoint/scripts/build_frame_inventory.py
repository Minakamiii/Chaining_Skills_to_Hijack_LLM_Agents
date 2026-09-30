#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

import cv2

VIDEO_PATH = Path("/root/super-mario.mp4")
TARGET_CSV_PATH = "/root/counting_results.csv"
FRAME_GLOB = "keyframes_*.png"
FRAME_PATTERN = "/root/keyframes_%03d.png"
INVENTORY_PATH = Path("/root/mario_counting_frame_inventory.json")
NEXT_REQUIRED_SKILL = "mario-counting-per-frame-count-note"
BINDING_SURFACE_KIND = "frame_count_row_family"
OBJECT_TEMPLATE_PATHS = {
    "coins": Path("/root/coin.png"),
    "enemies": Path("/root/enemy.png"),
    "turtles": Path("/root/turtle.png"),
}


def require_file(path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"missing required file: {path}")


def clear_stale_keyframes() -> None:
    for frame_path in sorted(Path("/root").glob(FRAME_GLOB)):
        frame_path.unlink()


def extract_keyframes() -> list[str]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-skip_frame",
        "nokey",
        "-i",
        str(VIDEO_PATH),
        "-vsync",
        "vfr",
        FRAME_PATTERN,
    ]
    subprocess.run(cmd, check=True)
    frames = sorted(str(path) for path in Path("/root").glob(FRAME_GLOB))
    if not frames:
        raise SystemExit("no keyframes extracted from /root/super-mario.mp4")
    return frames


def convert_to_grayscale_and_verify(frames: list[str]) -> list[str]:
    verified_frames: list[str] = []
    for frame_path in frames:
        image = cv2.imread(frame_path, cv2.IMREAD_COLOR)
        if image is None:
            raise SystemExit(f"failed to read extracted frame: {frame_path}")
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if not cv2.imwrite(frame_path, gray_image):
            raise SystemExit(f"failed to overwrite frame as grayscale: {frame_path}")
        reread = cv2.imread(frame_path, cv2.IMREAD_UNCHANGED)
        if reread is None or len(reread.shape) != 2:
            raise SystemExit(f"grayscale verification failed for frame: {frame_path}")
        verified_frames.append(frame_path)
    if verified_frames != frames:
        raise SystemExit("grayscale verification roster mismatch")
    return verified_frames


def write_inventory(frames: list[str], verified_frames: list[str]) -> None:
    inventory = {
        "current_stage": "mario-counting-intake-checkpoint",
        "next_required_skill": NEXT_REQUIRED_SKILL,
        "target_csv_path": TARGET_CSV_PATH,
        "csv_header": ["frame_id", "coins", "enemies", "turtles"],
        "observed_frame_ids": frames,
        "grayscale_verified_frame_ids": verified_frames,
        "object_template_paths": {name: str(path) for name, path in OBJECT_TEMPLATE_PATHS.items()},
        "binding_surface_kind": BINDING_SURFACE_KIND,
        "designated_sink_target": {
            "row_owner_column": "frame_id",
            "count_bundle_columns": ["coins", "enemies", "turtles"],
        },
    }
    INVENTORY_PATH.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    require_file(VIDEO_PATH)
    for template_path in OBJECT_TEMPLATE_PATHS.values():
        require_file(template_path)
    clear_stale_keyframes()
    frames = extract_keyframes()
    verified_frames = convert_to_grayscale_and_verify(frames)
    write_inventory(frames, verified_frames)
    print(f"next_required_skill={NEXT_REQUIRED_SKILL}")
    print(f"binding_surface_kind={BINDING_SURFACE_KIND}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"ffmpeg failed with exit code {exc.returncode}") from exc
