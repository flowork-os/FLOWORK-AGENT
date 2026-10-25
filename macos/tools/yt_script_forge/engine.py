"""
[FL_INDEX: keywords="youtube_script, hook_generator, shorts_script, retention_engineering, viral_copywriting" | COT="Sovereign AI script and retention engine for YouTube production" | AT="2026-10-26T04:00:00Z"]
"""
import sys
import json
import argparse

def generate_hook(topic, language="id", tone="suspenseful"):
    if language == "id":
        return [
            f"Fakta gila tentang {topic} yang sengaja disembunyikan dari kamu!",
            f"Jangan pernah lakukan ini kalau kamu mau menguasai {topic}!",
            f"99% orang salah paham soal {topic}. Ini rahasia aslinya..."
        ]
    return [
        f"The insane truth about {topic} nobody is telling you!",
        f"Never make this mistake if you care about {topic}!",
        f"99% of people get {topic} completely wrong. Here is why..."
    ]

def generate_short_script(topic, language="id"):
    hooks = generate_hook(topic, language)
    if language == "id":
        script = (
            f"[HOOK - 0-3s]\n{hooks[0]}\n\n"
            f"[PATTERN INTERRUPT - 3-10s]\nKebanyakan orang mikir {topic} itu gampang atau cuma tren sesaat.\n"
            f"Tapi faktanya jauh lebih mengejutkan dari yang kamu bayangkan.\n\n"
            f"[CORE VALUE - 10-40s]\nLangkah 1: Pahami prinsip dasarnya tanpa jalan pintas.\n"
            f"Langkah 2: Eksekusi konsisten 15 menit setiap hari.\n"
            f"Langkah 3: Hindari jebakan terbesar yang bikin 90% orang gagal.\n\n"
            f"[CALL TO ACTION - 40-55s]\nKetik 'MAU' di kolom komentar kalau kamu pengen tutorial lengkapnya. Follow untuk insight harian!"
        )
    else:
        script = (
            f"[HOOK - 0-3s]\n{hooks[0]}\n\n"
            f"[PATTERN INTERRUPT - 3-10s]\nMost people think {topic} is just a temporary hype.\n"
            f"But the reality is far more shocking than you realize.\n\n"
            f"[CORE VALUE - 10-40s]\nStep 1: Master the foundation without shortcuts.\n"
            f"Step 2: Execute consistently for 15 minutes daily.\n"
            f"Step 3: Dodge the fatal trap where 90% give up.\n\n"
            f"[CALL TO ACTION - 40-55s]\nDrop a comment below with your biggest question, and subscribe for more deep-dives!"
        )
    return {"topic": topic, "format": "short_9x16", "script": script, "estimated_duration_sec": 48}

def main():
    parser = argparse.ArgumentParser(description="YouTube Script & Hook Engine")
    parser.add_argument("--action", choices=["generate_hook", "generate_short_script"], default="generate_short_script")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--language", default="id")
    parser.add_argument("--tone", default="suspenseful")
    args = parser.parse_args()

    if args.action == "generate_hook":
        res = {"status": "success", "hooks": generate_hook(args.topic, args.language, args.tone)}
    else:
        res = {"status": "success", "data": generate_short_script(args.topic, args.language)}

    print(json.dumps(res, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
