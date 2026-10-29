#!/usr/bin/env python3
# [FL_INDEX: keywords="mocap_stickman_engine, motion_detector, video_to_stickman, mediapipe_mocap, adaptive_framing, temporal_smoothing, digital_puppetry" | purpose="Sovereign high-fidelity Video Motion Capture (MoCap) Stickman Puppeteer Engine transforming video actors into smooth 2D animated stickmen matching body movement, head orientation, and facial gestures on user custom backgrounds"]
"""
Stickman Studio Video-to-Stickman Motion Capture Engine (MoCap Puppeteer)
Extracts real human motion, posture, head tilt, and gestures frame-by-frame
and maps them smoothly to a stylized 2D stickman over a custom user background.
Co-authored-by: Flowork OS <agent@floworkos.com>
"""

import sys
import os
import math
import time
import subprocess
import tempfile
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pose_tracker import PoseTracker


def smooth_interpolate(curr, prev, alpha=0.65):
    """Exponential Moving Average (EMA) smoothing for temporal landmark stability."""
    if prev is None:
        return curr
    return {k: alpha * curr[k] + (1.0 - alpha) * prev[k] for k in curr}


class MocapStickmanEngine:
    def __init__(self, width=720, height=1280, smoothing_alpha=0.65):
        self.width = width
        self.height = height
        self.alpha = smoothing_alpha
        self.prev_joints = None
        self.tracker = PoseTracker()
        self.ground_y = int(self.height * 0.82)
        self.cx = self.width // 2

        self.font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if not os.path.exists(self.font_bold_path):
            self.font_bold_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

    def _get_font(self, size):
        try:
            return ImageFont.truetype(self.font_bold_path, int(size))
        except Exception:
            return ImageFont.load_default()

    def reset(self):
        """Reset temporal smoothing state between clips."""
        self.prev_joints = None

    def load_background(self, bg_image_path=None):
        """Loads and cover-crops custom background image or generates a clean studio gradient."""
        if bg_image_path and os.path.exists(bg_image_path):
            try:
                bg_raw = Image.open(bg_image_path).convert("RGBA")
                bg_w, bg_h = bg_raw.size
                target_ratio = self.width / float(self.height)
                curr_ratio = bg_w / float(bg_h)
                if curr_ratio > target_ratio:
                    new_w = int(bg_h * target_ratio)
                    start_x = (bg_w - new_w) // 2
                    cropped = bg_raw.crop((start_x, 0, start_x + new_w, bg_h))
                else:
                    new_h = int(bg_w / target_ratio)
                    start_y = (bg_h - new_h) // 2
                    cropped = bg_raw.crop((0, start_y, bg_w, start_y + new_h))
                resized = cropped.resize((self.width, self.height), Image.Resampling.LANCZOS)
                return resized
            except Exception as e:
                print(f"[MoCapEngine] Warning loading background {bg_image_path}: {e}", file=sys.stderr)

        # Fallback: Clean warm studio gradient
        bg = Image.new("RGBA", (self.width, self.height), (248, 246, 240, 255))
        draw = ImageDraw.Draw(bg)
        top_c = (248, 246, 240)
        bot_c = (235, 233, 225)
        for y in range(self.ground_y):
            ratio = y / float(self.ground_y)
            r = int(top_c[0] + (bot_c[0] - top_c[0]) * ratio)
            g = int(top_c[1] + (bot_c[1] - top_c[1]) * ratio)
            b = int(top_c[2] + (bot_c[2] - top_c[2]) * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        draw.rectangle([0, self.ground_y, self.width, self.height], fill=(220, 218, 210))
        draw.line([(0, self.ground_y), (self.width, self.ground_y)], fill=(180, 178, 170), width=4)
        return bg

    def quadratic_bezier(self, p0, p1, p2, num_points=18):
        points = []
        for i in range(num_points + 1):
            u = i / float(num_points)
            x = (1 - u)**2 * p0[0] + 2 * (1 - u) * u * p1[0] + u**2 * p2[0]
            y = (1 - u)**2 * p0[1] + 2 * (1 - u) * u * p1[1] + u**2 * p2[1]
            points.append((int(x), int(y)))
        return points

    def draw_limb(self, draw, p0, p1, p2, width=12, color=(25, 27, 34), outline=(255, 255, 255)):
        pts = self.quadratic_bezier(p0, p1, p2, num_points=18)
        if len(pts) >= 2:
            if outline:
                draw.line(pts, fill=outline, width=width + 4, joint="curve")
            draw.line(pts, fill=color, width=width, joint="curve")
        r = width // 2
        for pt in [p0, p2]:
            if outline:
                draw.ellipse([pt[0] - r - 2, pt[1] - r - 2, pt[0] + r + 2, pt[1] + r + 2], fill=outline)
            draw.ellipse([pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r], fill=color)

    def render_mocap_frame(self, bg_img, raw_joints, t=0.0, energy=0.5, character_style='classic', framing_mode='auto'):
        """
        Renders a single motion capture frame.
        Takes normalized landmarks (0.0 - 1.0) and translates them onto target canvas.
        """
        pil_frame = bg_img.copy()
        draw = ImageDraw.Draw(pil_frame)

        if not raw_joints:
            return cv2.cvtColor(np.array(pil_frame.convert("RGB")), cv2.COLOR_RGB2BGR)

        # 1. Temporal Smoothing (EMA Filter)
        smoothed = {}
        for k, v in raw_joints.items():
            if self.prev_joints and k in self.prev_joints:
                smoothed[k] = {
                    "x": self.alpha * v["x"] + (1.0 - self.alpha) * self.prev_joints[k]["x"],
                    "y": self.alpha * v["y"] + (1.0 - self.alpha) * self.prev_joints[k]["y"],
                    "z": self.alpha * v["z"] + (1.0 - self.alpha) * self.prev_joints[k]["z"],
                    "visibility": v.get("visibility", 1.0)
                }
            else:
                smoothed[k] = v
        self.prev_joints = smoothed
        j = smoothed

        # 2. Determine Framing: Full-Body vs Upper-Body / Bust
        has_legs = (
            j.get("l_ankle", {}).get("visibility", 0) > 0.35 and
            j.get("r_ankle", {}).get("visibility", 0) > 0.35 and
            j.get("l_knee", {}).get("visibility", 0) > 0.35 and
            j.get("l_ankle", {}).get("y", 2.0) <= 1.05 and
            j.get("r_ankle", {}).get("y", 2.0) <= 1.05
        )

        has_hips = (
            j.get("l_hip", {}).get("visibility", 0) > 0.25 and
            j.get("r_hip", {}).get("visibility", 0) > 0.25 and
            j.get("l_hip", {}).get("y", 2.0) <= 1.05
        )

        # 3. Canvas Coordinate Mapping
        sh_l = j.get("l_shoulder", {"x": 0.40, "y": 0.50, "visibility": 0.9})
        sh_r = j.get("r_shoulder", {"x": 0.60, "y": 0.50, "visibility": 0.9})
        nose = j.get("nose", {"x": 0.50, "y": 0.35, "visibility": 0.9})

        sh_dist = math.hypot(sh_l["x"] - sh_r["x"], sh_l["y"] - sh_r["y"]) or 0.25
        # Ideal shoulder width on our 720px width canvas: approx 150-170px
        scale_factor = (160.0 / (sh_dist * self.width)) * (self.width / 720.0)
        scale_factor = max(0.65, min(2.2, scale_factor))

        actor_cx = (sh_l["x"] + sh_r["x"]) / 2.0
        actor_cy = (sh_l["y"] + sh_r["y"]) / 2.0

        # Anchor origin in target canvas coordinates
        if has_legs:
            # Full Body: anchor comfortably centered
            target_cx = self.cx
            target_cy = int(self.height * 0.48)
        else:
            # Upper-Body / Bust: anchor comfortably at mid-height
            target_cx = self.cx
            target_cy = int(self.height * 0.52) if framing_mode != 'presenter' else int(self.height * 0.48)

        def map_pt(pt_dict, default_offset=(0, 0), max_y_clamp=None):
            if not pt_dict or pt_dict.get("visibility", 0) < 0.25 or pt_dict.get("y", 0) > 1.08:
                return (int(target_cx + default_offset[0]), int(target_cy + default_offset[1]))
            dx = (pt_dict["x"] - actor_cx) * self.width * scale_factor
            dy = (pt_dict["y"] - actor_cy) * self.height * scale_factor
            pt_x = int(target_cx + dx)
            pt_y = int(target_cy + dy)
            if max_y_clamp is not None:
                pt_y = min(pt_y, max_y_clamp)
            return (pt_x, pt_y)

        # Calculate Head & Shoulder Positions
        p_sh_l = map_pt(sh_l, (-75, 0))
        p_sh_r = map_pt(sh_r, (75, 0))
        mid_shoulder = ((p_sh_l[0] + p_sh_r[0]) // 2, (p_sh_l[1] + p_sh_r[1]) // 2)

        head_r = max(42, int(sh_dist * self.width * scale_factor * 0.38))
        head_r = min(68, head_r)

        # Map Nose / Head
        nose_dy = (nose.get("y", 0.35) - actor_cy) * self.height * scale_factor
        head_cy = mid_shoulder[1] - head_r - int(24 * (self.height / 1280.0))
        head_cx = int(target_cx + (nose.get("x", 0.5) - actor_cx) * self.width * scale_factor * 0.7)

        # Fixed Anatomical Bone Lengths (Guarantees zero stretching or distortion)
        L_up = int(head_r * 1.18)
        L_fore = int(head_r * 1.12)

        # Left Arm Angular FK
        el_l_raw = j.get("l_elbow")
        if el_l_raw and el_l_raw.get("visibility", 0) >= 0.28 and el_l_raw.get("y", 0) <= 1.05:
            ang_up_l = math.atan2(el_l_raw["y"] - sh_l["y"], el_l_raw["x"] - sh_l["x"])
        else:
            ang_up_l = math.radians(105)

        p_el_l = (
            int(p_sh_l[0] + L_up * math.cos(ang_up_l)),
            int(p_sh_l[1] + L_up * math.sin(ang_up_l))
        )

        wr_l_raw = j.get("l_wrist")
        if wr_l_raw and wr_l_raw.get("visibility", 0) >= 0.28 and wr_l_raw.get("y", 0) <= 1.05 and el_l_raw:
            ang_fore_l = math.atan2(wr_l_raw["y"] - el_l_raw["y"], wr_l_raw["x"] - el_l_raw["x"])
        else:
            ang_fore_l = math.radians(88)

        p_wr_l = (
            int(p_el_l[0] + L_fore * math.cos(ang_fore_l)),
            int(p_el_l[1] + L_fore * math.sin(ang_fore_l))
        )

        # Right Arm Angular FK
        el_r_raw = j.get("r_elbow")
        if el_r_raw and el_r_raw.get("visibility", 0) >= 0.28 and el_r_raw.get("y", 0) <= 1.05:
            ang_up_r = math.atan2(el_r_raw["y"] - sh_r["y"], el_r_raw["x"] - sh_r["x"])
        else:
            ang_up_r = math.radians(75)

        p_el_r = (
            int(p_sh_r[0] + L_up * math.cos(ang_up_r)),
            int(p_sh_r[1] + L_up * math.sin(ang_up_r))
        )

        wr_r_raw = j.get("r_wrist")
        if wr_r_raw and wr_r_raw.get("visibility", 0) >= 0.28 and wr_r_raw.get("y", 0) <= 1.05 and el_r_raw:
            ang_fore_r = math.atan2(wr_r_raw["y"] - el_r_raw["y"], wr_r_raw["x"] - el_r_raw["x"])
        else:
            ang_fore_r = math.radians(92)

        p_wr_r = (
            int(p_el_r[0] + L_fore * math.cos(ang_fore_r)),
            int(p_el_r[1] + L_fore * math.sin(ang_fore_r))
        )

        # Torso & Lower Body Anatomy
        torso_len = int(head_r * 2.2)
        mid_hip = (mid_shoulder[0], mid_shoulder[1] + torso_len)
        hip_span = int(head_r * 0.65)
        p_hip_l = (mid_hip[0] - hip_span // 2, mid_hip[1])
        p_hip_r = (mid_hip[0] + hip_span // 2, mid_hip[1])

        if has_legs and has_hips:
            L_thigh = int(head_r * 1.55)
            L_calf = int(head_r * 1.55)

            ang_thigh_l = math.atan2(j["l_knee"]["y"] - j["l_hip"]["y"], j["l_knee"]["x"] - j["l_hip"]["x"])
            p_kn_l = (int(p_hip_l[0] + L_thigh * math.cos(ang_thigh_l)), int(p_hip_l[1] + L_thigh * math.sin(ang_thigh_l)))
            ang_calf_l = math.atan2(j["l_ankle"]["y"] - j["l_knee"]["y"], j["l_ankle"]["x"] - j["l_knee"]["x"])
            p_ank_l = (int(p_kn_l[0] + L_calf * math.cos(ang_calf_l)), int(p_kn_l[1] + L_calf * math.sin(ang_calf_l)))

            ang_thigh_r = math.atan2(j["r_knee"]["y"] - j["r_hip"]["y"], j["r_knee"]["x"] - j["r_hip"]["x"])
            p_kn_r = (int(p_hip_r[0] + L_thigh * math.cos(ang_thigh_r)), int(p_hip_r[1] + L_thigh * math.sin(ang_thigh_r)))
            ang_calf_r = math.atan2(j["r_ankle"]["y"] - j["r_knee"]["y"], j["r_ankle"]["x"] - j["r_knee"]["x"])
            p_ank_r = (int(p_kn_r[0] + L_calf * math.cos(ang_calf_r)), int(p_kn_r[1] + L_calf * math.sin(ang_calf_r)))
        else:
            # Proportional natural standing posture anchored to floor
            leg_total = self.ground_y - mid_hip[1]
            knee_drop = int(leg_total * 0.48)
            stance_w = int(head_r * 0.65)
            p_kn_l = (p_hip_l[0] - 12, mid_hip[1] + knee_drop)
            p_kn_r = (p_hip_r[0] + 12, mid_hip[1] + knee_drop)
            p_ank_l = (mid_hip[0] - stance_w, self.ground_y)
            p_ank_r = (mid_hip[0] + stance_w, self.ground_y)

        # 4. Drawing Layers
        ink = (25, 27, 34)
        white = (255, 255, 255)
        accent = (0, 229, 255)
        limb_w = max(9, int(13 * (self.height / 1280.0)))

        is_presenter = (framing_mode == 'presenter')

        if not is_presenter:
            # Ground Shadow
            shadow_w = int(140 * (self.height / 1280.0))
            draw.ellipse([mid_hip[0] - shadow_w, self.ground_y - 8,
                          mid_hip[0] + shadow_w, self.ground_y + 16], fill=(0, 0, 0, 55))

            # Legs (Bezier limbs)
            self.draw_limb(draw, p_hip_l, p_kn_l, p_ank_l, width=limb_w, color=ink, outline=white)
            self.draw_limb(draw, p_hip_r, p_kn_r, p_ank_r, width=limb_w, color=ink, outline=white)
            # Feet shoes
            draw.line([p_ank_l, (p_ank_l[0] - 24, p_ank_l[1])], fill=ink, width=limb_w)
            draw.line([p_ank_r, (p_ank_r[0] + 24, p_ank_r[1])], fill=ink, width=limb_w)

        # Torso Spine (Connecting Mid-Hip to Mid-Shoulder)
        draw.line([mid_hip, mid_shoulder], fill=white, width=limb_w + 4)
        draw.line([mid_hip, mid_shoulder], fill=ink, width=limb_w)

        # Collarbone (Connecting Left Shoulder -> Mid Shoulder -> Right Shoulder)
        draw.line([p_sh_l, p_sh_r], fill=white, width=limb_w + 4)
        draw.line([p_sh_l, p_sh_r], fill=ink, width=limb_w)

        # Neck (Connecting Mid-Shoulder to Head Base)
        head_bottom_y = head_cy + head_r
        draw.line([mid_shoulder, (mid_shoulder[0], head_bottom_y)], fill=white, width=limb_w + 2)
        draw.line([mid_shoulder, (mid_shoulder[0], head_bottom_y)], fill=ink, width=limb_w)

        # Arms (Following actor's tracked shoulders, elbows, wrists)
        self.draw_limb(draw, p_sh_l, p_el_l, p_wr_l, width=limb_w - 1, color=ink, outline=white)
        self.draw_limb(draw, p_sh_r, p_el_r, p_wr_r, width=limb_w - 1, color=ink, outline=white)

        # Hands / Palms at Wrists
        hand_r = limb_w // 2 + 3
        for hw in [p_wr_l, p_wr_r]:
            draw.ellipse([hw[0] - hand_r - 2, hw[1] - hand_r - 2, hw[0] + hand_r + 2, hw[1] + hand_r + 2], fill=white)
            draw.ellipse([hw[0] - hand_r, hw[1] - hand_r, hw[0] + hand_r, hw[1] + hand_r], fill=ink)

        # Presenter Desk (if presenter mode)
        if is_presenter:
            desk_y = mid_hip[1] - int(head_r * 0.4)
            desk_h = self.height - desk_y
            # Modern acrylic frosted desk
            draw.rounded_rectangle([self.cx - 260, desk_y, self.cx + 260, self.height + 40], radius=24, fill=(30, 41, 59, 235), outline=(0, 229, 255), width=3)
            # Desk surface line glow
            draw.line([(self.cx - 240, desk_y + 4), (self.cx + 240, desk_y + 4)], fill=(148, 163, 184), width=4)
            # Microphone
            mic_x = self.cx + 120
            draw.line([(mic_x, desk_y + 10), (mic_x, desk_y - 45)], fill=(100, 116, 139), width=5)
            draw.rounded_rectangle([mic_x - 8, desk_y - 65, mic_x + 8, desk_y - 42], radius=6, fill=(15, 23, 42), outline=(0, 229, 255), width=2)

        # Scarf / Collar (Flowork trademark personality)
        draw.line([(mid_shoulder[0] - 26, mid_shoulder[1]),
                   (mid_shoulder[0] + 26, mid_shoulder[1])], fill=accent, width=int(12 * (self.height / 1280.0)))

        # Head Radius & Circle
        draw.ellipse([head_cx - head_r - 2, head_cy - head_r - 2,
                      head_cx + head_r + 2, head_cy + head_r + 2], fill=white)
        draw.ellipse([head_cx - head_r, head_cy - head_r,
                      head_cx + head_r, head_cy + head_r], fill=white, outline=ink, width=max(4, int(7 * (self.height / 1280.0))))

        # Head Tilt Calculation from Eyes
        eye_l = j.get("l_eye", {})
        eye_r = j.get("r_eye", {})
        if eye_l.get("visibility", 0) > 0.4 and eye_r.get("visibility", 0) > 0.4:
            tilt_angle = math.atan2(eye_r["y"] - eye_l["y"], eye_r["x"] - eye_l["x"])
        else:
            tilt_angle = 0.0

        # Eyes (Look direction & blink)
        eye_offset_x = int(head_r * 0.36)
        eye_offset_y = int(head_r * 0.10)
        eye_r_sz = max(3, int(head_r * 0.12))

        # Rotate eyes with head tilt
        for side in (-1, 1):
            ex_local = side * eye_offset_x
            ey_local = -eye_offset_y
            ex_rot = ex_local * math.cos(tilt_angle) - ey_local * math.sin(tilt_angle)
            ey_rot = ex_local * math.sin(tilt_angle) + ey_local * math.cos(tilt_angle)
            ex = int(head_cx + ex_rot)
            ey = int(head_cy + ey_rot)
            draw.ellipse([ex - eye_r_sz, ey - eye_r_sz, ex + eye_r_sz, ey + eye_r_sz], fill=ink)

            # Eyebrow
            bw = int(head_r * 0.28)
            draw.line([(ex - bw//2, ey - int(head_r * 0.22)), (ex + bw//2, ey - int(head_r * 0.22))], fill=ink, width=3)

        # Mouth (Driven by audio energy and mouth landmark aperture)
        mouth_l = j.get("mouth_l", {})
        mouth_r = j.get("mouth_r", {})
        mouth_w = max(int(head_r * 0.25), int(math.hypot(mouth_l.get("x", 0) - mouth_r.get("x", 0), mouth_l.get("y", 0) - mouth_r.get("y", 0)) * self.width * scale_factor))
        mouth_w = min(int(head_r * 0.65), max(int(head_r * 0.25), mouth_w))

        mouth_cy = head_cy + int(head_r * 0.44)
        if energy > 0.1:
            mh = int(head_r * 0.12 + head_r * 0.35 * energy)
            draw.ellipse([head_cx - mouth_w//2, mouth_cy - mh//2, head_cx + mouth_w//2, mouth_cy + mh//2], fill=ink)
            if mh > 10:
                draw.arc([head_cx - mouth_w//2 + 4, mouth_cy, head_cx + mouth_w//2 - 4, mouth_cy + mh//2], start=0, end=180, fill=(244, 114, 182), width=3)
        else:
            draw.line([(head_cx - mouth_w//2, mouth_cy), (head_cx + mouth_w//2, mouth_cy)], fill=ink, width=3)

        # 5. Character Archetype Accessories
        if character_style == 'girl':
            # Twin cute anime hair ribbons / ponytail
            draw.arc([head_cx - head_r - 8, head_cy - head_r + 4, head_cx - head_r + 20, head_cy - head_r + 32], start=45, end=270, fill=(244, 114, 182), width=6)
            draw.arc([head_cx + head_r - 20, head_cy - head_r + 4, head_cx + head_r + 8, head_cy - head_r + 32], start=270, end=135, fill=(244, 114, 182), width=6)
            # Ribbon bow on top
            draw.ellipse([head_cx - 16, head_cy - head_r - 12, head_cx - 2, head_cy - head_r + 2], fill=(236, 72, 153))
            draw.ellipse([head_cx + 2, head_cy - head_r - 12, head_cx + 16, head_cy - head_r + 2], fill=(236, 72, 153))
            draw.ellipse([head_cx - 5, head_cy - head_r - 10, head_cx + 5, head_cy - head_r], fill=(244, 114, 182))
            # Cute anime cheek blush
            draw.ellipse([head_cx - int(head_r * 0.55), head_cy + int(head_r * 0.12), head_cx - int(head_r * 0.32), head_cy + int(head_r * 0.28)], fill=(251, 113, 133, 160))
            draw.ellipse([head_cx + int(head_r * 0.32), head_cy + int(head_r * 0.12), head_cx + int(head_r * 0.55), head_cy + int(head_r * 0.28)], fill=(251, 113, 133, 160))
        elif character_style == 'glasses' or character_style == 'smart':
            # Stylish glasses matching presenter
            sg_y = head_cy - eye_offset_y
            gw = int(head_r * 0.30)
            gh = int(head_r * 0.22)
            # Left lens frame
            draw.rectangle([head_cx - eye_offset_x - gw//2, sg_y - gh//2, head_cx - eye_offset_x + gw//2, sg_y + gh//2], outline=(15, 23, 42), width=3)
            # Right lens frame
            draw.rectangle([head_cx + eye_offset_x - gw//2, sg_y - gh//2, head_cx + eye_offset_x + gw//2, sg_y + gh//2], outline=(15, 23, 42), width=3)
            # Bridge
            draw.line([(head_cx - eye_offset_x + gw//2, sg_y), (head_cx + eye_offset_x - gw//2, sg_y)], fill=(15, 23, 42), width=3)
        elif character_style == 'cool':
            # Cool sunglasses over eyes
            sg_y = head_cy - eye_offset_y
            draw.rectangle([head_cx - eye_offset_x - 14, sg_y - 8, head_cx - eye_offset_x + 14, sg_y + 8], fill=(15, 23, 42))
            draw.rectangle([head_cx + eye_offset_x - 14, sg_y - 8, head_cx + eye_offset_x + 14, sg_y + 8], fill=(15, 23, 42))
            draw.line([(head_cx - eye_offset_x + 14, sg_y), (head_cx + eye_offset_x - 14, sg_y)], fill=(15, 23, 42), width=3)
        elif character_style == 'business':
            # Professional necktie down the torso
            tie_top_y = mid_shoulder[1] + 8
            tie_bot_y = mid_hip[1] - int(torso_len * 0.2)
            draw.polygon([
                (mid_shoulder[0] - 6, tie_top_y),
                (mid_shoulder[0] + 6, tie_top_y),
                (mid_shoulder[0] + 12, tie_bot_y - 12),
                (mid_shoulder[0], tie_bot_y),
                (mid_shoulder[0] - 12, tie_bot_y - 12)
            ], fill=(225, 29, 72))

        rgb_img = pil_frame.convert("RGB")
        return cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2BGR)


def extract_audio_envelope(audio_src, total_frames, fps=24):
    """Calculates RMS audio energy envelope for realistic speech dynamics."""
    default_env = [0.5 for _ in range(max(1, total_frames))]
    if not audio_src or not os.path.exists(audio_src):
        return default_env
    temp_wav = os.path.join(tempfile.gettempdir(), f"_mocap_env_{os.getpid()}_{int(time.time() * 1000)}.wav")
    try:
        cmd = ['ffmpeg', '-y', '-i', audio_src, '-vn', '-ac', '1', '-ar', '16000', '-f', 'wav', temp_wav]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(temp_wav):
            import soundfile as sf
            data, sr = sf.read(temp_wav)
            os.remove(temp_wav)
            if len(data) == 0:
                return default_env
            spf = int(sr / fps)
            max_amp = float(np.percentile(np.abs(data), 95)) or 0.1
            env = []
            for f in range(total_frames):
                chunk = data[f * spf:(f + 1) * spf]
                if len(chunk) > 0:
                    rms = float(np.sqrt(np.mean(chunk**2)))
                    norm = min(1.0, (rms / max_amp) * 1.5)
                    env.append(max(0.08, norm))
                else:
                    env.append(0.08)
            return env
    except Exception:
        if os.path.exists(temp_wav):
            try: os.remove(temp_wav)
            except Exception: pass
    return default_env


def ensure_compatible_h264(video_path):
    """Verifies cv2.VideoCapture can read the video stream. If codec is incompatible (e.g. AV1, VP9), transcodes to fast h264."""
    try:
        test_cap = cv2.VideoCapture(video_path)
        ret, frame = test_cap.read()
        test_cap.release()
        if ret and frame is not None and frame.shape[0] > 0:
            return video_path, None
    except Exception:
        pass

    temp_h264 = os.path.join(tempfile.gettempdir(), f"_mocap_trans_{os.getpid()}_{int(time.time() * 1000)}.mp4")
    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18',
        '-c:a', 'copy', temp_h264
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return temp_h264, temp_h264


def run_mocap_pipeline(video_path, background_image_path, output_mp4, character_style='classic', framing_mode='auto', target_fps=30):
    """
    Complete Video-to-Stickman Motion Capture Production Pipeline.
    1. Tracks actor landmarks frame-by-frame via MediaPipe.
    2. Renders dynamic stickman following human motion over custom background.
    3. Multiplexes original source audio into final high-res MP4.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Input video not found: {video_path}")

    # Ensure input video is readable by OpenCV VideoCapture
    work_video, temp_to_clean = ensure_compatible_h264(video_path)

    cap = cv2.VideoCapture(work_video)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or target_fps
    width = 720
    height = 1280

    engine = MocapStickmanEngine(width=width, height=height)
    bg_img = engine.load_background(background_image_path)

    # Audio Envelope
    audio_env = extract_audio_envelope(video_path, total_frames, fps=src_fps)

    temp_raw = output_mp4 + ".raw.mp4"
    os.makedirs(os.path.dirname(os.path.abspath(output_mp4)), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_raw, fourcc, src_fps, (width, height))

    print(f"[MoCap Pipeline] 🎬 Tracking and rendering {total_frames} frames ({character_style}, framing={framing_mode})...")
    f_idx = 0
    t0 = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        t = f_idx / src_fps
        energy = audio_env[f_idx] if f_idx < len(audio_env) else 0.5

        # MediaPipe Pose tracking
        analysis = engine.tracker.analyze_image(frame)
        joints = analysis.get("joints") if analysis.get("has_pose") else None

        # Render MoCap Stickman Frame
        rendered_bgr = engine.render_mocap_frame(
            bg_img, joints, t=t, energy=energy,
            character_style=character_style, framing_mode=framing_mode
        )
        out.write(rendered_bgr)
        f_idx += 1

        if f_idx % 60 == 0:
            pct = int((f_idx / total_frames) * 100) if total_frames > 0 else 0
            print(f"   [MoCap] {f_idx}/{total_frames} frames ({pct}%) rendered...")

    cap.release()
    out.release()
    if temp_to_clean and os.path.exists(temp_to_clean):
        try: os.remove(temp_to_clean)
        except Exception: pass

    elapsed = time.time() - t0
    fps_stat = f_idx / elapsed if elapsed > 0 else 0
    print(f"[MoCap Pipeline] ✓ Rendered {f_idx} frames in {elapsed:.2f}s ({fps_stat:.1f} FPS)")

    # Multiplex Original Audio into Output MP4
    print("[MoCap Pipeline] 🔊 Multiplexing original audio stream into final MP4...")
    cmd = [
        'ffmpeg', '-y',
        '-i', temp_raw,
        '-i', video_path,
        '-map', '0:v:0',
        '-map', '1:a:0?',
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        output_mp4
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if os.path.exists(temp_raw):
        os.remove(temp_raw)

    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg muxing failed: {res.stderr.decode()}")

    print(f"[MoCap Pipeline] 🎉 SUCCESS: {output_mp4} ({os.path.getsize(output_mp4)} bytes)")
    return output_mp4


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: mocap_stickman_engine.py <video_in> <bg_image> <output_mp4> [character_style] [framing_mode]", file=sys.stderr)
        sys.exit(1)
    _video_in = sys.argv[1]
    _bg_in = sys.argv[2] if sys.argv[2] != 'none' else None
    _video_out = sys.argv[3]
    _char_style = sys.argv[4] if len(sys.argv) > 4 else 'classic'
    _framing = sys.argv[5] if len(sys.argv) > 5 else 'auto'
    run_mocap_pipeline(_video_in, _bg_in, _video_out, character_style=_char_style, framing_mode=_framing)

