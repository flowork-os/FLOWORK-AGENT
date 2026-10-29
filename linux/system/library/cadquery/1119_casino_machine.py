# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, casino_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: casino_machine

from __future__ import annotations

import cadquery as cq
import math

# ===== shim core =====
def _rpy_R(r, p, y):
    """Rotation matrix Rz(yaw)@Ry(pitch)@Rx(roll) as rows (URDF convention)."""
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    return (
        (cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
        (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
        (-sp,     cp * sr,                cp * cr),
    )

def _mat_mul(A, B):
    return tuple(
        tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )

def _mat_vec(A, v):
    return tuple(sum(A[i][k] * v[k] for k in range(3)) for i in range(3))

class _Tf:
    """Rigid transform: rotation matrix R (rows) + translation t."""
    __slots__ = ("R", "t")
    _I = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

    def __init__(self, R=None, t=(0.0, 0.0, 0.0)):
        self.R = R if R is not None else _Tf._I
        self.t = (float(t[0]), float(t[1]), float(t[2]))

    @staticmethod
    def from_origin(origin):
        if origin is None:
            return _Tf()
        xyz = getattr(origin, "xyz", (0.0, 0.0, 0.0))
        rpy = getattr(origin, "rpy", (0.0, 0.0, 0.0))
        return _Tf(_rpy_R(rpy[0], rpy[1], rpy[2]), xyz)

    def __matmul__(self, o):
        return _Tf(_mat_mul(self.R, o.R),
                   tuple(a + b for a, b in zip(_mat_vec(self.R, o.t), self.t)))

    def location(self):
        R, t = self.R, self.t
        xdir = cq.Vector(R[0][0], R[1][0], R[2][0])
        zdir = cq.Vector(R[0][2], R[1][2], R[2][2])
        return cq.Location(cq.Plane(origin=cq.Vector(*t), xDir=xdir, normal=zdir))

class ValidationError(ValueError):
    pass

class ArticulationType:
    REVOLUTE = "revolute"
    CONTINUOUS = "continuous"
    PRISMATIC = "prismatic"
    FIXED = "fixed"
    FLOATING = "floating"

class Origin:
    __slots__ = ("xyz", "rpy")

    def __init__(self, xyz=(0.0, 0.0, 0.0), rpy=(0.0, 0.0, 0.0)):
        self.xyz = (float(xyz[0]), float(xyz[1]), float(xyz[2]))
        self.rpy = (float(rpy[0]), float(rpy[1]), float(rpy[2]))

class Material:
    def __init__(self, name, rgba=None, texture=None, *, color=None):
        self.name = str(name)
        c = rgba if rgba is not None else color
        if c is not None:
            c = tuple(float(v) for v in c)
            if len(c) == 3:
                c = c + (1.0,)
        self.rgba = c
        self.texture = texture

class MotionLimits:
    def __init__(self, effort=1.0, velocity=1.0, lower=None, upper=None):
        self.effort = float(effort)
        self.velocity = float(velocity)
        self.lower = None if lower is None else float(lower)
        self.upper = None if upper is None else float(upper)

class Box:
    __slots__ = ("size",)

    def __init__(self, size):
        self.size = (float(size[0]), float(size[1]), float(size[2]))

    def _cq(self):
        sx, sy, sz = self.size
        return cq.Solid.makeBox(sx, sy, sz, cq.Vector(-sx / 2, -sy / 2, -sz / 2))

class Cylinder:
    __slots__ = ("radius", "length")

    def __init__(self, radius, length=None, *, height=None):
        self.radius = float(radius)
        self.length = float(height if length is None else length)

    @property
    def height(self):
        return self.length

    def _cq(self):
        return cq.Solid.makeCylinder(
            self.radius, self.length, cq.Vector(0, 0, -self.length / 2), cq.Vector(0, 0, 1)
        )

def _to_shape(model):
    """Coerce a cadquery object (Workplane/Shape/Assembly) or a shim geometry
    wrapper into a single cq.Shape."""
    if isinstance(model, _CQMesh):
        return model.shape
    if hasattr(model, "_cq"):
        return model._cq()
    if isinstance(model, cq.Assembly):
        return model.toCompound()
    if isinstance(model, cq.Workplane):
        vals = [v for v in model.vals() if isinstance(v, cq.Shape)]
        if not vals:
            raise ValidationError("cadquery Workplane has no shape values")
        return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)
    if isinstance(model, cq.Shape):
        return model
    raise ValidationError("unsupported cadquery model type: %r" % type(model))

class _CQMesh:
    """Mesh stand-in that simply carries an exact cadquery B-rep shape."""
    __slots__ = ("shape", "name")

    def __init__(self, shape, name=None):
        self.shape = shape
        self.name = name

    def _cq(self):
        return self.shape

def mesh_from_cadquery(model, name=None, **kwargs):
    return _CQMesh(_to_shape(model), name=name if isinstance(name, str) else None)

class Visual:
    __slots__ = ("geometry", "origin", "material", "name")

    def __init__(self, geometry, origin=None, material=None, name=None):
        self.geometry = geometry
        self.origin = origin or Origin()
        self.material = material
        self.name = name

class Part:
    def __init__(self, name, visuals=None, inertial=None, meta=None):
        self.name = name
        self.visuals = list(visuals or [])
        self.collisions = []
        self.inertial = inertial
        self.meta = dict(meta or {})

    def visual(self, geometry, *, origin=None, material=None, color=None, name=None):
        if color is not None and material is None:
            material = color if isinstance(color, (str, Material)) else Material("inline", rgba=color)
        v = Visual(geometry, origin=origin, material=material, name=name)
        self.visuals.append(v)
        return v

    def get_visual(self, name):
        for v in self.visuals:
            if v.name == name:
                return v
        raise ValidationError("unknown visual %r" % name)

class Articulation:
    def __init__(self, name, articulation_type, parent, child, origin=None,
                 axis=(0.0, 0.0, 1.0), motion_limits=None, motion_properties=None,
                 mimic=None, meta=None):
        self.name = name
        self.articulation_type = articulation_type
        self.parent = parent if isinstance(parent, str) else parent.name
        self.child = child if isinstance(child, str) else child.name
        self.origin = origin or Origin()
        self.axis = tuple(float(a) for a in axis)
        self.motion_limits = motion_limits
        self.motion_properties = motion_properties
        self.mimic = mimic
        self.meta = dict(meta or {})

    # aliases used by some scripts
    @property
    def joint_type(self):
        return self.articulation_type

    @property
    def limit(self):
        return self.motion_limits

class ArticulatedObject:
    def __init__(self, name, parts=None, articulations=None, materials=None, meta=None, assets=None):
        self.name = name
        self.parts = list(parts or [])
        self.articulations = list(articulations or [])
        self.materials = list(materials or [])
        self.meta = dict(meta or {})
        self.assets = assets

    # ---- builders ----
    def part(self, name, *, visuals=None, inertial=None, meta=None):
        p = Part(name, visuals=visuals, inertial=inertial, meta=meta)
        self.parts.append(p)
        return p

    link = part

    def articulation(self, name, articulation_type, parent, child, *, origin=None,
                     axis=None, motion_limits=None, motion_properties=None, mimic=None, meta=None):
        a = Articulation(name, articulation_type, parent, child, origin=origin,
                         axis=axis or (0.0, 0.0, 1.0), motion_limits=motion_limits,
                         motion_properties=motion_properties, mimic=mimic, meta=meta)
        self.articulations.append(a)
        return a

    def joint(self, name, joint_type, parent, child, *, origin=None, axis=None,
              limit=None, dynamics=None, mimic=None, meta=None):
        return self.articulation(name, joint_type, parent, child, origin=origin, axis=axis,
                                 motion_limits=limit, motion_properties=dynamics, mimic=mimic, meta=meta)

    def material(self, name, *, rgba=None, color=None, texture=None):
        m = Material(name, rgba=rgba, color=color, texture=texture)
        self.materials.append(m)
        return m

    def set_assets(self, assets):
        self.assets = assets
        return assets

    # ---- queries ----
    def get_part(self, name):
        key = name if isinstance(name, str) else name.name
        for p in self.parts:
            if p.name == key:
                return p
        raise ValidationError("unknown part %r" % name)

    get_link = get_part

    def get_articulation(self, name):
        key = name if isinstance(name, str) else getattr(name, "name", name)
        for a in self.articulations:
            if a.name == key:
                return a
        raise ValidationError("unknown articulation %r" % name)

    get_joint = get_articulation

    def root_parts(self):
        children = {a.child for a in self.articulations}
        return [p for p in self.parts if p.name not in children]

    root_links = root_parts

    def validate(self, *a, **k):
        return None

    def to_urdf(self, *a, **k):
        raise ValidationError("URDF export is not available in self-contained CadQuery mode")

    # ---- rest-pose world transform per part (URDF forward kinematics, q=0) ----
    def _world_transforms(self):
        parent_of, joint_tf = {}, {}
        for a in self.articulations:
            parent_of[a.child] = a.parent
            joint_tf[a.child] = _Tf.from_origin(a.origin)
        cache = {}

        def world(name):
            if name in cache:
                return cache[name]
            if name in parent_of:
                tf = world(parent_of[name]) @ joint_tf[name]
            else:
                tf = _Tf()
            cache[name] = tf
            return tf

        return {p.name: world(p.name) for p in self.parts}

    # ---- assemble to a CadQuery Assembly in rest pose ----
    def to_cq(self):
        worlds = self._world_transforms()
        asm = cq.Assembly(name=self.name or "model")
        idx = 0
        for part in self.parts:
            wt = worlds.get(part.name, _Tf())
            for vis in part.visuals:
                try:
                    shape = _to_shape(vis.geometry)
                except Exception as exc:
                    raise ValidationError(
                        "part %r visual %r: %s" % (part.name, vis.name, exc)
                    )
                loc = (wt @ _Tf.from_origin(vis.origin)).location()
                rgba = None
                mat = vis.material
                if isinstance(mat, str):
                    mat = next((m for m in self.materials if m.name == mat), None)
                if isinstance(mat, Material) and mat.rgba:
                    rgba = mat.rgba
                kw = {"name": "%s_%d" % (part.name, idx)}
                if rgba:
                    kw["color"] = cq.Color(*rgba)
                asm.add(shape, loc=loc, **kw)
                idx += 1
        return asm

    # convenience aliases a few scripts might call
    def to_assembly(self):
        return self.to_cq()

    def compound(self):
        return self.to_cq().toCompound()

# ===== model =====
import math
import cadquery as cq
def _box(dx: float, dy: float, dz: float, x: float, y: float, z: float) -> cq.Workplane:
    """CadQuery box with center-style placement in model coordinates."""
    return cq.Workplane("XY").box(dx, dy, dz).translate((x, y, z))
def _ring_tube(outer_radius: float, inner_radius: float, length: float) -> cq.Workplane:
    """A centered hollow cylinder, authored along local Z for later placement."""
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length, both=True)
    )
