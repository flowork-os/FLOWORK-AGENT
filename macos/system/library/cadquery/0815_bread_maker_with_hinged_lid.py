# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bread_maker_with_hinged_lid, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bread_maker_with_hinged_lid

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
BODY_W = 0.390
BODY_D = 0.320
BODY_H = 0.205
CHAMBER_Y = 0.040
CHAMBER_OPEN_W = 0.202
CHAMBER_OPEN_D = 0.148
CHAMBER_DEPTH = 0.158
HINGE_Y = 0.145
HINGE_Z = 0.216
PAN_BODY_W = 0.187
PAN_BODY_D = 0.127
PAN_H = 0.148
PAN_WALL = 0.0022
PAN_BOTTOM = 0.0040
PAN_FLANGE_W = 0.204
PAN_FLANGE_D = 0.144
PAN_FLANGE_T = 0.0020
LID_W = 0.276
LID_D = 0.205
LID_H = 0.032
LID_BOTTOM_Z = -0.003
LID_TUBE_OUTER = 0.0066
LID_TUBE_INNER = 0.0048
LID_TUBE_L = 0.180
WINDOW_W = 0.155
WINDOW_D = 0.102
WINDOW_Y = -0.108
VENT_W = 0.056
VENT_D = 0.028
VENT_H = 0.010
VENT_HINGE_Y = -0.030
VENT_HINGE_Z = 0.029
VENT_SLOT_Y = -0.044
PANEL_TOP_Z = BODY_H + 0.005
DIAL_Y = -0.108
DIAL_OUTER_R = 0.036
DIAL_INNER_R = 0.022
BUTTON_CAP_W = 0.028
BUTTON_CAP_D = 0.018
BUTTON_CAP_H = 0.005
BUTTON_STEM_W = 0.013
BUTTON_STEM_D = 0.008
BUTTON_STEM_H = 0.010
BUTTON_PROUD = 0.0015
BUTTON_LAYOUT = (
    (-0.053, -0.082),
    (0.053, -0.082),
    (-0.067, -0.112),
    (0.067, -0.112),
    (0.000, -0.150),
)
def _rounded_box(
    width: float,
    depth: float,
    height: float,
    *,
    corner: float,
    top_fillet: float,
):
    solid = cq.Workplane("XY").box(width, depth, height, centered=(True, True, False))
    solid = solid.edges("|Z").fillet(corner)
    solid = solid.edges(">Z").fillet(top_fillet)
    return solid
def _body_shell_shape():
    shell = _rounded_box(
        BODY_W,
        BODY_D,
        BODY_H,
        corner=0.028,
        top_fillet=0.012,
    )
    chamber_cut = (
        cq.Workplane("XY")
        .box(
            CHAMBER_OPEN_W,
            CHAMBER_OPEN_D,
            CHAMBER_DEPTH + 0.006,
            centered=(True, True, False),
        )
        .translate((0.0, CHAMBER_Y, BODY_H - CHAMBER_DEPTH))
    )
    shell = shell.cut(chamber_cut)

    control_rise = _rounded_box(
        0.244,
        0.092,
        0.006,
        corner=0.010,
        top_fillet=0.003,
    ).translate((0.0, -0.106, BODY_H - 0.001))
    shell = shell.union(control_rise)

    for offset_x in (-0.122, 0.122):
        rear_mount = _rounded_box(
            0.028,
            0.018,
            0.022,
            corner=0.004,
            top_fillet=0.003,
        ).translate((offset_x, HINGE_Y, BODY_H - 0.001))
        shell = shell.union(rear_mount)

    for button_x, button_y in BUTTON_LAYOUT:
        button_cut = (
            cq.Workplane("XY")
            .box(
                BUTTON_STEM_W + 0.002,
                BUTTON_STEM_D + 0.002,
                0.018,
                centered=(True, True, False),
            )
            .translate((button_x, button_y, PANEL_TOP_Z - 0.016))
        )
        shell = shell.cut(button_cut)

    return shell
