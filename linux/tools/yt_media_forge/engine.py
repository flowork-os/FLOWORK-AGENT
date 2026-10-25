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
        out_audio = payload.get("output_path", "/home/mrflow/flowork/.FL_BIN/scratch/voiceover.mp3")
        out_srt = out_audio.rsplit(".", 1)[0] + ".srt"
        os.makedirs(os.path.dirname(os.path.abspath(out_audio)), exist_ok=True)
        
        ok = asyncio.run(synthesize_voiceover(text, voice, out_audio, out_srt))
        print(json.dumps({
            "success": ok,
            "audio_path": out_audio,
            "subtitle_path": out_srt if os.path.exists(out_srt) else None
        }))

    elif action in ("render_video", "render_short"):
        res = "1080x1920" if action == "render_short" else "1920x1080"
        audio = payload.get("audio_path")
        out_mp4 = payload.get("output_path", "/home/mrflow/flowork/.FL_BIN/scratch/render_output.mp4")
        scenes = payload.get("scenes", [])
        os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
        
        result = render_slideshow_video(scenes, audio, out_mp4, resolution=res)
        print(json.dumps(result))

if __name__ == "__main__":
    main()
