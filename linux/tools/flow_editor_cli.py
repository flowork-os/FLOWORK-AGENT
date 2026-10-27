# [FL_INDEX: keywords="flow_editor_cli, video_automation, flow_studio_api, timeline_composer, ai_editor_tool" | purpose="CLI and programmatic Python interface for autonomous AI video editing on Flow Studio"]
import sys
import os
import json
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = os.environ.get('FLOW_STUDIO_URL', 'http://127.0.0.1:18012')

def make_request(path, method='GET', data=None):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method=method)
    if data is not None:
        req.add_header('Content-Type', 'application/json')
        body_bytes = json.dumps(data).encode('utf-8')
    else:
        body_bytes = None

    try:
        with urllib.request.urlopen(req, data=body_bytes, timeout=30) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        try:
            return json.loads(err_body)
        except Exception:
            return {"status": "error", "message": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def send_agent_command(action, payload):
    return make_request('/api/agent/command', method='POST', data={
        "action": action,
        "payload": payload
    })

def cmd_get_state():
    res = make_request('/api/project/state', method='GET')
    print(json.dumps(res, indent=2))

def cmd_add_clip(track_id, media_url, name, start, duration, in_point=0, out_point=None):
    if out_point is None:
        out_point = duration
    payload = {
        "trackId": track_id,
        "mediaUrl": media_url,
        "name": name,
        "start": float(start),
        "duration": float(duration),
        "inPoint": float(in_point),
        "outPoint": float(out_point)
    }
    res = send_agent_command('ADD_CLIP', payload)
    print(json.dumps(res, indent=2))

def cmd_split_clip(clip_id, at_second):
    payload = {
        "clipId": clip_id,
        "atSecond": float(at_second)
    }
    res = send_agent_command('SPLIT_CLIP', payload)
    print(json.dumps(res, indent=2))

def cmd_trim_clip(clip_id, new_duration, new_out_point=None):
    payload = {
        "clipId": clip_id,
        "newDuration": float(new_duration)
    }
    if new_out_point is not None:
        payload["newOutPoint"] = float(new_out_point)
    res = send_agent_command('TRIM_CLIP', payload)
    print(json.dumps(res, indent=2))

def cmd_set_properties(clip_id, props_json_str):
    try:
        props = json.loads(props_json_str)
    except Exception as e:
        print(f"Error parsing props JSON: {e}")
        return
    payload = {
        "clipId": clip_id,
        "properties": props
    }
    res = send_agent_command('SET_PROPERTIES', payload)
    print(json.dumps(res, indent=2))

def cmd_add_caption(text, start, duration, pos_y=38, font_size=28, color='#ffffff'):
    payload = {
        "text": text,
        "start": float(start),
        "duration": float(duration),
        "posY": float(pos_y),
        "fontSize": float(font_size),
        "color": color
    }
    res = send_agent_command('ADD_CAPTION', payload)
    print(json.dumps(res, indent=2))

def cmd_generate_tts(text, voice='id-ID-ArdiNeural', start=0):
    payload = {
        "text": text,
        "voice": voice,
        "start": float(start)
    }
    res = send_agent_command('GENERATE_TTS', payload)
    print(json.dumps(res, indent=2))

def cmd_auto_caption(media_path, language='id'):
    payload = {
        "mediaPath": media_path,
        "language": language
    }
    res = send_agent_command('AUTO_CAPTION', payload)
    print(json.dumps(res, indent=2))

def cmd_render(resolution='1080p', fps=30, format='mp4'):
    payload = {
        "resolution": resolution,
        "fps": int(fps),
        "format": format
    }
    res = send_agent_command('RENDER_PROJECT', payload)
    print(json.dumps(res, indent=2))

def cmd_clear():
    res = send_agent_command('CLEAR_TIMELINE', {})
    print(json.dumps(res, indent=2))

def print_help():
    print("""Flowork OS - Flow Studio Sovereign AI Video Editor CLI
Usage:
  python3 tools/flow_editor_cli.py <command> [args...]

Commands:
  state                                                 - Show current timeline state
  clear                                                 - Clear all tracks and clips
  add-clip <trackId> <mediaUrl> <name> <start> <dur>   - Insert video/audio clip
  split-clip <clipId> <atSecond>                        - Split clip at timestamp
  trim-clip <clipId> <newDuration> [newOutPoint]        - Trim clip duration
  set-props <clipId> '{"scale":120,"posX":10}'          - Update position, scale, opacity, etc.
  add-caption <text> <start> <duration> [posY] [size]   - Add styled subtitle/caption
  generate-tts <text> [voice] [start]                   - Create natural neural speech clip
  auto-caption <mediaPath> [language]                   - Transcribe audio to timeline captions
  render [1080p|720p] [fps] [mp4|webm]                  - Render project via FFmpeg
""")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('help', '--help', '-h'):
        print_help()
        return

    cmd = sys.argv[1].lower()
    if cmd == 'state':
        cmd_get_state()
    elif cmd == 'clear':
        cmd_clear()
    elif cmd == 'add-clip':
        if len(sys.argv) < 7:
            print("Usage: add-clip <trackId> <mediaUrl> <name> <start> <duration> [inPoint] [outPoint]")
            return
        in_p = sys.argv[7] if len(sys.argv) > 7 else 0
        out_p = sys.argv[8] if len(sys.argv) > 8 else None
        cmd_add_clip(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], in_p, out_p)
    elif cmd == 'split-clip':
        if len(sys.argv) < 4:
            print("Usage: split-clip <clipId> <atSecond>")
            return
        cmd_split_clip(sys.argv[2], sys.argv[3])
    elif cmd == 'trim-clip':
        if len(sys.argv) < 4:
            print("Usage: trim-clip <clipId> <newDuration> [newOutPoint]")
            return
        out_p = sys.argv[4] if len(sys.argv) > 4 else None
        cmd_trim_clip(sys.argv[2], sys.argv[3], out_p)
    elif cmd == 'set-props':
        if len(sys.argv) < 4:
            print("Usage: set-props <clipId> <propsJsonString>")
            return
        cmd_set_properties(sys.argv[2], sys.argv[3])
    elif cmd == 'add-caption':
        if len(sys.argv) < 5:
            print("Usage: add-caption <text> <start> <duration> [posY] [fontSize]")
            return
        py = sys.argv[5] if len(sys.argv) > 5 else 38
        fs = sys.argv[6] if len(sys.argv) > 6 else 28
        cmd_add_caption(sys.argv[2], sys.argv[3], sys.argv[4], py, fs)
    elif cmd == 'generate-tts':
        if len(sys.argv) < 3:
            print("Usage: generate-tts <text> [voice] [start]")
            return
        voice = sys.argv[3] if len(sys.argv) > 3 else 'id-ID-ArdiNeural'
        start = sys.argv[4] if len(sys.argv) > 4 else 0
        cmd_generate_tts(sys.argv[2], voice, start)
    elif cmd == 'auto-caption':
        if len(sys.argv) < 3:
            print("Usage: auto-caption <mediaPath> [language]")
            return
        lang = sys.argv[3] if len(sys.argv) > 3 else 'id'
        cmd_auto_caption(sys.argv[2], lang)
    elif cmd == 'render':
        res = sys.argv[2] if len(sys.argv) > 2 else '1080p'
        fps = sys.argv[3] if len(sys.argv) > 3 else 30
        fmt = sys.argv[4] if len(sys.argv) > 4 else 'mp4'
        cmd_render(res, fps, fmt)
    else:
        print(f"Unknown command: {cmd}")
        print_help()

if __name__ == '__main__':
    main()