def _housing_mesh() -> cq.Workplane:
    """Curved casino cabinet body with an arched top and open reel window."""
    width = 0.78

    # Main body and a forward belly panel give the front a convex casino-machine
    # stance while still leaving a through-opening for the reel window.
    body = _box(width, 0.42, 1.10, 0.0, 0.0, 0.58)
    body = body.union(_box(0.72, 0.075, 0.74, 0.0, -0.228, 0.55))

    # Rounded top box: an arched Y/Z profile extruded across the machine width.
    top = (
        cq.Workplane("YZ")
        .moveTo(-0.225, 1.08)
        .lineTo(0.225, 1.08)
        .lineTo(0.225, 1.25)
        .threePointArc((0.0, 1.43), (-0.225, 1.25))
        .close()
        .extrude(width, both=True)
    )
    body = body.union(top)

    # A lower plinth and sloped control brow make the front read as one curved
    # shell rather than a plain rectangular box.
    body = body.union(_box(0.82, 0.46, 0.10, 0.0, 0.0, 0.05))
    body = body.union(_box(0.70, 0.080, 0.16, 0.0, -0.270, 0.61))

    # Through aperture for the reel window.  This keeps the reels physically in
    # a real opening instead of intersecting a solid cabinet face.
    body = body.cut(_box(0.62, 0.95, 0.34, 0.0, -0.04, 0.91))
    # Bore clear push-button guide holes through the protruding control brow.
    for x in (-0.115, 0.115):
        body = body.cut(
            cq.Workplane("XZ")
            .circle(0.042)
            .extrude(0.42, both=True)
            .translate((x, -0.255, 0.590))
        )

    # Slightly soften the manufactured cabinet silhouette.  Fillets are kept
    # modest so the window cut and plinth remain robust.
    try:
        body = body.edges("|Z").fillet(0.018)
        body = body.edges(">Z").fillet(0.030)
    except Exception:
        pass
    return body
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="curved_front_casino_machine")

    red = model.material("deep_red_lacquer", rgba=(0.55, 0.02, 0.035, 1.0))
    black = model.material("gloss_black", rgba=(0.005, 0.005, 0.008, 1.0))
    chrome = model.material("brushed_chrome", rgba=(0.72, 0.72, 0.66, 1.0))
    warm = model.material("warm_lamp", rgba=(1.0, 0.76, 0.12, 1.0))
    green = model.material("green_lamp", rgba=(0.0, 0.95, 0.22, 1.0))
    red_lamp = model.material("red_lamp", rgba=(1.0, 0.08, 0.03, 1.0))
    reel_white = model.material("reel_ivory", rgba=(0.94, 0.88, 0.72, 1.0))
    reel_red = model.material("symbol_red", rgba=(0.90, 0.02, 0.02, 1.0))
    reel_blue = model.material("symbol_blue", rgba=(0.05, 0.20, 0.95, 1.0))
    reel_green = model.material("symbol_green", rgba=(0.02, 0.65, 0.10, 1.0))
    steel = model.material("dark_steel", rgba=(0.16, 0.17, 0.18, 1.0))
    brass = model.material("brass_lock", rgba=(0.86, 0.61, 0.18, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_housing_mesh(), "curved_cabinet", tolerance=0.002),
        material=red,
        name="curved_cabinet",
    )

    # Central reel-window surround, glass lip, and marquee lighting.
    body.visual(Box((0.70, 0.030, 0.050)), origin=Origin(xyz=(0.0, -0.310, 1.105)), material=black, name="window_bezel_top")
    body.visual(Box((0.70, 0.030, 0.050)), origin=Origin(xyz=(0.0, -0.310, 0.715)), material=black, name="window_bezel_bottom")
    body.visual(Box((0.050, 0.030, 0.360)), origin=Origin(xyz=(-0.345, -0.310, 0.910)), material=black, name="window_bezel_side_0")
    body.visual(Box((0.050, 0.030, 0.360)), origin=Origin(xyz=(0.345, -0.310, 0.910)), material=black, name="window_bezel_side_1")
    body.visual(Box((0.52, 0.014, 0.095)), origin=Origin(xyz=(0.0, -0.221, 1.245)), material=warm, name="rounded_top_sign")
    for idx, x in enumerate((-0.18, 0.0, 0.18)):
        body.visual(
            Cylinder(radius=0.034, length=0.010),
            origin=Origin(xyz=(x, -0.230, 1.245), rpy=(-math.pi / 2, 0.0, 0.0)),
            material=red_lamp if idx != 1 else green,
            name=f"marquee_lamp_{idx}",
        )

    # Separate cylindrical guides for the two push buttons.  They are hollow
    # mesh tubes so the prismatic button caps can move without a collision
    # waiver.
    guide_mesh = _ring_tube(0.055, 0.038, 0.070)
    for idx, x in enumerate((-0.115, 0.115)):
        body.visual(
            mesh_from_cadquery(guide_mesh, f"button_guide_{idx}", tolerance=0.001),
            origin=Origin(xyz=(x, -0.285, 0.590), rpy=(-math.pi / 2, 0.0, 0.0)),
            material=chrome,
            name=f"button_guide_{idx}",
        )
        body.visual(
            Cylinder(radius=0.020, length=0.012),
            origin=Origin(xyz=(x, -0.328, 0.655), rpy=(-math.pi / 2, 0.0, 0.0)),
            material=warm,
            name=f"button_pilot_{idx}",
        )
        for pad_idx, z_sign in enumerate((-1.0, 1.0)):
            body.visual(
                Box((0.022, 0.050, 0.007)),
                origin=Origin(xyz=(x, -0.285, 0.590 + z_sign * 0.0355)),
                material=black,
                name=f"button_bushing_{idx}_{pad_idx}",
            )

    # Narrow reel separators double as visible bearing supports; each rotating
    # shaft touches these faces without interpenetrating them.
    for idx, x in enumerate((-0.2775, -0.0925, 0.0925, 0.2775)):
        body.visual(
            Box((0.010, 0.055, 0.390)),
            origin=Origin(xyz=(x, -0.180, 0.910)),
            material=black,
            name=f"reel_support_{idx}",
        )

    # Lower cashbox trim frame, mounted to the curved body behind the hinged
    # door.
    body.visual(Box((0.52, 0.022, 0.035)), origin=Origin(xyz=(-0.010, -0.281, 0.5175)), material=black, name="cashbox_frame_top")
    body.visual(Box((0.52, 0.022, 0.035)), origin=Origin(xyz=(-0.010, -0.281, 0.1625)), material=black, name="cashbox_frame_bottom")
    body.visual(Box((0.035, 0.022, 0.370)), origin=Origin(xyz=(-0.280, -0.281, 0.340)), material=black, name="cashbox_frame_hinge")
    body.visual(Box((0.035, 0.022, 0.370)), origin=Origin(xyz=(0.260, -0.281, 0.340)), material=black, name="cashbox_frame_latch")

    # Rotating reels on horizontal shafts behind the front window.
    reel_centers = (-0.185, 0.0, 0.185)
    symbol_mats = (reel_red, reel_blue, reel_green)
    for idx, x in enumerate(reel_centers):
        reel = model.part(f"reel_{idx}")
        reel.visual(
            Cylinder(radius=0.106, length=0.148),
            origin=Origin(rpy=(0.0, math.pi / 2, 0.0)),
            material=reel_white,
            name="reel_drum",
        )
        reel.visual(
            Cylinder(radius=0.017, length=0.175),
            origin=Origin(rpy=(0.0, math.pi / 2, 0.0)),
            material=steel,
            name="shaft",
        )
        for sym, (y, z) in enumerate(((-0.098, -0.040), (-0.106, 0.0), (-0.098, 0.040))):
            reel.visual(
                Box((0.112, 0.006, 0.032)),
                origin=Origin(xyz=(0.0, y, z)),
                material=symbol_mats[(idx + sym) % len(symbol_mats)],
                name=f"symbol_{sym}",
            )
        model.articulation(
            f"body_to_reel_{idx}",
            ArticulationType.CONTINUOUS,
            parent=body,
            child=reel,
            origin=Origin(xyz=(x, -0.180, 0.910)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=2.0, velocity=18.0),
        )

    # Two illuminated front push buttons that translate inward inside the guide
    # barrels.
    for idx, (x, mat) in enumerate(((-0.115, green), (0.115, red_lamp))):
        button = model.part(f"button_{idx}")
        button.visual(
            Cylinder(radius=0.032, length=0.046),
            origin=Origin(xyz=(0.0, -0.021, 0.0), rpy=(-math.pi / 2, 0.0, 0.0)),
            material=mat,
            name="lit_cap",
        )
        button.visual(
            Cylinder(radius=0.022, length=0.018),
            origin=Origin(xyz=(0.0, -0.048, 0.0), rpy=(-math.pi / 2, 0.0, 0.0)),
            material=warm,
            name="front_lens",
        )
        model.articulation(
            f"body_to_button_{idx}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(xyz=(x, -0.285, 0.590)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(effort=15.0, velocity=0.30, lower=0.0, upper=0.026),
        )

    # Lower cashbox door on a vertical side hinge.
    door_w = 0.460
    door_h = 0.320
    cashbox_door = model.part("cashbox_door")
    cashbox_door.visual(
        Box((door_w, 0.024, door_h)),
        origin=Origin(xyz=(door_w / 2, -0.012, door_h / 2)),
        material=steel,
        name="door_panel",
    )
    cashbox_door.visual(
        Cylinder(radius=0.016, length=door_h + 0.035),
        origin=Origin(xyz=(0.0, -0.020, door_h / 2)),
        material=chrome,
        name="hinge_barrel",
    )
    cashbox_door.visual(
        Cylinder(radius=0.026, length=0.018),
        origin=Origin(xyz=(door_w * 0.66, -0.029, door_h * 0.55), rpy=(-math.pi / 2, 0.0, 0.0)),
        material=brass,
        name="round_lock",
    )
    model.articulation(
        "body_to_cashbox_door",
        ArticulationType.REVOLUTE,
        parent=body,
        child=cashbox_door,
        origin=Origin(xyz=(-0.255, -0.292, 0.180)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(effort=8.0, velocity=1.2, lower=0.0, upper=1.35),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
