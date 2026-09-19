import os
import sys
import time
import shutil
import subprocess
import json

def run_cmd(cmd):
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\nStderr: {p.stderr[:300]}")
    return p

def benchmark_ffmpeg_stitching():
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        print("FFmpeg not found on host PATH. Skipping benchmark.")
        return None

    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bench_tmp")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 1. Generate 3 short H.264 MP4 clips (3 seconds each, 1280x720, silent AAC audio)
        clips = []
        for i in range(3):
            clip_path = os.path.join(temp_dir, f"clip_{i}.mp4")
            color = ["blue", "darkgreen", "purple"][i]
            cmd = (
                f'ffmpeg -y -f lavfi -i color=c={color}:s=1280x720:d=3 -f lavfi -i anullsrc=r=44100:cl=stereo '
                f'-c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -shortest "{clip_path}"'
            )
            run_cmd(cmd)
            clips.append(clip_path)

        # 2. Benchmark Method A: Re-encoding concatenation
        reencode_out = os.path.join(temp_dir, "reencode_out.mp4")
        reencode_cmd = (
            f'ffmpeg -y -i "{clips[0]}" -i "{clips[1]}" -i "{clips[2]}" '
            f'-filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]" '
            f'-map "[v]" -map "[a]" -c:v libx264 -preset medium -c:a aac "{reencode_out}"'
        )
        t0 = time.perf_counter()
        run_cmd(reencode_cmd)
        reencode_duration = time.perf_counter() - t0

        # 3. Benchmark Method B: Lossless Stream-Copy (-c copy)
        list_file = os.path.join(temp_dir, "concat_list.txt")
        with open(list_file, "w") as f:
            for c in clips:
                f.write(f"file '{c.replace(os.sep, '/')}'\n")

        streamcopy_out = os.path.join(temp_dir, "streamcopy_out.mp4")
        streamcopy_cmd = f'ffmpeg -y -f concat -safe 0 -i "{list_file}" -c copy "{streamcopy_out}"'
        t1 = time.perf_counter()
        run_cmd(streamcopy_cmd)
        streamcopy_duration = time.perf_counter() - t1

        speedup = reencode_duration / streamcopy_duration if streamcopy_duration > 0 else 0

        results = {
            "reencode_duration_seconds": round(reencode_duration, 4),
            "stream_copy_duration_seconds": round(streamcopy_duration, 4),
            "measured_speedup_factor": round(speedup, 2)
        }

        eval_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval")
        os.makedirs(eval_dir, exist_ok=True)
        out_json = os.path.join(eval_dir, "stitch_benchmark_results.json")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        print("\n" + "=" * 65)
        print("FFMPEG STITCHING BENCHMARK RESULTS")
        print("=" * 65)
        print(f"  * Re-encoding Concatenation:  {round(reencode_duration, 3)}s")
        print(f"  * Lossless Stream-Copy:       {round(streamcopy_duration, 3)}s")
        print(f"  * Measured Speedup Factor:    {round(speedup, 1)}x faster")
        print("=" * 65 + "\n")
        return results

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    benchmark_ffmpeg_stitching()
