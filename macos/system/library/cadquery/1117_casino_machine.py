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
CABINET_WIDTH = 0.385
CABINET_HEIGHT = 0.575
SHELF_Z = 0.214
SCREEN_TILT_DEG = -7.5
SCREEN_TILT_RAD = math.radians(SCREEN_TILT_DEG)
BUTTON_CENTERS = (-0.112, -0.056, 0.0, 0.056, 0.112)
def _build_cabinet_shape() -> cq.Workplane:
    profile = [
        (-0.146, 0.000),
        (0.122, 0.000),
        (0.108, CABINET_HEIGHT),
        (0.006, CABINET_HEIGHT),
        (-0.054, 0.522),
        (-0.090, 0.243),
        (-0.160, SHELF_Z),
        (-0.160, 0.176),
        (-0.145, 0.156),
        (-0.146, 0.000),
    ]
    inner_profile = [
        (-0.130, 0.014),
        (0.104, 0.014),
        (0.097, 0.552),
        (0.010, 0.552),
        (-0.040, 0.509),
        (-0.071, 0.252),
        (-0.110, 0.232),
        (-0.128, 0.205),
        (-0.130, 0.014),
    ]

    outer = cq.Workplane("YZ").polyline(profile).close().extrude(CABINET_WIDTH / 2.0, both=True)
    inner = cq.Workplane("YZ").polyline(inner_profile).close().extrude((CABINET_WIDTH - 0.030) / 2.0, both=True)
    body = outer.cut(inner)

    screen_cutter = (
        cq.Workplane("XY")
        .box(0.278, 0.140, 0.210)
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), SCREEN_TILT_DEG)
        .translate((0.0, -0.072, 0.392))
    )
    tray_cutter = cq.Workplane("XY").box(0.212, 0.132, 0.078).translate((0.0, -0.100, 0.106))
    for button_x in BUTTON_CENTERS:
        pocket_cutter = cq.Workplane("XY").box(0.052, 0.024, 0.020).translate((button_x, -0.138, SHELF_Z + 0.012))
        button_cutter = cq.Workplane("XY").box(0.020, 0.014, 0.050).translate((button_x, -0.138, SHELF_Z + 0.010))
        body = body.cut(pocket_cutter)
        body = body.cut(button_cutter)

    return body.cut(screen_cutter).cut(tray_cutter)
def _build_tray_flap_shape() -> cq.Workplane:
    door = cq.Workplane("XY").box(0.182, 0.009, 0.050)
    lip = cq.Workplane("XY").box(0.134, 0.010, 0.010).translate((0.0, -0.001, 0.020))
    hinge_barrel = (
        cq.Workplane("XY")
        .cylinder(0.170, 0.005)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90.0)
        .translate((0.0, 0.004, -0.025))
    )
    hinge_leaf = cq.Workplane("XY").box(0.168, 0.012, 0.004).translate((0.0, 0.004, -0.023))
    return door.union(lip).union(hinge_barrel).union(hinge_leaf)
def _build_tray_hinge_support_shape() -> cq.Workplane:
    bar = cq.Workplane("XY").box(0.188, 0.014, 0.008)
    left_tab = cq.Workplane("XY").box(0.010, 0.014, 0.150).translate((-0.094, 0.0, 0.071))
    right_tab = cq.Workplane("XY").box(0.010, 0.014, 0.150).translate((0.094, 0.0, 0.071))
    return bar.union(left_tab).union(right_tab)
def _build_control_panel_shape() -> cq.Workplane:
    panel = cq.Workplane("XY").box(0.314, 0.076, 0.010)
    for button_x in BUTTON_CENTERS:
        pocket = cq.Workplane("XY").box(0.050, 0.024, 0.004).translate((button_x, 0.0, 0.003))
        hole = cq.Workplane("XY").box(0.020, 0.014, 0.016).translate((button_x, 0.0, 0.0))
        panel = panel.cut(pocket).cut(hole)
    return panel
def _build_button_cap_shape() -> cq.Workplane:
    return cq.Workplane("XY").box(0.046, 0.020, 0.008).edges("|Z").fillet(0.0025)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bartop_video_poker_terminal")

    cabinet_color = model.material("cabinet_color", rgba=(0.16, 0.16, 0.18, 1.0))
    trim_color = model.material("trim_color", rgba=(0.08, 0.08, 0.09, 1.0))
    screen_color = model.material("screen_color", rgba=(0.10, 0.22, 0.19, 0.92))
    button_color = model.material("button_color", rgba=(0.76, 0.12, 0.11, 1.0))

    cabinet = model.part("cabinet")
    cabinet.visual(
        mesh_from_cadquery(_build_cabinet_shape(), "terminal_cabinet"),
        material=cabinet_color,
        name="shell",
    )
    cabinet.visual(
        mesh_from_cadquery(_build_control_panel_shape(), "video_poker_button_panel"),
        origin=Origin(xyz=(0.0, -0.138, SHELF_Z + 0.005)),
        material=trim_color,
        name="control_shelf",
    )
    cabinet.visual(
        mesh_from_cadquery(_build_tray_hinge_support_shape(), "tray_hinge_support"),
        origin=Origin(xyz=(0.0, -0.115, 0.079)),
        material=trim_color,
        name="tray_hinge_support",
    )

    cabinet.visual(
        Box((0.260, 0.020, 0.190)),
        origin=Origin(xyz=(0.0, -0.071, 0.392), rpy=(SCREEN_TILT_RAD, 0.0, 0.0)),
        material=screen_color,
        name="screen_panel",
    )
    cabinet.visual(
        Box((0.284, 0.024, 0.214)),
        origin=Origin(xyz=(0.0, -0.061, 0.392), rpy=(SCREEN_TILT_RAD, 0.0, 0.0)),
        material=trim_color,
        name="screen_mount",
    )

    tray_flap = model.part("tray_flap")
    tray_flap.visual(
        mesh_from_cadquery(_build_tray_flap_shape(), "cash_tray_flap"),
        origin=Origin(xyz=(0.0, -0.003, 0.025)),
        material=trim_color,
        name="door",
    )
    model.articulation(
        "cabinet_to_tray_flap",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=tray_flap,
        origin=Origin(xyz=(0.0, -0.129, 0.079)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=10.0, velocity=2.5, lower=0.0, upper=1.25),
    )

    button_cap = mesh_from_cadquery(_build_button_cap_shape(), "video_poker_button_cap")
    for index, button_x in enumerate(BUTTON_CENTERS):
        button = model.part(f"play_button_{index}")
        button.visual(
            button_cap,
            origin=Origin(xyz=(0.0, 0.0, 0.004)),
            material=button_color,
            name="cap",
        )
        button.visual(
            Box((0.016, 0.010, 0.012)),
            origin=Origin(xyz=(0.0, 0.0, -0.006)),
            material=button_color,
            name="stem",
        )
        button.visual(
            Box((0.030, 0.016, 0.003)),
            origin=Origin(xyz=(0.0, 0.0, -0.0115)),
            material=button_color,
            name="retainer",
        )
        model.articulation(
            f"cabinet_to_play_button_{index}",
            ArticulationType.PRISMATIC,
            parent=cabinet,
            child=button,
            origin=Origin(xyz=(button_x, -0.138, SHELF_Z + 0.010)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(effort=4.0, velocity=0.08, lower=0.0, upper=0.0035),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
