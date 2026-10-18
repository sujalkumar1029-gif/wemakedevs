#!/usr/bin/env bash
set -eo pipefail

ARTIFACT_DIR="/home/sk1029/.gemini/antigravity-ide/brain/7489b000-849e-45bb-b511-7bb7659edd14"
WORKSPACE_DIR="/home/sk1029/Documents/projects/wemakedevs"
MP4_OUTPUT="${ARTIFACT_DIR}/impactgraph_walkthrough.mp4"
WEBP_OUTPUT="${ARTIFACT_DIR}/impactgraph_walkthrough.webp"
WORKSPACE_MP4="${WORKSPACE_DIR}/walkthrough_demo.mp4"

echo "[1/6] Resetting and re-seeding FalkorDB graph data..."
cd "${WORKSPACE_DIR}"
.venv/bin/python3 -m oracle.seed_data

echo "[2/6] Launching Firefox on DISPLAY=:0 with automated walkthrough..."
DISPLAY=:0 firefox --new-instance --kiosk "http://localhost:8000?walkthrough=1" &
FIREFOX_PID=$!
echo "Firefox PID: ${FIREFOX_PID}"

# Allow Firefox window to map and paint
sleep 3

echo "[3/6] Starting FFmpeg 1080p recording for 56 seconds..."
ffmpeg -y -f x11grab -video_size 1920x1080 -i :0 -t 56 \
  -c:v libopenh264 -pix_fmt yuv420p -r 30 \
  "${MP4_OUTPUT}"

echo "[4/6] Terminating Firefox demo window..."
kill "${FIREFOX_PID}" 2>/dev/null || true
pkill -f "firefox.*walkthrough" 2>/dev/null || true

echo "[5/6] Copying MP4 to workspace root..."
cp "${MP4_OUTPUT}" "${WORKSPACE_MP4}"

echo "[6/6] Generating animated WebP for artifact preview..."
ffmpeg -y -i "${MP4_OUTPUT}" \
  -vf "fps=8,scale=960:-1:flags=lanczos" \
  -c:v libwebp_anim -loop 0 \
  "${WEBP_OUTPUT}" || echo "[WARNING] WebP generation skipped"

echo "Video walkthrough generation completed successfully!"
ls -lh "${MP4_OUTPUT}" "${WORKSPACE_MP4}" "${WEBP_OUTPUT}" || true
