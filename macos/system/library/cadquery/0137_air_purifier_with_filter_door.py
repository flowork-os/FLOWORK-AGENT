# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_purifier_with_filter_door, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_purifier_with_filter_door

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
import cadquery as cq
BODY_W = 0.255
BODY_D = 0.225
BODY_H = 0.740
WALL = 0.0035
OPENING_W = 0.182
OPENING_H = 0.548
OPENING_CENTER_Z = 0.382
REAR_FACE_Y = -BODY_D / 2.0 + WALL * 0.5
DOOR_W = 0.178
DOOR_H = 0.544
DOOR_T = 0.014
DOOR_HINGE_R = 0.006
DOOR_HINGE_LEN = 0.118
DOOR_SWING = 2.05
FILTER_W = 0.166
FILTER_D = 0.108
FILTER_H = 0.518
FILTER_TRAVEL = 0.078
FILTER_ORIGIN_Y = REAR_FACE_Y + 0.01525
BUTTON_BANK_Y = 0.042
BUTTON_BANK_W = 0.102
BUTTON_BANK_D = 0.038
BUTTON_TRAY_D = 0.003
BUTTON_STEM_SLOT_W = 0.084
BUTTON_STEM_SLOT_D = 0.018
BUTTON_TRAVEL = 0.0015
BUTTON_CAP_R = 0.009
BUTTON_CAP_H = 0.0032
BUTTON_STEM_R = 0.0037
BUTTON_STEM_H = 0.006
BUTTON_XS = (-0.033, -0.011, 0.011, 0.033)
FRONT_PANEL_W = 0.160
FRONT_PANEL_H = 0.470
FRONT_PANEL_Z = 0.390
FRONT_PANEL_RECESS = 0.004
TOP_VENT_Y = -0.018
TOP_VENT_XS = (-0.050, -0.032, -0.014, 0.004, 0.022, 0.040, 0.058)
TOP_VENT_W = 0.010
TOP_VENT_D = 0.052
def _housing_shell() -> object:
    body = (
        cq.Workplane("XY")
        .box(BODY_W, BODY_D, BODY_H)
        .edges("|Z")
        .fillet(0.032)
        .translate((0.0, 0.0, BODY_H / 2.0))
        .faces("<Z")
        .shell(-WALL)
    )

    rear_opening = (
        cq.Workplane("XY")
        .box(OPENING_W, WALL * 6.0, OPENING_H)
        .translate((0.0, -BODY_D / 2.0, OPENING_CENTER_Z))
    )
    body = body.cut(rear_opening)

    front_recess = (
        cq.Workplane("XY")
        .box(FRONT_PANEL_W, FRONT_PANEL_RECESS, FRONT_PANEL_H)
        .translate((0.0, BODY_D / 2.0 - FRONT_PANEL_RECESS / 2.0, FRONT_PANEL_Z))
    )
    body = body.cut(front_recess)

    button_tray = (
        cq.Workplane("XY")
        .box(BUTTON_BANK_W, BUTTON_BANK_D, BUTTON_TRAY_D)
        .translate((0.0, BUTTON_BANK_Y, BODY_H - BUTTON_TRAY_D / 2.0))
    )
    body = body.cut(button_tray)

    stem_slot = (
        cq.Workplane("XY")
        .box(BUTTON_STEM_SLOT_W, BUTTON_STEM_SLOT_D, 0.010)
        .translate((0.0, BUTTON_BANK_Y, BODY_H - BUTTON_TRAY_D - 0.005))
    )
    body = body.cut(stem_slot)

    vent_cutters = (
        cq.Workplane("XY")
        .pushPoints([(x, TOP_VENT_Y) for x in TOP_VENT_XS])
        .rect(TOP_VENT_W, TOP_VENT_D)
        .extrude(0.010)
        .translate((0.0, 0.0, BODY_H - 0.006))
    )
    body = body.cut(vent_cutters)
    return body
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="tower_purifier")

    shell_white = model.material("shell_white", rgba=(0.92, 0.93, 0.95, 1.0))
    trim_charcoal = model.material("trim_charcoal", rgba=(0.14, 0.15, 0.17, 1.0))
    filter_frame = model.material("filter_frame", rgba=(0.18, 0.19, 0.21, 1.0))
    filter_media = model.material("filter_media", rgba=(0.36, 0.46, 0.52, 1.0))
    tab_orange = model.material("tab_orange", rgba=(0.91, 0.47, 0.16, 1.0))
    button_black = model.material("button_black", rgba=(0.08, 0.09, 0.10, 1.0))

    housing = model.part("housing")
    housing.visual(
        mesh_from_cadquery(_housing_shell(), "purifier_housing"),
        material=shell_white,
        name="shell",
    )
    housing.visual(
        Box((BODY_W + 0.010, BODY_D + 0.010, 0.026)),
        origin=Origin(xyz=(0.0, 0.0, 0.013)),
        material=trim_charcoal,
        name="base_ring",
    )

    rear_door = model.part("rear_door")
    rear_door.visual(
        Box((DOOR_W, DOOR_T, DOOR_H)),
        origin=Origin(xyz=(-DOOR_W / 2.0, 0.0, 0.0)),
        material=shell_white,
        name="door_leaf",
    )
    rear_door.visual(
        Box((DOOR_W - 0.022, 0.004, DOOR_H - 0.070)),
        origin=Origin(xyz=(-DOOR_W / 2.0 + 0.004, -0.004, 0.0)),
        material=trim_charcoal,
        name="door_inset",
    )
    for index, z in enumerate((-0.195, 0.0, 0.195)):
        rear_door.visual(
            Cylinder(radius=DOOR_HINGE_R, length=DOOR_HINGE_LEN),
            origin=Origin(xyz=(0.0, 0.0, z)),
            material=trim_charcoal,
            name=f"hinge_knuckle_{index}",
        )

    filter_part = model.part("filter")
    filter_part.visual(
        Box((FILTER_W, FILTER_D, FILTER_H)),
        origin=Origin(xyz=(0.0, FILTER_D / 2.0, 0.0)),
        material=filter_frame,
        name="cartridge",
    )
    filter_part.visual(
        Box((FILTER_W - 0.020, FILTER_D - 0.018, FILTER_H - 0.040)),
        origin=Origin(xyz=(0.0, FILTER_D / 2.0 + 0.003, 0.0)),
        material=filter_media,
        name="media",
    )
    filter_part.visual(
        Box((0.022, 0.014, 0.030)),
        origin=Origin(xyz=(0.0, -0.004, FILTER_H / 2.0 - 0.030)),
        material=tab_orange,
        name="tab_stem",
    )
    filter_part.visual(
        Box((0.050, 0.008, 0.016)),
        origin=Origin(xyz=(0.0, -0.013, FILTER_H / 2.0 - 0.024)),
        material=tab_orange,
        name="tab_pull",
    )

    for index, x in enumerate(BUTTON_XS):
        button = model.part(f"button_{index}")
        button.visual(
            Cylinder(radius=BUTTON_CAP_R, length=BUTTON_CAP_H),
            origin=Origin(xyz=(0.0, 0.0, BUTTON_CAP_H / 2.0)),
            material=button_black,
            name="button_cap",
        )
        button.visual(
            Cylinder(radius=BUTTON_STEM_R, length=BUTTON_STEM_H),
            origin=Origin(xyz=(0.0, 0.0, -BUTTON_STEM_H / 2.0)),
            material=button_black,
            name="button_stem",
        )
        model.articulation(
            f"housing_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=housing,
            child=button,
            origin=Origin(xyz=(x, BUTTON_BANK_Y, BODY_H - BUTTON_TRAY_D)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=8.0,
                velocity=0.05,
                lower=0.0,
                upper=BUTTON_TRAVEL,
            ),
        )

    model.articulation(
        "housing_to_rear_door",
        ArticulationType.REVOLUTE,
        parent=housing,
        child=rear_door,
        origin=Origin(
            xyz=(OPENING_W / 2.0, -BODY_D / 2.0 - DOOR_T / 2.0, OPENING_CENTER_Z)
        ),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=1.2,
            lower=0.0,
            upper=DOOR_SWING,
        ),
    )
    model.articulation(
        "housing_to_filter",
        ArticulationType.PRISMATIC,
        parent=housing,
        child=filter_part,
        origin=Origin(xyz=(0.0, FILTER_ORIGIN_Y, OPENING_CENTER_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=30.0,
            velocity=0.15,
            lower=0.0,
            upper=FILTER_TRAVEL,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
