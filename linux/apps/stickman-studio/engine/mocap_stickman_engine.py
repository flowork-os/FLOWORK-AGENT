#!/usr/bin/env python3
# [FL_INDEX: keywords="mocap_stickman_engine, multi_entity_mocap, demographic_puppeteer, yolo_pose, animal_mocap, forward_kinematics, stickman_studio" | purpose="Sovereign Multi-Entity Video Motion Capture (MoCap) Stickman Puppeteer Engine transforming video actors (men, women, children, animals) into smooth 2D animated stick figures matching movement, gestures, and audio on custom backgrounds"]
"""
Stickman Studio Multi-Entity Video-to-Stickman Motion Capture Engine (MoCap Puppeteer)
Extracts multi-human poses and animal tracks frame-by-frame using YOLO-Pose & YOLO-Detection,
classifies demographics (male, female, child) and animal species (dog, cat, bird),
and maps them smoothly to stylized 2D stickmen over a custom user background.
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
from multi_entity_tracker import MultiEntityTracker


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
        self.entity_tracker = MultiEntityTracker(width=self.width, height=self.height, smoothing_alpha=smoothing_alpha)
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
        self.entity_tracker.reset()

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
        for y in range(self.height):
            ratio = y / float(self.height)
            r = int(top_c[0] + (bot_c[0] - top_c[0]) * ratio)
            g = int(top_c[1] + (bot_c[1] - top_c[1]) * ratio)
            b = int(top_c[2] + (bot_c[2] - top_c[2]) * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b, 255))
        # Subtle floor baseboard
        draw.line([(0, self.ground_y), (self.width, self.ground_y)], fill=(210, 206, 195), width=3)
        return bg

    def draw_limb(self, draw, p_start, p_mid, p_end, width=10, color=(25, 27, 34), outline=(255, 255, 255)):
        """Draws organic stylized stick limbs with white outline for depth separation."""
        if outline:
            draw.line([p_start, p_mid], fill=outline, width=width + 4)
            draw.line([p_mid, p_end], fill=outline, width=width + 4)
            draw.ellipse([p_mid[0] - width//2 - 2, p_mid[1] - width//2 - 2,
                          p_mid[0] + width//2 + 2, p_mid[1] + width//2 + 2], fill=outline)

        draw.line([p_start, p_mid], fill=color, width=width)
        draw.line([p_mid, p_end], fill=color, width=width)
        draw.ellipse([p_mid[0] - width//2, p_mid[1] - width//2,
                      p_mid[0] + width//2, p_mid[1] + width//2], fill=color)

    def draw_shadow(self, draw, cx, ground_y, rx=50, ry=12):
        """Draws grounded contact drop shadow on floor."""
        draw.ellipse([cx - rx, ground_y - ry, cx + rx, ground_y + ry], fill=(15, 23, 42, 60))

    def render_stick_human(self, draw, kps, ground_y=None, archetype='male', scale=1.0, energy=0.5, t=0.0):
        """
        Renders a full-body stickman using Forward Kinematics (FK) pinned bone lengths.
        kps: numpy array of shape (17, 2) in canvas coordinates
        """
        # COCO 17 Keypoints:
        # 0: nose, 1: left_eye, 2: right_eye, 3: left_ear, 4: right_ear
        # 5: left_sh, 6: right_sh, 7: left_el, 8: right_el, 9: left_wr, 10: right_wr
        # 11: left_hip, 12: right_hip, 13: left_kn, 14: right_kn, 15: left_ank, 16: right_ank

        sh_l, sh_r = kps[5], kps[6]
        hip_l, hip_r = kps[11], kps[12]
        nose = kps[0]
        eye_l, eye_r = kps[1], kps[2]

        mid_sh = ((sh_l[0] + sh_r[0]) / 2.0, (sh_l[1] + sh_r[1]) / 2.0)
        sh_w = math.hypot(sh_l[0] - sh_r[0], sh_l[1] - sh_r[1])
        head_r = max(18, int(max(sh_w * 0.45, 26 * scale)))
        if archetype == 'child':
            head_r = int(head_r * 1.25) # Cute larger head ratio for kids

        head_cx = int(nose[0])
        head_cy = int(nose[1])
        if head_cy >= mid_sh[1] - head_r:
            head_cy = int(mid_sh[1] - head_r - 12)

        # Grounding
        target_ground = ground_y or self.ground_y

        # Forward Kinematics Bone Lengths
        L_upper = int(head_r * 1.20)
        L_fore = int(head_r * 1.15)
        L_torso = int(head_r * (1.8 if archetype == 'child' else 2.2))
        L_thigh = int(head_r * (1.2 if archetype == 'child' else 1.6))
        L_calf = int(head_r * (1.2 if archetype == 'child' else 1.6))

        # Grounding & Shadow
        target_ground = ground_y or self.ground_y

        # Torso & Hips
        mid_hip = (int(mid_sh[0]), int(mid_sh[1] + L_torso))
        hip_span = int(head_r * (0.8 if archetype == 'female' else 0.7))
        p_hip_l = (int(mid_hip[0] - hip_span // 2), int(mid_hip[1]))
        p_hip_r = (int(mid_hip[0] + hip_span // 2), int(mid_hip[1]))

        # Detect if ankles are authentically near the floor or if framing is bust/half-body
        has_grounded_ankles = (np.sum(kps[15]) > 0 and np.sum(kps[16]) > 0 and kps[15][1] >= target_ground * 0.84)

        if has_grounded_ankles:
            # Full body in camera view
            ang_thigh_l = math.atan2(kps[13][1] - hip_l[1], kps[13][0] - hip_l[0])
            p_kn_l = (int(p_hip_l[0] + L_thigh * math.cos(ang_thigh_l)), int(p_hip_l[1] + L_thigh * math.sin(ang_thigh_l)))
            ang_calf_l = math.atan2(kps[15][1] - kps[13][1], kps[15][0] - kps[13][0])
            p_ank_l = (int(p_kn_l[0] + L_calf * math.cos(ang_calf_l)), int(p_kn_l[1] + L_calf * math.sin(ang_calf_l)))

            ang_thigh_r = math.atan2(kps[14][1] - hip_r[1], kps[14][0] - hip_r[0])
            p_kn_r = (int(p_hip_r[0] + L_thigh * math.cos(ang_thigh_r)), int(p_hip_r[1] + L_thigh * math.sin(ang_thigh_r)))
            ang_calf_r = math.atan2(kps[16][1] - kps[14][1], kps[16][0] - kps[14][0])
            p_ank_r = (int(p_kn_r[0] + L_calf * math.cos(ang_calf_r)), int(p_kn_r[1] + L_calf * math.sin(ang_calf_r)))
            actual_ground = max(p_ank_l[1], p_ank_r[1])
        else:
            # Bust / sitting shot: synthesize natural standing legs grounded on floor
            leg_span = target_ground - mid_hip[1]
            knee_y = mid_hip[1] + int(leg_span * 0.48)
            p_kn_l = (p_hip_l[0] - 8, knee_y)
            p_kn_r = (p_hip_r[0] + 8, knee_y)
            p_ank_l = (p_hip_l[0] - 14, target_ground)
            p_ank_r = (p_hip_r[0] + 14, target_ground)
            actual_ground = target_ground

        self.draw_shadow(draw, int(mid_sh[0]), actual_ground, rx=int(head_r * 1.5), ry=int(head_r * 0.35))

        # Arms Left
        ang_up_l = math.atan2(kps[7][1] - sh_l[1], kps[7][0] - sh_l[0]) if np.sum(kps[7]) > 0 else math.radians(115)
        p_el_l = (int(sh_l[0] + L_upper * math.cos(ang_up_l)), int(sh_l[1] + L_upper * math.sin(ang_up_l)))
        ang_fore_l = math.atan2(kps[9][1] - kps[7][1], kps[9][0] - kps[7][0]) if np.sum(kps[9]) > 0 else math.radians(85)
        p_wr_l = (int(p_el_l[0] + L_fore * math.cos(ang_fore_l)), int(p_el_l[1] + L_fore * math.sin(ang_fore_l)))

        # Arms Right
        ang_up_r = math.atan2(kps[8][1] - sh_r[1], kps[8][0] - sh_r[0]) if np.sum(kps[8]) > 0 else math.radians(65)
        p_el_r = (int(sh_r[0] + L_upper * math.cos(ang_up_r)), int(sh_r[1] + L_upper * math.sin(ang_up_r)))
        ang_fore_r = math.atan2(kps[10][1] - kps[8][1], kps[10][0] - kps[8][0]) if np.sum(kps[10]) > 0 else math.radians(95)
        p_wr_r = (int(p_el_r[0] + L_fore * math.cos(ang_fore_r)), int(p_el_r[1] + L_fore * math.sin(ang_fore_r)))

        ink = (15, 23, 42)
        white = (255, 255, 255)
        pen_w = max(4, int(7 * scale))

        # Render Legs
        self.draw_limb(draw, p_hip_l, p_kn_l, p_ank_l, width=pen_w, color=ink, outline=white)
        self.draw_limb(draw, p_hip_r, p_kn_r, p_ank_r, width=pen_w, color=ink, outline=white)
        # Feet shoes
        draw.line([p_ank_l, (p_ank_l[0] - int(16 * scale), p_ank_l[1])], fill=ink, width=pen_w)
        draw.line([p_ank_r, (p_ank_r[0] + int(16 * scale), p_ank_r[1])], fill=ink, width=pen_w)

        # Torso Spine & Collarbone
        draw.line([mid_hip, mid_sh], fill=white, width=pen_w + 4)
        draw.line([mid_hip, mid_sh], fill=ink, width=pen_w)
        draw.line([tuple(sh_l), tuple(sh_r)], fill=white, width=pen_w + 4)
        draw.line([tuple(sh_l), tuple(sh_r)], fill=ink, width=pen_w)

        # Neck
        draw.line([mid_sh, (int(mid_sh[0]), head_cy + head_r)], fill=white, width=pen_w + 2)
        draw.line([mid_sh, (int(mid_sh[0]), head_cy + head_r)], fill=ink, width=pen_w)

        # Arms
        self.draw_limb(draw, (int(sh_l[0]), int(sh_l[1])), p_el_l, p_wr_l, width=pen_w, color=ink, outline=white)
        self.draw_limb(draw, (int(sh_r[0]), int(sh_r[1])), p_el_r, p_wr_r, width=pen_w, color=ink, outline=white)

        # Head Circle
        draw.ellipse([head_cx - head_r - 2, head_cy - head_r - 2, head_cx + head_r + 2, head_cy + head_r + 2], fill=white)
        draw.ellipse([head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r], fill=white, outline=ink, width=pen_w)

        # Head Tilt Calculation
        tilt_angle = 0.0
        if np.sum(eye_l) > 0 and np.sum(eye_r) > 0:
            tilt_angle = math.atan2(eye_r[1] - eye_l[1], eye_r[0] - eye_l[0])

        # Eyes & Gaze
        eye_off_x = int(head_r * 0.35)
        eye_off_y = int(head_r * 0.10)
        eye_r_sz = max(2, int(head_r * 0.12))

        # Only draw natural eye pupils if NOT wearing full sunglasses
        has_sunglasses = (archetype in ('male', 'cool'))
        if not has_sunglasses:
            for side in (-1, 1):
                ex_local = side * eye_off_x
                ey_local = -eye_off_y
                ex_rot = ex_local * math.cos(tilt_angle) - ey_local * math.sin(tilt_angle)
                ey_rot = ex_local * math.sin(tilt_angle) + ey_local * math.cos(tilt_angle)
                ex = int(head_cx + ex_rot)
                ey = int(head_cy + ey_rot)
                draw.ellipse([ex - eye_r_sz, ey - eye_r_sz, ex + eye_r_sz, ey + eye_r_sz], fill=ink)

        # Lip-sync Mouth (Smooth subtle aperture)
        mouth_w = int(head_r * 0.38)
        mouth_cy = head_cy + int(head_r * 0.38)
        if energy > 0.18:
            mh = int(head_r * 0.10 + head_r * 0.28 * energy)
            draw.ellipse([head_cx - mouth_w//2, mouth_cy - mh//2, head_cx + mouth_w//2, mouth_cy + mh//2], fill=ink)
            if mh > 8:
                draw.arc([head_cx - mouth_w//2 + 3, mouth_cy, head_cx + mouth_w//2 - 3, mouth_cy + mh//2], start=0, end=180, fill=(244, 114, 182), width=2)
        else:
            draw.line([(head_cx - mouth_w//2, mouth_cy), (head_cx + mouth_w//2, mouth_cy)], fill=ink, width=3)

        # Archetype Specific Accessories
        if archetype == 'female' or archetype == 'girl':
            # Twin Anime Hair Ribbons & Pink Bow
            draw.arc([head_cx - head_r - 8, head_cy - head_r + 4, head_cx - head_r + 20, head_cy - head_r + 32], start=45, end=270, fill=(244, 114, 182), width=5)
            draw.arc([head_cx + head_r - 20, head_cy - head_r + 4, head_cx + head_r + 8, head_cy - head_r + 32], start=270, end=135, fill=(244, 114, 182), width=5)
            draw.ellipse([head_cx - 16, head_cy - head_r - 10, head_cx - 2, head_cy - head_r + 4], fill=(236, 72, 153))
            draw.ellipse([head_cx + 2, head_cy - head_r - 10, head_cx + 16, head_cy - head_r + 4], fill=(236, 72, 153))
            # Pink Cheek Blush
            draw.ellipse([head_cx - int(head_r * 0.65), head_cy + int(head_r * 0.15), head_cx - int(head_r * 0.35), head_cy + int(head_r * 0.40)], fill=(251, 113, 133, 180))
            draw.ellipse([head_cx + int(head_r * 0.35), head_cy + int(head_r * 0.15), head_cx + int(head_r * 0.65), head_cy + int(head_r * 0.40)], fill=(251, 113, 133, 180))
        elif archetype == 'male' or archetype == 'cool':
            # Cool Sunglasses & Red Tie
            sg_y = head_cy - eye_off_y
            draw.rectangle([head_cx - eye_off_x - 10, sg_y - 6, head_cx - eye_off_x + 10, sg_y + 6], fill=ink)
            draw.rectangle([head_cx + eye_off_x - 10, sg_y - 6, head_cx + eye_off_x + 10, sg_y + 6], fill=ink)
            draw.line([(head_cx - eye_off_x + 10, sg_y), (head_cx + eye_off_x - 10, sg_y)], fill=ink, width=3)
            # Necktie
            tie_top_y = int(mid_sh[1] + 6)
            tie_bot_y = int(mid_hip[1] - L_torso * 0.3)
            draw.polygon([(head_cx - 5, tie_top_y), (head_cx + 5, tie_top_y),
                          (head_cx + 8, tie_bot_y - 10), (head_cx, tie_bot_y), (head_cx - 8, tie_bot_y - 10)], fill=(225, 29, 72))
        elif archetype == 'child':
            # Cute Backwards Baseball Cap (Amber)
            cap_c = (245, 158, 11)
            draw.arc([head_cx - head_r - 2, head_cy - head_r - 6, head_cx + head_r + 2, head_cy], start=180, end=360, fill=cap_c, width=int(8 * scale))
            draw.line([(head_cx - head_r - 2, head_cy - 4), (head_cx - head_r - 18, head_cy - 10)], fill=cap_c, width=int(6 * scale))
        elif archetype == 'glasses' or archetype == 'smart':
            sg_y = head_cy - eye_off_y
            gw = int(head_r * 0.30)
            gh = int(head_r * 0.22)
            draw.rectangle([head_cx - eye_off_x - gw//2, sg_y - gh//2, head_cx - eye_off_x + gw//2, sg_y + gh//2], outline=ink, width=3)
            draw.rectangle([head_cx + eye_off_x - gw//2, sg_y - gh//2, head_cx + eye_off_x + gw//2, sg_y + gh//2], outline=ink, width=3)
            draw.line([(head_cx - eye_off_x + gw//2, sg_y), (head_cx + eye_off_x - gw//2, sg_y)], fill=ink, width=3)

    def render_stick_animal(self, draw, entity, t=0.0, frame_idx=0):
        """
        Renders an animated stick animal (dog, cat, bird) tracking genuine position and trajectory.
        """
        species = entity.get('species', 'dog')
        bbox = entity.get('bbox', [0, 0, 100, 100])
        cx, cy = entity.get('center', (100, 100))
        ground_y = int(entity.get('ground_y', self.ground_y))
        facing = entity.get('facing', 'right')
        
        box_w = max(30, bbox[2] - bbox[0])
        box_h = max(20, bbox[3] - bbox[1])
        scale = max(0.5, min(1.6, box_h / 140.0))
        
        ink = (15, 23, 42)
        white = (255, 255, 255)
        pen_w = max(3, int(6 * scale))

        # Ground Drop Shadow
        self.draw_shadow(draw, int(cx), ground_y, rx=int(45 * scale), ry=int(12 * scale))

        if species in ('dog', 'cat', 'horse', 'sheep', 'cow'):
            body_len = int(70 * scale)
            hip_x = int(cx - (body_len // 2 if facing == 'right' else -body_len // 2))
            sh_x = int(cx + (body_len // 2 if facing == 'right' else -body_len // 2))
            
            body_y = ground_y - int(55 * scale)
            hip_pt = (hip_x, body_y)
            sh_pt = (sh_x, body_y - int(5 * scale))
            
            # Spine Body Line
            draw.line([hip_pt, sh_pt], fill=white, width=pen_w + 4)
            draw.line([hip_pt, sh_pt], fill=ink, width=pen_w)
            
            # Head & Neck
            head_r = int(16 * scale)
            head_cx = sh_x + int((20 if facing == 'right' else -20) * scale)
            head_cy = body_y - int(20 * scale)
            draw.line([sh_pt, (head_cx, head_cy)], fill=white, width=pen_w + 2)
            draw.line([sh_pt, (head_cx, head_cy)], fill=ink, width=pen_w)
            
            draw.ellipse([head_cx - head_r - 2, head_cy - head_r - 2, head_cx + head_r + 2, head_cy + head_r + 2], fill=white)
            draw.ellipse([head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r], fill=white, outline=ink, width=pen_w)
            
            # Eyes & Snout
            eye_x = head_cx + int((4 if facing == 'right' else -4) * scale)
            draw.ellipse([eye_x - 3, head_cy - 4, eye_x + 3, head_cy + 2], fill=ink)
            
            if species == 'dog':
                # Floppy ears & Red Nose
                ear_x = head_cx - int((head_r if facing == 'right' else -head_r) * 0.8)
                draw.ellipse([ear_x - 4, head_cy - 6, ear_x + 6, head_cy + 16], fill=ink)
                nose_x = head_cx + int((head_r if facing == 'right' else -head_r))
                draw.ellipse([nose_x - 3, head_cy + 1, nose_x + 3, head_cy + 7], fill=(225, 29, 72))
                # Happy Wagging Tail (Sine wave)
                tail_wag = math.sin(t * 14.0) * 22
                tail_tip = (hip_x - int((26 if facing == 'right' else -26) * scale), int(body_y - 28 * scale + tail_wag))
                draw.line([hip_pt, tail_tip], fill=ink, width=pen_w)
            else:
                # Pointy Cat Ears & Arched Tail
                ear_x = head_cx - int((head_r * 0.5 if facing == 'right' else -head_r * 0.5))
                draw.polygon([(ear_x - 4, head_cy - head_r + 2), (ear_x, head_cy - head_r - 12), (ear_x + 4, head_cy - head_r + 2)], fill=ink)
                # Curved Tail
                tail_tip = (hip_x - int((24 if facing == 'right' else -24) * scale), body_y - int(32 * scale))
                draw.line([hip_pt, tail_tip], fill=ink, width=pen_w)

            # 4 Articulated Legs (with trot walk-cycle dynamics)
            leg_walk = math.sin(t * 10.0) * 12
            # Front leg 1 & 2
            f1 = (sh_x + 4, ground_y - int(25 * scale))
            draw.line([sh_pt, f1], fill=ink, width=pen_w)
            draw.line([f1, (f1[0] + 4, ground_y)], fill=ink, width=pen_w)
            
            f2 = (sh_x - 8, ground_y - int(25 * scale))
            draw.line([sh_pt, f2], fill=ink, width=pen_w)
            draw.line([f2, (f2[0] - 2, ground_y)], fill=ink, width=pen_w)
            
            # Back leg 1 & 2 (with hock joint)
            b1 = (hip_x - 10, ground_y - int(26 * scale))
            draw.line([hip_pt, b1], fill=ink, width=pen_w)
            draw.line([b1, (b1[0] + 8, ground_y)], fill=ink, width=pen_w)
            
            b2 = (hip_x + 8, ground_y - int(26 * scale))
            draw.line([hip_pt, b2], fill=ink, width=pen_w)
            draw.line([b2, (b2[0] + 6, ground_y)], fill=ink, width=pen_w)

        elif species == 'bird':
            # Stick Bird: 2 legs, round body, beak, flapping wings
            body_r = int(14 * scale)
            draw.ellipse([cx - body_r, cy - body_r, cx + body_r, cy + body_r], fill=white, outline=ink, width=pen_w)
            # Beak
            beak_x = cx + int((body_r + 8 if facing == 'right' else -body_r - 8))
            draw.polygon([(cx + (body_r if facing == 'right' else -body_r), cy - 4),
                          (beak_x, cy),
                          (cx + (body_r if facing == 'right' else -body_r), cy + 4)], fill=(245, 158, 11))
            # 2 Spindly legs
            draw.line([(cx - 4, cy + body_r), (cx - 4, ground_y)], fill=ink, width=3)
            draw.line([(cx + 4, cy + body_r), (cx + 4, ground_y)], fill=ink, width=3)
            # Flapping stick wing
            wing_flap = math.sin(t * 18.0) * 16
            draw.line([(cx, cy), (cx - int(18 * scale), int(cy - 12 + wing_flap))], fill=ink, width=pen_w)

    def render_multi_entity_frame(self, bg_image, entities, t=0.0, energy=0.5, default_style='auto', framing_mode='auto', frame_idx=0):
        """
        Renders all tracked entities (humans and animals) simultaneously onto background canvas with soft alpha shadows.
        """
        base_bg = bg_image.convert("RGBA")
        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")

        # Single Presenter Special Mode (if only 1 human and framing_mode == 'presenter')
        is_single_presenter = (framing_mode == 'presenter' and len(entities) == 1 and entities[0]['type'] == 'human')

        for ent in entities:
            if ent['type'] == 'human':
                kps = ent['kps']
                # Determine archetype
                if default_style != 'auto' and len(entities) == 1:
                    style = default_style
                else:
                    style = ent.get('archetype', 'male')
                    
                target_ground = int(ent.get('ground_y', self.ground_y))
                self.render_stick_human(draw, kps, ground_y=target_ground, archetype=style, energy=energy, t=t)
                
            elif ent['type'] == 'animal':
                self.render_stick_animal(draw, ent, t=t, frame_idx=frame_idx)

        # Draw Studio Presenter Desk if active
        if is_single_presenter:
            desk_y = int(self.height * 0.62)
            draw.rounded_rectangle([self.cx - 260, desk_y, self.cx + 260, self.height + 40], radius=24, fill=(30, 41, 59, 235), outline=(0, 229, 255), width=3)
            draw.line([(self.cx - 240, desk_y + 4), (self.cx + 240, desk_y + 4)], fill=(148, 163, 184), width=4)
            mic_x = self.cx + 120
            draw.line([(mic_x, desk_y + 10), (mic_x, desk_y - 45)], fill=(100, 116, 139), width=5)
            draw.rounded_rectangle([mic_x - 8, desk_y - 65, mic_x + 8, desk_y - 42], radius=6, fill=(15, 23, 42), outline=(0, 229, 255), width=2)

        composited = Image.alpha_composite(base_bg, overlay)
        rgb_img = composited.convert("RGB")
        return cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2BGR)

    def render_mocap_frame(self, bg_image, joints, t=0.0, energy=0.5, character_style='classic', framing_mode='auto'):
        """
        Backward-compatible single-actor joints interface.
        """
        pil_frame = bg_image.copy()
        draw = ImageDraw.Draw(pil_frame, "RGBA")

        if joints is None:
            # Idle gentle breath animation
            joints = {
                "nose": {"x": 0.50, "y": 0.38 + 0.01 * math.sin(t * 2.0), "z": 0.0, "visibility": 0.99},
                "l_shoulder": {"x": 0.58, "y": 0.48, "z": 0.0, "visibility": 0.99},
                "r_shoulder": {"x": 0.42, "y": 0.48, "z": 0.0, "visibility": 0.99},
                "l_elbow": {"x": 0.63, "y": 0.60, "z": 0.0, "visibility": 0.99},
                "r_elbow": {"x": 0.37, "y": 0.60, "z": 0.0, "visibility": 0.99},
                "l_wrist": {"x": 0.65, "y": 0.72, "z": 0.0, "visibility": 0.99},
                "r_wrist": {"x": 0.35, "y": 0.72, "z": 0.0, "visibility": 0.99},
                "l_hip": {"x": 0.54, "y": 0.65, "z": 0.0, "visibility": 0.99},
                "r_hip": {"x": 0.46, "y": 0.65, "z": 0.0, "visibility": 0.99},
                "l_knee": {"x": 0.54, "y": 0.76, "z": 0.0, "visibility": 0.99},
                "r_knee": {"x": 0.46, "y": 0.76, "z": 0.0, "visibility": 0.99},
                "l_ankle": {"x": 0.54, "y": 0.82, "z": 0.0, "visibility": 0.99},
                "r_ankle": {"x": 0.46, "y": 0.82, "z": 0.0, "visibility": 0.99}
            }

        # Convert dictionary to COCO 17 array
        kps = np.zeros((17, 2), dtype=np.float32)
        def _get_pt(k):
            val = joints.get(k, {})
            return (val.get('x', 0.5) * self.width, val.get('y', 0.5) * self.height)
            
        kps[0] = _get_pt('nose')
        kps[1] = _get_pt('l_eye')
        kps[2] = _get_pt('r_eye')
        kps[5] = _get_pt('l_shoulder')
        kps[6] = _get_pt('r_shoulder')
        kps[7] = _get_pt('l_elbow')
        kps[8] = _get_pt('r_elbow')
        kps[9] = _get_pt('l_wrist')
        kps[10] = _get_pt('r_wrist')
        kps[11] = _get_pt('l_hip')
        kps[12] = _get_pt('r_hip')
        kps[13] = _get_pt('l_knee')
        kps[14] = _get_pt('r_knee')
        kps[15] = _get_pt('l_ankle')
        kps[16] = _get_pt('r_ankle')

        arch = 'female' if character_style == 'girl' else ('child' if character_style == 'child' else character_style)
        self.render_stick_human(draw, kps, ground_y=self.ground_y, archetype=arch, energy=energy, t=t)

        if framing_mode == 'presenter':
            desk_y = int(self.height * 0.62)
            draw.rounded_rectangle([self.cx - 260, desk_y, self.cx + 260, self.height + 40], radius=24, fill=(30, 41, 59, 235), outline=(0, 229, 255), width=3)
            draw.line([(self.cx - 240, desk_y + 4), (self.cx + 240, desk_y + 4)], fill=(148, 163, 184), width=4)
            mic_x = self.cx + 120
            draw.line([(mic_x, desk_y + 10), (mic_x, desk_y - 45)], fill=(100, 116, 139), width=5)
            draw.rounded_rectangle([mic_x - 8, desk_y - 65, mic_x + 8, desk_y - 42], radius=6, fill=(15, 23, 42), outline=(0, 229, 255), width=2)

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


def run_mocap_pipeline(video_path, background_image_path, output_mp4, character_style='auto', framing_mode='auto', target_fps=30):
    """
    Complete Multi-Entity Video-to-Stickman Motion Capture Production Pipeline.
    1. Tracks multi-human postures and animals frame-by-frame via YOLO-Pose & YOLO-Object.
    2. Renders dynamic stickmen (men, women, children, dogs, cats) following motion over custom background.
    3. Multiplexes original source audio into final high-res MP4.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Input video not found: {video_path}")

    work_video, temp_to_clean = ensure_compatible_h264(video_path)

    cap = cv2.VideoCapture(work_video)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or target_fps
    width = 720
    height = 1280

    engine = MocapStickmanEngine(width=width, height=height)
    bg_img = engine.load_background(background_image_path)

    audio_env = extract_audio_envelope(video_path, total_frames, fps=src_fps)

    temp_raw = output_mp4 + ".raw.mp4"
    os.makedirs(os.path.dirname(os.path.abspath(output_mp4)), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_raw, fourcc, src_fps, (width, height))

    print(f"[MoCap Pipeline] 🎬 Multi-Entity Tracking & Rendering {total_frames} frames ({character_style}, framing={framing_mode})...")
    f_idx = 0
    t0 = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        t = f_idx / src_fps
        energy = audio_env[f_idx] if f_idx < len(audio_env) else 0.5

        # Detect multiple humans and animals with demographic classification
        # Animal detection runs every 3rd frame to optimize CPU rendering throughput
        run_animal = (f_idx % 3 == 0)
        entities = engine.entity_tracker.analyze_frame(frame, frame_idx=f_idx, fps=src_fps, run_animal_detection=run_animal)

        # Render Multi-Entity Stickman Frame
        rendered_bgr = engine.render_multi_entity_frame(
            bg_img, entities, t=t, energy=energy,
            default_style=character_style, framing_mode=framing_mode, frame_idx=f_idx
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
    _char_style = sys.argv[4] if len(sys.argv) > 4 else 'auto'
    _framing = sys.argv[5] if len(sys.argv) > 5 else 'auto'
    run_mocap_pipeline(_video_in, _bg_in, _video_out, character_style=_char_style, framing_mode=_framing)
