#!/usr/bin/env python3
import os
import subprocess
import time
import urllib.request
import json

ARTIFACT_DIR = "/home/sk1029/.gemini/antigravity-ide/brain/7489b000-849e-45bb-b511-7bb7659edd14"
WORKSPACE_DIR = "/home/sk1029/Documents/projects/wemakedevs"
FRAMES_DIR = "/tmp/walkthrough_frames"
PROFILE_DIR = "/tmp/ff_walkthrough_gen_profile"

os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(PROFILE_DIR, exist_ok=True)

# 1. Reset database to fresh seed state
print("[1/5] Seeding FalkorDB graph...")
subprocess.run([f"{WORKSPACE_DIR}/.venv/bin/python3", "-m", "oracle.seed_data"], cwd=WORKSPACE_DIR, check=True)

# 2. Stages to capture
STAGES = [
    ("01_overview", "overview", 3.5),
    ("02_step1_context", "step_1", 3.5),
    ("03_step2_causes", "step_2", 3.5),
    ("04_step3_deployments", "step_3", 3.5),
    ("05_step4_evidence", "step_4", 4.0),
    ("06_step5_blast_radius", "step_5", 4.0),
    ("07_step6_service_owner", "step_6", 3.5),
    ("08_step7_hypotheses", "step_7", 4.0),
    ("09_policy_rejection", "policy_rejection", 4.0),
    ("10_policy_approval", "policy_approval", 4.0),
    ("11_audit_verification", "audit_verification", 4.0),
    ("12_inc3022_redis", "multi_incident_1", 4.0),
    ("13_inc5102_logistics", "multi_incident_2", 4.0),
    ("14_complete", "complete", 4.5),
]

print(f"[2/5] Capturing {len(STAGES)} 1080p frames via Firefox engine...")

# Execute real approval before audit verification frame
approval_done = False

for idx, (frame_name, stage_id, duration) in enumerate(STAGES):
    output_png = f"{FRAMES_DIR}/{frame_name}.png"
    url = f"http://localhost:8000?stage={stage_id}&snapshot=1"

    # If entering audit verification, trigger the real approval endpoint
    if stage_id == "audit_verification" and not approval_done:
        try:
            req_data = json.dumps({
                "approver": "Sarah Connor (Staff SRE)",
                "notes": "Verified connection pool starvation in telemetry. Rollback approved."
            }).encode('utf-8')
            req = urllib.request.Request(
                "http://localhost:8000/actions/act-sim-4091-rollback/approve",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=5)
            approval_done = True
        except Exception as e:
            print(f"Approval call notice: {e}")

    cmd = [
        "firefox",
        "--headless",
        "--new-instance",
        "--profile", PROFILE_DIR,
        "--screenshot", output_png,
        "--window-size", "1920,1080",
        url
    ]
    print(f"  [{idx+1}/{len(STAGES)}] Capturing {stage_id} -> {output_png}...")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

print("[3/5] Generating frame duplicate inputs for smooth video timing...")
# Create concat script for ffmpeg with exact durations
concat_file = f"{FRAMES_DIR}/input.txt"
with open(concat_file, "w") as f:
    for frame_name, stage_id, duration in STAGES:
        png_path = f"{FRAMES_DIR}/{frame_name}.png"
        f.write(f"file '{png_path}'\n")
        f.write(f"duration {duration}\n")
    # Last file must be repeated for ffmpeg concat demuxer
    last_png = f"{FRAMES_DIR}/{STAGES[-1][0]}.png"
    f.write(f"file '{last_png}'\n")

# 4. Compile MP4 with ffmpeg
mp4_out = f"{ARTIFACT_DIR}/impactgraph_walkthrough.mp4"
workspace_mp4 = f"{WORKSPACE_DIR}/walkthrough_demo.mp4"
webp_out = f"{ARTIFACT_DIR}/impactgraph_walkthrough.webp"

print(f"[4/5] Encoding high-definition 1080p MP4 to {mp4_out}...")
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", concat_file,
    "-vsync", "vfr",
    "-pix_fmt", "yuv420p",
    "-c:v", "libopenh264",
    "-b:v", "2500k",
    mp4_out
]
subprocess.run(ffmpeg_cmd, check=True)
subprocess.run(["cp", mp4_out, workspace_mp4], check=True)

print(f"[5/5] Encoding animated WebP preview to {webp_out}...")
webp_cmd = [
    "ffmpeg", "-y",
    "-i", mp4_out,
    "-vf", "fps=6,scale=960:-1:flags=lanczos",
    "-c:v", "libwebp_anim",
    "-loop", "0",
    webp_out
]
subprocess.run(webp_cmd, check=True)

print("\nAll artifacts generated successfully!")
for path in [mp4_out, workspace_mp4, webp_out]:
    if os.path.exists(path):
        size = os.path.getsize(path) / (1024 * 1024)
        print(f"  - {path} ({size:.2f} MB)")
