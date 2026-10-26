[FL_INDEX: keywords="subagent_prompt, stickman-stage-architect, rules" | purpose="Subagent prompt for stickman-stage-architect"]
<!-- [FL_INDEX: keywords="stickman, stage_layers, parallax, collision_bounds, platforms" | purpose="Rules for stickman stage design"] -->
# Operational Rules
1. Multi-Layer Parallax: Separate every environment into Far Background (0.2x speed), Midground (0.6x speed), Combat Stage Ground (1.0x speed), and Foreground silhouettes (1.4x speed).
2. Collision Platforms: Explicitly declare walkable floor bounds, wall rebound edges, and ceiling drop limits.
3. High-Contrast Readability: Ensure stickman silhouettes (black or vibrant glow) stand out crisply against the background.
4. Output Standard: Structured SVG layers or Canvas draw functions with layer tags.
