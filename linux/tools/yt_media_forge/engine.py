# [FL_INDEX: keywords="youtube, video_render, ffmpeg, edge_tts, audio_synthesis, shorts, automation" | purpose="Sovereign CLI engine for neural TTS audio synthesis and FFmpeg video assembly"]
import os
import sys
import json
import asyncio
import subprocess
import shutil

async def synthesize_voiceover(text, voice, output_audio, output_srt=None):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    if output_srt:
        sub_maker = edge_tts.SubMaker()
        with open(output_audio, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    sub_maker.feed(chunk)
        with open(output_srt, "w", encoding="utf-8") as f:
            f.write(sub_maker.get_srt())
    else:
        await communicate.save(output_audio)
    return os.path.exists(output_audio)

def render_slideshow_video(scenes, audio_path, output_mp4, resolution="1080x1920", fps=30):
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    try:
        dur_out = subprocess.check_output(probe_cmd, text=True).strip()
        total_audio_dur = float(dur_out)
    except Exception:
        total_audio_dur = 10.0

    width, height = resolution.split("x")
    inputs = []
    
    ffmpeg_cmd = ["ffmpeg", "-y"]
    if not scenes or len(scenes) == 0:
        ffmpeg_cmd.extend(["-f", "lavfi", "-i", f"color=c=0x12141a:s={resolution}:d={total_audio_dur}"])
    else:
        n_scenes = len(scenes)
        dur_per_scene = total_audio_dur / n_scenes
        filter_complex = []
        concat_inputs = []
        for i, sc in enumerate(scenes):
            img = sc.get("image")
            inputs.extend(["-loop", "1", "-t", str(dur_per_scene), "-i", img])
            filter_complex.append(f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]")
            concat_inputs.append(f"[v{i}]")
        filter_complex.append(f"{''.join(concat_inputs)}concat=n={n_scenes}:v=1:a=0[vcat]")
        ffmpeg_cmd.extend(inputs)
        ffmpeg_cmd.extend(["-filter_complex", ";".join(filter_complex), "-map", "[vcat]"])

    ffmpeg_cmd.extend([
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_mp4
    ])

    proc = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return {
        "success": proc.returncode == 0,
        "exit_code": proc.returncode,
        "output_file": output_mp4 if proc.returncode == 0 else None,
        "error": proc.stderr if proc.returncode != 0 else None
    }

def sample_audio_stream(url, start_offset=0, duration=10, output_path=None):
    if not output_path:
        scratch_dir = os.path.join(os.getcwd(), ".FL_BIN", "scratch")
        output_path = os.path.join(scratch_dir, f"sample_stream_{int(start_offset)}s.mp3")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Cap duration to max 30s to prevent unbounded execution
    duration = min(max(int(duration), 1), 30)
    
    # Step 1: Extract direct audio stream URL via yt-dlp in <10s
    try:
        ytdlp_proc = subprocess.run(
            ["yt-dlp", "-g", "-f", "bestaudio", "--socket-timeout", "10", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15
        )
        if ytdlp_proc.returncode != 0:
            return {"success": False, "error": f"yt-dlp stream resolution failed: {ytdlp_proc.stderr.strip()}"}
        stream_url = ytdlp_proc.stdout.strip().splitlines()[0]
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "yt-dlp stream resolution timed out after 15s"}
    except Exception as e:
        return {"success": False, "error": f"Failed to resolve stream URL: {str(e)}"}
        
    # Step 2: Grab exact slice via ffmpeg directly from stream URL in <25s
    try:
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_offset),
            "-i", stream_url,
            "-t", str(duration),
            "-vn",
            "-c:a", "libmp3lame",
            "-q:a", "4",
            "-nostats",
            "-loglevel", "error",
            output_path
        ]
        ff_proc = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=25)
        if ff_proc.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return {
                "success": True,
                "output_path": output_path,
                "file_size_bytes": os.path.getsize(output_path),
                "duration_seconds": duration,
                "start_offset": start_offset
            }
        else:
            return {"success": False, "error": f"FFmpeg sampling failed: {ff_proc.stderr.strip()}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "FFmpeg audio sampling timed out after 25s"}
    except Exception as e:
        return {"success": False, "error": f"Failed to sample audio stream: {str(e)}"}

def main():
    if len(sys.argv) > 1 and sys.argv[1].startswith("{"):
        payload = json.loads(sys.argv[1])
    else:
        print(json.dumps({
            "status": "online",
            "engine": "yt_media_forge",
            "ffmpeg": bool(shutil.which("ffmpeg")),
            "edge_tts": True
        }))
        return

    action = payload.get("action", "status")

    if action == "synthesize_audio":
        text = payload.get("script_text", "")
        voice = payload.get("voice", "id-ID-GadisNeural")
        scratch_dir = os.path.join(os.getcwd(), ".FL_BIN", "scratch")
        default_audio = os.path.join(scratch_dir, "voiceover.mp3")
        out_audio = payload.get("output_path", default_audio)
        out_srt = out_audio.rsplit(".", 1)[0] + ".srt"
        os.makedirs(os.path.dirname(os.path.abspath(out_audio)), exist_ok=True)
        
        ok = asyncio.run(synthesize_voiceover(text, voice, out_audio, out_srt))
        print(json.dumps({
            "success": ok,
            "audio_path": out_audio,
            "subtitle_path": out_srt if os.path.exists(out_srt) else None
        }))

    elif action == "sample_audio_stream":
        url = payload.get("url")
        if not url:
            print(json.dumps({"success": False, "error": "Missing 'url' parameter for sample_audio_stream"}))
            return
        start_offset = payload.get("start_offset", 0)
        dur = payload.get("duration", 10)
        out_path = payload.get("output_path")
        result = sample_audio_stream(url, start_offset=start_offset, duration=dur, output_path=out_path)
        print(json.dumps(result))

    elif action in ("render_video", "render_short"):
        res = "1080x1920" if action == "render_short" else "1920x1080"
        audio = payload.get("audio_path")
        scratch_dir = os.path.join(os.getcwd(), ".FL_BIN", "scratch")
        default_mp4 = os.path.join(scratch_dir, "render_output.mp4")
        out_mp4 = payload.get("output_path", default_mp4)
        scenes = payload.get("scenes", [])
        os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
        
        result = render_slideshow_video(scenes, audio, out_mp4, resolution=res)
        print(json.dumps(result))

if __name__ == "__main__":
    main()
