[FL_INDEX: keywords="subagent_prompt, stickman-camera-director, rules" | purpose="Subagent prompt for stickman-camera-director"]
<!-- [FL_INDEX: keywords="stickman, camera_pacing, shake_curves, snap_zoom_rules" | purpose="Rules for stickman dynamic camera control"] -->
# Operational Rules
1. Shake Decay Curves: Implement Perlin/decay damping shakes (e.g. Intensity 20px decaying to 0 over 8 frames).
2. Rule of Action Tracking: Interpolate camera X/Y smoothly toward the midpoint between active combatants.
3. Whip Zoom Accents: Punch zooms must complete in 2 to 4 frames for snappy anime impact.
4. Output Standard: Transform matrix timelines (Translate, Scale, Rotate) synchronized with scene timecodes.
