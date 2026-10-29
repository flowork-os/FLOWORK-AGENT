#!/usr/bin/env python3
# [FL_INDEX: keywords="stick_hub_storyteller_engine, stickman_animation, viral_cartoon, kinetic_subtitles, walk_cycle, audio_lipsync, rubber_hose, storytelling" | purpose="Sovereign Stick Hub animated storyteller engine delivering high-fidelity full-body solo cartoon stickman animations with dynamic walk cycles, lip-sync, expressive poses, and clean kinetic subtitles"]
"""
Stick Hub Animated Storyteller Engine
High-fidelity 2D dynamic animation engine inspired by Stick Hub Animation
and Alan Becker viral cartoon standards.
Co-authored-by: Flowork OS <agent@floworkos.com>
"""

import sys
import os
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Import props from stickman_renderer if available
try:
    from stickman_renderer import PROP_DRAW, Local, G, font
except ImportError:
    PROP_DRAW = {}
    Local = None
    G = None
    font = None


def ease_out_back(x):
    x = max(0.0, min(1.0, x))
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


class StorytellerCanvas:
    """Logical coordinate canvas wrapper with exact 1.0 scaling."""
    def __init__(self, img):
        self.d = ImageDraw.Draw(img)
        self.s = 1.0

    def p(self, pt):
        return (int(pt[0] * self.s), int(pt[1] * self.s))

    def wd(self, w):
        return max(1, int(round(w * self.s)))

    def line(self, pts, w, col=(27, 27, 31)):
        pp = [self.p(q) for q in pts]
        self.d.line(pp, fill=col, width=self.wd(w), joint="curve")
        r = w * self.s / 2
        for q in (pp[0], pp[-1]):
            self.d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)

    def circle(self, c, r, fill=None, outline=None, w=0):
        x, y = self.p(c)
        r = r * self.s
        self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=outline, width=self.wd(w) if outline else 0)

    def ellipse(self, box, fill=None, outline=None, w=0):
        self.d.ellipse([*self.p(box[:2]), *self.p(box[2:])], fill=fill, outline=outline, width=self.wd(w) if outline else 0)

    def rrect(self, box, rad, fill=None, outline=None, w=0):
        self.d.rounded_rectangle([*self.p(box[:2]), *self.p(box[2:])], radius=rad * self.s, fill=fill,
                                 outline=outline, width=self.wd(w) if outline else 0)

    def poly(self, pts, fill=None, outline=None, w=0):
        pp = [self.p(q) for q in pts]
        if fill:
            self.d.polygon(pp, fill=fill)
        if outline:
            self.line(list(pts) + [pts[0], pts[1]], w, outline)

    def arc(self, box, a0, a1, col, w):
        self.d.arc([*self.p(box[:2]), *self.p(box[2:])], a0, a1, fill=col, width=self.wd(w))

    def text(self, xy, s, px, fill=(27, 27, 31), stroke=0, stroke_fill=(27, 27, 31), anchor="mm"):
        self.d.text(self.p(xy), s, font=font(int(px * self.s)) if font else ImageFont.load_default(), fill=fill, anchor=anchor)


class StorytellerLocal:
    """Prop local space centered around cx, cy."""
    def __init__(self, g, cx, cy, k, bg, acc):
        self.g, self.cx, self.cy, self.k, self.bg, self.acc = g, cx, cy, k, bg, acc

    def pt(self, x, y):
        return (self.cx + x * self.k, self.cy + y * self.k)

    def line(self, pts, w=10, col=(27, 27, 31)):
        self.g.line([self.pt(*q) for q in pts], w * self.k, col)

    def circle(self, x, y, r, fill=None, ink=True, w=9):
        self.g.circle(self.pt(x, y), r * self.k, fill, (27, 27, 31) if ink else None, w * self.k)

    def ell(self, x0, y0, x1, y1, fill=None, ink=True, w=9):
        self.g.ellipse([*self.pt(x0, y0), *self.pt(x1, y1)], fill, (27, 27, 31) if ink else None, w * self.k)

    def rrect(self, x0, y0, x1, y1, rad=14, fill=None, ink=True, w=9):
        self.g.rrect([*self.pt(x0, y0), *self.pt(x1, y1)], rad * self.k, fill, (27, 27, 31) if ink else None, w * self.k)

    def poly(self, pts, fill=None, ink=True, w=9):
        self.g.poly([self.pt(*q) for q in pts], fill, (27, 27, 31) if ink else None, w * self.k)

    def arc(self, x0, y0, x1, y1, a0, a1, w=9, col=(27, 27, 31)):
        self.g.arc([*self.pt(x0, y0), *self.pt(x1, y1)], a0, a1, col, w * self.k)

    def text(self, x, y, s, px, fill=(27, 27, 31), stroke=0):
        self.g.text(self.pt(x, y), s, px * self.k, fill, stroke * self.k)