def _pan_shape():
    bucket = (
        cq.Workplane("XY")
        .box(PAN_BODY_W, PAN_BODY_D, PAN_H, centered=(True, True, False))
        .translate((0.0, 0.0, -PAN_H))
    )
    bucket = bucket.edges("|Z").fillet(0.010)
    inner_cut = (
        cq.Workplane("XY")
        .box(
            PAN_BODY_W - (2.0 * PAN_WALL),
            PAN_BODY_D - (2.0 * PAN_WALL),
            PAN_H,
            centered=(True, True, False),
        )
        .translate((0.0, 0.0, -PAN_H + PAN_BOTTOM))
    )
    bucket = bucket.cut(inner_cut)

    flange = cq.Workplane("XY").box(
        PAN_FLANGE_W,
        PAN_FLANGE_D,
        PAN_FLANGE_T,
        centered=(True, True, False),
    )
    flange_cut = (
        cq.Workplane("XY")
        .box(
            PAN_BODY_W - (2.0 * PAN_WALL),
            PAN_BODY_D - (2.0 * PAN_WALL),
            PAN_FLANGE_T + 0.003,
            centered=(True, True, False),
        )
        .translate((0.0, 0.0, -0.001))
    )
    flange = flange.cut(flange_cut)
    return bucket.union(flange)
def _lid_shell_shape():
    lid = _rounded_box(
        LID_W,
        LID_D,
        LID_H,
        corner=0.014,
        top_fillet=0.008,
    ).translate((0.0, -LID_D / 2.0, LID_BOTTOM_Z))

    cavity_cut = (
        cq.Workplane("XY")
        .box(
            LID_W - 0.022,
            LID_D - 0.028,
            LID_H,
            centered=(True, True, False),
        )
        .translate((0.0, -(LID_D / 2.0) - 0.004, LID_BOTTOM_Z - 0.001))
    )
    lid = lid.cut(cavity_cut)

    window_cut = (
        cq.Workplane("XY")
        .box(WINDOW_W, WINDOW_D, 0.024, centered=(True, True, False))
        .translate((0.0, WINDOW_Y, 0.012))
    )
    lid = lid.cut(window_cut)

    for offset_x in (-0.015, 0.0, 0.015):
        slot_cut = (
            cq.Workplane("XY")
            .box(0.006, 0.018, 0.008, centered=(True, True, False))
            .translate((offset_x, VENT_SLOT_Y, 0.021))
        )
        lid = lid.cut(slot_cut)

    for offset_x in (-0.122, 0.122):
        rear_relief = (
            cq.Workplane("XY")
            .box(0.038, 0.030, 0.026, centered=(True, True, False))
            .translate((offset_x, -0.006, -0.004))
        )
        lid = lid.cut(rear_relief)

    hinge_tube = (
        cq.Workplane("YZ")
        .circle(LID_TUBE_OUTER)
        .circle(LID_TUBE_INNER)
        .extrude(LID_TUBE_L / 2.0, both=True)
    )
    return lid.union(hinge_tube)
def _vent_cap_shape():
    cap = _rounded_box(
        VENT_W,
        VENT_D,
        VENT_H,
        corner=0.004,
        top_fillet=0.0025,
    ).translate((0.0, -VENT_D / 2.0, 0.0))
    return cap
def _dial_ring_shape():
    ring = (
        cq.Workplane("XY")
        .circle(DIAL_OUTER_R)
        .circle(DIAL_INNER_R)
        .extrude(0.008)
    )
    ring = ring.edges(">Z").fillet(0.0015)
    return ring