class StickHubStorytellerEngine:
    def __init__(self, width=720, height=1280):
        self.width = width
        self.height = height
        self.scale = 1.15 * (self.height / 1280.0)
        self.ground_y = int(self.height * 0.82)
        self.cx = self.width // 2

        # High-res TrueType fonts for clean kinetic subtitles and UI
        self.font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if not os.path.exists(self.font_bold_path):
            self.font_bold_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

    def _get_font(self, size):
        try:
            return ImageFont.truetype(self.font_bold_path, int(size))
        except Exception:
            return ImageFont.load_default()

    def quadratic_bezier(self, p0, p1, p2, num_points=24):
        points = []
        for i in range(num_points + 1):
            u = i / float(num_points)
            x = (1 - u)**2 * p0[0] + 2 * (1 - u) * u * p1[0] + u**2 * p2[0]
            y = (1 - u)**2 * p0[1] + 2 * (1 - u) * u * p1[1] + u**2 * p2[1]
            points.append((int(x), int(y)))
        return points

    def draw_bezier_limb(self, draw, p0, p1, p2, width=12, color=(27, 27, 31), outline=(255, 255, 255), outline_w=2):
        pts = self.quadratic_bezier(p0, p1, p2, num_points=24)
        if len(pts) >= 2:
            if outline and outline_w > 0:
                draw.line(pts, fill=outline, width=width + outline_w * 2, joint="curve")
            draw.line(pts, fill=color, width=width, joint="curve")
        r = width // 2
        for pt in [p0, p2]:
            if outline and outline_w > 0:
                draw.ellipse([pt[0] - r - outline_w, pt[1] - r - outline_w,
                              pt[0] + r + outline_w, pt[1] + r + outline_w], fill=outline)
            draw.ellipse([pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r], fill=color)

    # -------------------------------------------------------------
    # LAYER 1: Background & Ground Staging
    # -------------------------------------------------------------
    def draw_background(self, pil_img, draw, t, bg_image_path=None, stage_theme='minimal_clean'):
        # Option A: Custom or AI Generated Background Image
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
                pil_img.paste(resized, (0, 0))

                # Soft ground horizon shadow
                ground_overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
                g_draw = ImageDraw.Draw(ground_overlay)
                g_draw.line([(0, self.ground_y), (self.width, self.ground_y)], fill=(0, 0, 0, 60), width=3)
                pil_img.alpha_composite(ground_overlay)
                return (240, 240, 240)  # assume background is present
            except Exception as e:
                print(f"[StickHubEngine] Warning loading bg {bg_image_path}: {e}", file=sys.stderr)

        # Option B: Clean Procedural Minimal Cartoon Stage (Stick Hub Aesthetic)
        th = (stage_theme or 'minimal_clean').lower()
        if 'dark' in th or 'cyber' in th:
            top_c = (15, 23, 42)
            bot_c = (30, 41, 59)
            ground_c = (10, 15, 26)
            line_c = (56, 189, 248)
        else:
            # Stick Hub classic warm paper/minimal cartoon look
            top_c = (248, 246, 240)
            bot_c = (235, 233, 225)
            ground_c = (220, 218, 210)
            line_c = (180, 178, 170)

        # Vertical wall gradient
        for y in range(self.ground_y):
            ratio = y / float(self.ground_y)
            r = int(top_c[0] + (bot_c[0] - top_c[0]) * ratio)
            g = int(top_c[1] + (bot_c[1] - top_c[1]) * ratio)
            b = int(top_c[2] + (bot_c[2] - top_c[2]) * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

        # Ground floor
        draw.rectangle([0, self.ground_y, self.width, self.height], fill=ground_c)
        draw.line([(0, self.ground_y), (self.width, self.ground_y)], fill=line_c, width=4)

        # Subtle comic perspective grid lines on the ground
        for offset_x in [-280, -140, 0, 140, 280]:
            x_top = self.cx + offset_x
            x_bot = self.cx + int(offset_x * 1.6)
            draw.line([(x_top, self.ground_y), (x_bot, self.height)], fill=(line_c[0], line_c[1], line_c[2], 80), width=2)

        return bot_c

    # -------------------------------------------------------------
    # LAYER 2: Kinetic Legs, Torso & Walk Cycle
    # -------------------------------------------------------------
    def draw_character(self, draw, cx, t, energy, action, emotion, is_walking=False, walk_offset=0.0):
        sc = self.scale
        leg_len = 160 * sc
        torso_len = 175 * sc
        head_r = int(58 * sc)
        ink_color = (25, 27, 34)
        white_color = (255, 255, 255)
        accent_color = (0, 229, 255)

        sad = (emotion == 'sad' or action == 'sad')
        breath = math.sin(t * 2.6) * 4 * sc

        # Ground & Hop Calculation
        if is_walking:
            # 4-stage procedural walk cycle
            walk_freq = 6.2  # stride cadence
            phi = t * walk_freq
            bounce = abs(math.cos(phi)) * 14 * sc
            gy = self.ground_y - bounce

            # Hip position
            hip = (int(cx), int(gy - leg_len))

            # Leg 1 (Front): Swings forward & plants
            l1_phase = phi
            foot1_x = int(cx + math.sin(l1_phase) * 55 * sc)
            foot1_lift = max(0.0, -math.cos(l1_phase)) * 26 * sc
            foot1_y = int(self.ground_y - foot1_lift)
            knee1_x = int((hip[0] + foot1_x) // 2 + 12 * sc)
            knee1_y = int((hip[1] + foot1_y) // 2)

            # Leg 2 (Back): Swings backward & lifts
            l2_phase = phi + math.pi
            foot2_x = int(cx + math.sin(l2_phase) * 55 * sc)
            foot2_lift = max(0.0, -math.cos(l2_phase)) * 26 * sc
            foot2_y = int(self.ground_y - foot2_lift)
            knee2_x = int((hip[0] + foot2_x) // 2 - 12 * sc)
            knee2_y = int((hip[1] + foot2_y) // 2)

            # Ground Shadow
            sw = int(140 * sc - bounce * 1.5)
            draw.ellipse([cx - sw, self.ground_y - 8, cx + sw, self.ground_y + 16], fill=(0, 0, 0, 50))

            # Draw Legs (Bezier)
            limb_w = max(8, int(13 * sc))
            self.draw_bezier_limb(draw, hip, (knee2_x, knee2_y), (foot2_x, foot2_y), width=limb_w, color=ink_color, outline=white_color)
            self.draw_bezier_limb(draw, hip, (knee1_x, knee1_y), (foot1_x, foot1_y), width=limb_w, color=ink_color, outline=white_color)
            # Feet lines
            draw.line([(foot2_x, foot2_y), (foot2_x + int(24 * sc), foot2_y)], fill=ink_color, width=limb_w)
            draw.line([(foot1_x, foot1_y), (foot1_x + int(24 * sc), foot1_y)], fill=ink_color, width=limb_w)

            # Torso with slight forward lean during walk
            lean = 14 * sc
            neck = (int(hip[0] + lean), int(hip[1] - torso_len))
            draw.line([hip, neck], fill=white_color, width=limb_w + 4)
            draw.line([hip, neck], fill=ink_color, width=limb_w)

            # Arms swing in opposition to legs during walk
            arm_swing = math.sin(phi) * 45 * sc
            sh_l = (int(neck[0] - 12 * sc), int(neck[1] + 16 * sc))
            sh_r = (int(neck[0] + 12 * sc), int(neck[1] + 16 * sc))

            el_l = (int(sh_l[0] - arm_swing * 0.7), int(sh_l[1] + 65 * sc))
            hand_l = (int(el_l[0] - arm_swing), int(el_l[1] + 60 * sc))

            el_r = (int(sh_r[0] + arm_swing * 0.7), int(sh_r[1] + 65 * sc))
            hand_r = (int(el_r[0] + arm_swing), int(el_r[1] + 60 * sc))

            self.draw_bezier_limb(draw, sh_l, el_l, hand_l, width=limb_w - 1, color=ink_color, outline=white_color)
            self.draw_bezier_limb(draw, sh_r, el_r, hand_r, width=limb_w - 1, color=ink_color, outline=white_color)

        else:
            # Standing dynamic stance with natural breathing & weight shift
            breath = math.sin(t * 2.6) * 4 * sc
            gy = self.ground_y
            hip = (int(cx), int(gy - leg_len + breath * 0.3))

            # Ground Shadow
            sw = int(155 * sc)
            draw.ellipse([cx - sw, gy - 8, cx + sw, gy + 16], fill=(0, 0, 0, 50))

            # Standing Legs with natural solid stance
            limb_w = max(8, int(13 * sc))
            for side in (-1, 1):
                foot = (int(cx + side * 44 * sc), gy)
                knee = (int(cx + side * 28 * sc), int(gy - leg_len * 0.5))
                self.draw_bezier_limb(draw, hip, knee, foot, width=limb_w, color=ink_color, outline=white_color)
                draw.line([foot, (foot[0] + int(side * 26 * sc), gy)], fill=ink_color, width=limb_w)

            # Torso
            sad = emotion == 'sad' or action == 'sad'
            lean = 12 * sc if sad else 0.0
            neck = (int(cx + lean), int(hip[1] - torso_len + breath * 0.5))
            draw.line([hip, neck], fill=white_color, width=limb_w + 4)
            draw.line([hip, neck], fill=ink_color, width=limb_w)

            # Arms & Expressive Gestures
            sh_l = (int(neck[0] - 12 * sc), int(neck[1] + 16 * sc))
            sh_r = (int(neck[0] + 12 * sc), int(neck[1] + 16 * sc))
            self.draw_standing_arms(draw, sh_l, sh_r, action, t, energy, sc, limb_w, ink_color, white_color)

        # Scarf / Accent Collar (Stick Hub Trademark Personality)
        draw.line([(int(neck[0] - 28 * sc), int(neck[1] + 4 * sc)),
                   (int(neck[0] + 28 * sc), int(neck[1] + 4 * sc))], fill=accent_color, width=int(16 * sc))
        sway = math.sin(t * 3.2) * 8 * sc
        draw.polygon([(int(neck[0] + 12 * sc), int(neck[1] + 8 * sc)),
                      (int(neck[0] + 38 * sc + sway), int(neck[1] + 62 * sc)),
                      (int(neck[0] + 8 * sc + sway), int(neck[1] + 58 * sc))], fill=accent_color)

        # Head & Face Rig
        head_cx = int(neck[0] + (12 * sc if sad else 0))
        head_cy = int(neck[1] - head_r - 6 * sc + breath * 0.4)
        self.draw_head_and_face(draw, head_cx, head_cy, head_r, emotion, energy, t, sc, ink_color, white_color)

        return (head_cx, head_cy)

    # -------------------------------------------------------------
    # LAYER 3: Standing Arm Poses & Bezier Gestures
    # -------------------------------------------------------------
    def draw_standing_arms(self, draw, sh_l, sh_r, action, t, energy, sc, limb_w, ink_color, white_color):
        act = (action or 'talk').lower()
        s = math.sin

        if 'point' in act:
            # Right arm points forward/up emphatically
            el_r = (int(sh_r[0] + 65 * sc), int(sh_r[1] - 40 * sc))
            hand_r = (int(sh_r[0] + 140 * sc + s(t * 3.0) * 8 * sc), int(sh_r[1] - 90 * sc))
            # Left arm relaxed at hip
            el_l = (int(sh_l[0] - 40 * sc), int(sh_l[1] + 60 * sc))
            hand_l = (int(sh_l[0] - 25 * sc), int(sh_l[1] + 110 * sc))

        elif 'think' in act:
            # Right hand touches chin / head
            el_r = (int(sh_r[0] + 55 * sc), int(sh_r[1] + 35 * sc))
            hand_r = (int(sh_r[0] + 15 * sc), int(sh_r[1] - 70 * sc))
            # Left arm folded across chest
            el_l = (int(sh_l[0] - 45 * sc), int(sh_l[1] + 45 * sc))
            hand_l = (int(sh_l[0] + 25 * sc), int(sh_l[1] + 45 * sc))

        elif 'excited' in act or 'celebrate' in act:
            # Both hands raised joyfully waving in air
            w1 = s(t * 8.0) * 16 * sc
            w2 = s(t * 8.0 + 1.5) * 16 * sc
            el_l = (int(sh_l[0] - 65 * sc), int(sh_l[1] - 50 * sc))
            hand_l = (int(sh_l[0] - 110 * sc + w1), int(sh_l[1] - 130 * sc))
            el_r = (int(sh_r[0] + 65 * sc), int(sh_r[1] - 50 * sc))
            hand_r = (int(sh_r[0] + 110 * sc + w2), int(sh_r[1] - 130 * sc))

        elif 'shrug' in act:
            # Elbows bent outward, hands upturned
            el_l = (int(sh_l[0] - 75 * sc), int(sh_l[1] + 25 * sc))
            hand_l = (int(sh_l[0] - 110 * sc), int(sh_l[1] - 25 * sc))
            el_r = (int(sh_r[0] + 75 * sc), int(sh_r[1] + 25 * sc))
            hand_r = (int(sh_r[0] + 110 * sc), int(sh_r[1] - 25 * sc))

        elif 'stop' in act or 'warn' in act:
            # Right hand open palm extended forward
            el_r = (int(sh_r[0] + 55 * sc), int(sh_r[1] + 10 * sc))
            hand_r = (int(sh_r[0] + 120 * sc), int(sh_r[1] + 10 * sc))
            # Left arm at side
            el_l = (int(sh_l[0] - 35 * sc), int(sh_l[1] + 60 * sc))
            hand_l = (int(sh_l[0] - 25 * sc), int(sh_l[1] + 110 * sc))

        elif 'hips' in act:
            # Hands firmly on hips
            el_l = (int(sh_l[0] - 60 * sc), int(sh_l[1] + 45 * sc))
            hand_l = (int(sh_l[0] - 20 * sc), int(sh_l[1] + 75 * sc))
            el_r = (int(sh_r[0] + 60 * sc), int(sh_r[1] + 45 * sc))
            hand_r = (int(sh_r[0] + 20 * sc), int(sh_r[1] + 75 * sc))

        elif 'sad' in act:
            # Arms hanging limp
            el_l = (int(sh_l[0] - 20 * sc), int(sh_l[1] + 65 * sc))
            hand_l = (int(sh_l[0] - 15 * sc), int(sh_l[1] + 120 * sc))
            el_r = (int(sh_r[0] + 20 * sc), int(sh_r[1] + 65 * sc))
            hand_r = (int(sh_r[0] + 15 * sc), int(sh_r[1] + 120 * sc))

        else:
            # Default 'talk': Active conversational gesturing driven by speech energy
            talk_wave = s(t * 5.0) * (20 + 25 * energy) * sc
            el_r = (int(sh_r[0] + 45 * sc), int(sh_r[1] + 45 * sc))
            hand_r = (int(sh_r[0] + 85 * sc), int(sh_r[1] + talk_wave))

            el_l = (int(sh_l[0] - 35 * sc), int(sh_l[1] + 55 * sc))
            hand_l = (int(sh_l[0] - 20 * sc), int(sh_l[1] + 105 * sc))

        self.draw_bezier_limb(draw, sh_l, el_l, hand_l, width=limb_w - 1, color=ink_color, outline=white_color)
        self.draw_bezier_limb(draw, sh_r, el_r, hand_r, width=limb_w - 1, color=ink_color, outline=white_color)

    # -------------------------------------------------------------
    # LAYER 4: Expressive Head, Eyes, Eyebrows & Audio-Reactive Lipsync
    # -------------------------------------------------------------
    def draw_head_and_face(self, draw, hx, hy, r, emotion, energy, t, sc, ink_color, white_color):
        # 1. Head circle with crisp outline
        draw.ellipse([hx - r - 2, hy - r - 2, hx + r + 2, hy + r + 2], fill=white_color)
        draw.ellipse([hx - r, hy - r, hx + r, hy + r], fill=white_color, outline=ink_color, width=max(4, int(7 * sc)))

        # 2. Eye gaze & blinking
        blink = (t % 3.4) < 0.12
        look_dx = int(math.sin(t * 1.5) * 4 * sc)
        look_dy = int(math.cos(t * 1.2) * 2 * sc)
        if emotion == 'thinking':
            look_dx, look_dy = int(8 * sc), int(-8 * sc)
        elif emotion == 'sad':
            look_dx, look_dy = 0, int(6 * sc)

        eye_offset_x = int(18 * sc)
        eye_y = int(hy - 6 * sc)
        eye_r = max(4, int(6.5 * sc))

        for side in (-1, 1):
            ex = hx + side * eye_offset_x + look_dx
            ey = eye_y + look_dy
            if blink:
                draw.line([(ex - int(7 * sc), ey), (ex + int(7 * sc), ey)], fill=ink_color, width=max(2, int(4 * sc)))
            elif emotion == 'surprised':
                draw.ellipse([ex - eye_r - 4, ey - eye_r - 4, ex + eye_r + 4, ey + eye_r + 4], fill=white_color, outline=ink_color, width=int(3 * sc))
                draw.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=ink_color)
            else:
                draw.ellipse([ex - eye_r, ey - eye_r, ex + eye_r, ey + eye_r], fill=ink_color)

        # 3. Expressive Eyebrows
        brow_y = hy - int(24 * sc)
        brow_w = int(18 * sc)
        if emotion == 'angry':
            draw.line([(hx - eye_offset_x - brow_w//2, brow_y - int(4 * sc)), (hx - eye_offset_x + brow_w//2, brow_y + int(6 * sc))], fill=ink_color, width=int(4 * sc))
            draw.line([(hx + eye_offset_x - brow_w//2, brow_y + int(6 * sc)), (hx + eye_offset_x + brow_w//2, brow_y - int(4 * sc))], fill=ink_color, width=int(4 * sc))
        elif emotion in ('worried', 'sad'):
            draw.line([(hx - eye_offset_x - brow_w//2, brow_y + int(6 * sc)), (hx - eye_offset_x + brow_w//2, brow_y - int(4 * sc))], fill=ink_color, width=int(4 * sc))
            draw.line([(hx + eye_offset_x - brow_w//2, brow_y - int(4 * sc)), (hx + eye_offset_x + brow_w//2, brow_y + int(6 * sc))], fill=ink_color, width=int(4 * sc))
        elif emotion == 'thinking':
            draw.line([(hx - eye_offset_x - brow_w//2, brow_y), (hx - eye_offset_x + brow_w//2, brow_y)], fill=ink_color, width=int(4 * sc))
            draw.line([(hx + eye_offset_x - brow_w//2, brow_y - int(8 * sc)), (hx + eye_offset_x + brow_w//2, brow_y - int(8 * sc))], fill=ink_color, width=int(4 * sc))
        else:
            # Normal friendly arch
            draw.arc([hx - eye_offset_x - brow_w//2, brow_y - int(6 * sc), hx - eye_offset_x + brow_w//2, brow_y + int(6 * sc)], start=190, end=350, fill=ink_color, width=int(4 * sc))
            draw.arc([hx + eye_offset_x - brow_w//2, brow_y - int(6 * sc), hx + eye_offset_x + brow_w//2, brow_y + int(6 * sc)], start=190, end=350, fill=ink_color, width=int(4 * sc))

        # 4. Audio-Reactive Mouth (Procedural Lip-Sync)
        mouth_x = hx + int(look_dx * 0.5)
        mouth_y = hy + int(24 * sc + look_dy * 0.5)

        if energy > 0.12:
            # Speaking: open mouth scaled to energy
            mw = int((12 + 10 * energy) * sc)
            mh = int((6 + 18 * energy) * sc)
            draw.ellipse([mouth_x - mw, mouth_y - mh//2, mouth_x + mw, mouth_y + mh//2], fill=ink_color)
            # Little tongue or teeth pop inside open mouth
            if mh > 12 * sc:
                draw.arc([mouth_x - mw + 4, mouth_y, mouth_x + mw - 4, mouth_y + mh//2], start=0, end=180, fill=(244, 114, 182), width=int(4 * sc))
        elif emotion == 'happy':
            # Wide smile arc
            draw.arc([mouth_x - int(16 * sc), mouth_y - int(12 * sc), mouth_x + int(16 * sc), mouth_y + int(10 * sc)], start=15, end=165, fill=ink_color, width=int(4 * sc))
        elif emotion in ('sad', 'worried'):
            # Downward frown arc
            draw.arc([mouth_x - int(14 * sc), mouth_y + int(2 * sc), mouth_x + int(14 * sc), mouth_y + int(22 * sc)], start=195, end=345, fill=ink_color, width=int(4 * sc))
        else:
            # Neutral / subtle smile line
            draw.line([(mouth_x - int(10 * sc), mouth_y), (mouth_x + int(10 * sc), mouth_y)], fill=ink_color, width=int(4 * sc))

    # -------------------------------------------------------------
    # LAYER 5: Pop-In Comic Props
    # -------------------------------------------------------------
    def draw_prop_item(self, pil_img, draw, prop_name, cx, cy, t, lt, sc):
        if not prop_name or prop_name not in PROP_DRAW:
            return
        k = ease_out_back(lt / 0.45)
        if k < 0.05:
            return

        prop_x = cx
        prop_y = int(self.height * 0.28)

        # Soft disc halo behind prop
        halo_r = int(120 * sc * min(1.05, k))
        halo_overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        h_draw = ImageDraw.Draw(halo_overlay)
        h_draw.ellipse([prop_x - halo_r, prop_y - halo_r, prop_x + halo_r, prop_y + halo_r], fill=(0, 229, 255, 45))
        pil_img.alpha_composite(halo_overlay)

        # Render prop using exact 1.0 scaling StorytellerLocal context
        g = StorytellerCanvas(pil_img)
        loc = StorytellerLocal(g, prop_x, prop_y, max(0.02, k) * sc * 0.85, (245, 245, 245), (0, 229, 255))
        PROP_DRAW[prop_name](loc, t, lt)

    # -------------------------------------------------------------
    # LAYER 6: Clean Kinetic Subtitles (High-Contrast Modern Typography)
    # -------------------------------------------------------------
    def draw_kinetic_subtitles(self, pil_img, draw, text, t, sc):
        if not text or text.strip() == "" or text.strip() == "[Music / Ambience]":
            return

        clean_text = text.strip()
        font_size = max(24, int(36 * (self.height / 1280.0)))
        font = self._get_font(font_size)

        # Word wrap text to fit within 88% width
        max_w = int(self.width * 0.86)
        words = clean_text.split()
        lines = []
        cur_line = []

        for w in words:
            test_line = " ".join(cur_line + [w])
            bbox = font.getbbox(test_line)
            w_px = bbox[2] - bbox[0]
            if w_px <= max_w:
                cur_line.append(w)
            else:
                if cur_line:
                    lines.append(" ".join(cur_line))
                cur_line = [w]
        if cur_line:
            lines.append(" ".join(cur_line))

        # Calculate bounding box for pill backdrop
        line_height = int(font_size * 1.35)
        total_text_h = len(lines) * line_height
        sub_y = int(self.height * 0.88 - total_text_h // 2)

        # Measure max line width
        max_line_w = 0
        for line in lines:
            bbox = font.getbbox(line)
            max_line_w = max(max_line_w, bbox[2] - bbox[0])

        pad_x = 24
        pad_y = 14
        pill_box = [
            self.cx - max_line_w // 2 - pad_x,
            sub_y - pad_y,
            self.cx + max_line_w // 2 + pad_x,
            sub_y + total_text_h + pad_y - int(font_size * 0.2)
        ]

        # Draw translucent rounded pill backdrop with cyan highlight border
        sub_overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(sub_overlay)
        s_draw.rounded_rectangle(pill_box, radius=18, fill=(15, 23, 42, 220), outline=(0, 229, 255, 230), width=2)
        pil_img.alpha_composite(sub_overlay)

        # Draw each line centered with high contrast white text
        for i, line in enumerate(lines):
            ly = sub_y + i * line_height
            bbox = font.getbbox(line)
            lw = bbox[2] - bbox[0]
            lx = self.cx - lw // 2
            # Drop shadow
            draw.text((lx + 2, ly + 2), line, font=font, fill=(0, 0, 0, 180))
            # Main white text
            draw.text((lx, ly), line, font=font, fill=(255, 255, 255))

    # -------------------------------------------------------------
    # MASTER FRAME RENDERER: Full Composite
    # -------------------------------------------------------------
    def render_frame(self, beat_data, t=0.0, energy=0.7):
        """
        Renders a single frame of Stick Hub Storyteller animation.
        Returns a cv2 BGR NumPy image array (width x height).
        """
        pil_img = Image.new("RGBA", (self.width, self.height), (245, 245, 245, 255))
        draw = ImageDraw.Draw(pil_img)

        # 1. Background
        custom_bg = beat_data.get("background_image") or beat_data.get("background_path")
        stage_theme = beat_data.get("stage_theme") or beat_data.get("background", "minimal_clean")
        self.draw_background(pil_img, draw, t, bg_image_path=custom_bg, stage_theme=stage_theme)

        # 2. Action & Movement Detection
        action = beat_data.get("action") or beat_data.get("pose", "talk")
        emotion = beat_data.get("emotion", "neutral")
        text = beat_data.get("text", "")
        text_lower = text.lower()

        # Semantic action heuristics if default talk
        is_walking = False
        if any(w in text_lower for w in ["walk", "jalan", "melangkah", "pergi", "bergerak", "run", "lari"]):
            is_walking = True
        elif action in ["walk", "run", "stride", "move"]:
            is_walking = True

        if not action or action == 'talk':
            if any(w in text_lower for w in ["pikir", "think", "kenapa", "mengapa", "tahu", "gimana"]):
                action = 'think'
                emotion = 'thinking'
            elif any(w in text_lower for w in ["kaget", "shock", "wow", "astaga", "lihat", "surprised"]):
                action = 'point'
                emotion = 'surprised'
            elif any(w in text_lower for w in ["senang", "cuan", "sukses", "hebat", "berhasil", "happy"]):
                action = 'excited'
                emotion = 'happy'
            elif any(w in text_lower for w in ["sedih", "kecewa", "rugi", "sayang", "sad"]):
                action = 'sad'
                emotion = 'sad'
            elif any(w in text_lower for w in ["stop", "tunggu", "jangan", "wait", "awas"]):
                action = 'stop'

        # Character position (stationary or subtle walking translation)
        char_x = self.cx
        if is_walking:
            # Walking across screen or subtle cyclical drift
            char_x = int(self.cx + math.sin(t * 0.8) * 40 * self.scale)

        # 3. Solo Animated Character
        head_pos = self.draw_character(draw, char_x, t, energy, action, emotion, is_walking=is_walking)

        # 4. Comic Props Pop-In
        prop_name = beat_data.get("prop")
        lt = beat_data.get("local_time", t % 3.0)
        if prop_name:
            self.draw_prop_item(pil_img, draw, prop_name, self.cx, head_pos[1] - int(100 * self.scale), t, lt, self.scale)

        # 5. Kinetic Story Subtitles
        self.draw_kinetic_subtitles(pil_img, draw, text, t, self.scale)

        # Return RGB NumPy image formatted for OpenCV
        rgb_img = pil_img.convert("RGB")
        return cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2BGR)