def _button_shape():
    cap = _rounded_box(
        BUTTON_CAP_W,
        BUTTON_CAP_D,
        BUTTON_CAP_H,
        corner=0.003,
        top_fillet=0.0015,
    ).translate((0.0, 0.0, BUTTON_PROUD))
    stem = (
        cq.Workplane("XY")
        .box(
            BUTTON_STEM_W,
            BUTTON_STEM_D,
            BUTTON_STEM_H + BUTTON_PROUD + 0.0004,
            centered=(True, True, False),
        )
        .translate((0.0, 0.0, -BUTTON_STEM_H))
    )
    return cap.union(stem)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="premium_bread_maker")

    body_plastic = model.material("body_plastic", rgba=(0.20, 0.22, 0.24, 1.0))
    lid_plastic = model.material("lid_plastic", rgba=(0.18, 0.19, 0.21, 1.0))
    dark_trim = model.material("dark_trim", rgba=(0.10, 0.11, 0.12, 1.0))
    glass = model.material("glass", rgba=(0.55, 0.70, 0.78, 0.32))
    brushed_metal = model.material("brushed_metal", rgba=(0.72, 0.74, 0.77, 1.0))
    steel = model.material("steel", rgba=(0.62, 0.64, 0.67, 1.0))
    button_satin = model.material("button_satin", rgba=(0.77, 0.79, 0.82, 1.0))
    dial_graphite = model.material("dial_graphite", rgba=(0.14, 0.15, 0.16, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shell_shape(), "bread_maker_body_shell"),
        material=body_plastic,
        name="housing_shell",
    )
    body.visual(
        Cylinder(radius=0.010, length=0.014),
        origin=Origin(xyz=(0.0, CHAMBER_Y, BODY_H - PAN_H + PAN_BOTTOM - 0.007)),
        material=steel,
        name="spindle_boss",
    )

    body.visual(
        mesh_from_cadquery(_pan_shape(), "bread_maker_pan"),
        origin=Origin(xyz=(0.0, CHAMBER_Y, BODY_H)),
        material=brushed_metal,
        name="pan_shell",
    )
    body.visual(
        Cylinder(radius=0.019, length=0.004),
        origin=Origin(xyz=(0.0, DIAL_Y, PANEL_TOP_Z + 0.002)),
        material=dark_trim,
        name="dial_hub",
    )

    lid = model.part("lid")
    lid.visual(
        mesh_from_cadquery(_lid_shell_shape(), "bread_maker_lid_shell"),
        material=lid_plastic,
        name="lid_shell",
    )
    lid.visual(
        Box((0.171, 0.118, 0.004)),
        origin=Origin(xyz=(0.0, WINDOW_Y, 0.0110)),
        material=glass,
        name="window_glass",
    )

    vent_cap = model.part("vent_cap")
    vent_cap.visual(
        mesh_from_cadquery(_vent_cap_shape(), "bread_maker_vent_cap"),
        material=dark_trim,
        name="vent_cap_shell",
    )

    spindle = model.part("spindle")
    spindle.visual(
        Cylinder(radius=0.005, length=0.020),
        origin=Origin(xyz=(0.0, 0.0, 0.010)),
        material=steel,
        name="shaft",
    )
    spindle.visual(
        Cylinder(radius=0.0075, length=0.004),
        origin=Origin(xyz=(0.0, 0.0, 0.002)),
        material=steel,
        name="collar",
    )
    spindle.visual(
        Box((0.011, 0.004, 0.006)),
        origin=Origin(xyz=(0.0065, 0.0, 0.014)),
        material=steel,
        name="drive_tab",
    )

    dial_mesh = mesh_from_cadquery(_dial_ring_shape(), "bread_maker_dial_ring")
    dial = model.part("dial")
    dial.visual(
        dial_mesh,
        material=dial_graphite,
        name="dial_ring",
    )
    dial.visual(
        Box((0.006, 0.010, 0.003)),
        origin=Origin(xyz=(0.0, DIAL_OUTER_R - 0.004, 0.0095)),
        material=button_satin,
        name="dial_marker",
    )

    button_mesh = mesh_from_cadquery(_button_shape(), "bread_maker_button")
    for button_index, _ in enumerate(BUTTON_LAYOUT):
        button_part = model.part(f"button_{button_index}")
        button_part.visual(
            button_mesh,
            material=button_satin,
            name="button_shell",
        )

    model.articulation(
        "body_to_lid",
        ArticulationType.REVOLUTE,
        parent=body,
        child=lid,
        origin=Origin(xyz=(0.0, HINGE_Y, HINGE_Z)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=2.0, lower=0.0, upper=1.32),
    )
    model.articulation(
        "lid_to_vent_cap",
        ArticulationType.REVOLUTE,
        parent=lid,
        child=vent_cap,
        origin=Origin(xyz=(0.0, VENT_HINGE_Y, VENT_HINGE_Z)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=2.0, lower=0.0, upper=0.62),
    )
    model.articulation(
        "pan_to_spindle",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=spindle,
        origin=Origin(xyz=(0.0, CHAMBER_Y, BODY_H - PAN_H + PAN_BOTTOM)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=1.0, velocity=8.0),
    )
    model.articulation(
        "body_to_dial",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=dial,
        origin=Origin(xyz=(0.0, DIAL_Y, PANEL_TOP_Z + 0.001)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.5, velocity=6.0),
    )
    for button_index, (button_x, button_y) in enumerate(BUTTON_LAYOUT):
        model.articulation(
            f"body_to_button_{button_index}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=f"button_{button_index}",
            origin=Origin(xyz=(button_x, button_y, PANEL_TOP_Z)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=8.0,
                velocity=0.08,
                lower=0.0,
                upper=0.0015,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
