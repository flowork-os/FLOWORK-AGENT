# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camcorder_with_flipout_screen, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camcorder_with_flipout_screen

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
BODY_L = 0.112
BODY_W = 0.074
BODY_H = 0.085
BODY_FRONT_X = BODY_L / 2.0
BODY_SIDE_Y = BODY_W / 2.0
BODY_TOP_Z = BODY_H / 2.0
OBJECTIVE_Y = -0.008
OBJECTIVE_Z = 0.006
OBJECTIVE_RADIUS = 0.024
OBJECTIVE_LENGTH = 0.040
DOOR_W = 0.078
DOOR_H = 0.060
DOOR_T = 0.0035
DOOR_HINGE_X = -0.022
DOOR_CENTER_Z = 0.002
DOOR_HINGE_Y = BODY_SIDE_Y + 0.003247
SCREEN_PIVOT_X = 0.008
SCREEN_PIVOT_Y = -DOOR_T / 2.0
SCREEN_W = 0.053
SCREEN_H = 0.042
SCREEN_T = 0.0032
DIAL_X = -0.030
DIAL_Y = -0.018
DIAL_Z = BODY_TOP_Z + 0.0042
def _body_shape() -> cq.Workplane:
    main_shell = cq.Workplane("XY").box(BODY_L, BODY_W, BODY_H).edges().fillet(0.0045)

    rear_hump = (
        cq.Workplane("XY")
        .transformed(offset=(-0.032, -0.004, 0.014))
        .box(0.040, 0.056, 0.030)
        .edges("|Z")
        .fillet(0.004)
    )

    lens_collar = (
        cq.Workplane("XY")
        .transformed(offset=(BODY_FRONT_X - 0.006, OBJECTIVE_Y, OBJECTIVE_Z), rotate=(0.0, 90.0, 0.0))
        .circle(0.030)
        .extrude(0.010)
    )

    dial_pedestal = (
        cq.Workplane("XY")
        .transformed(offset=(DIAL_X, DIAL_Y, BODY_TOP_Z), rotate=(0.0, 0.0, 0.0))
        .circle(0.013)
        .extrude(0.0042)
    )

    hinge_post = (
        cq.Workplane("XY")
        .transformed(offset=(DOOR_HINGE_X, DOOR_HINGE_Y - 0.004299, DOOR_CENTER_Z - 0.026))
        .circle(0.0011)
        .extrude(0.052)
    )

    hinge_bridge = (
        cq.Workplane("XY")
        .transformed(offset=(DOOR_HINGE_X - 0.006, DOOR_HINGE_Y - 0.00445, DOOR_CENTER_Z))
        .box(0.012, 0.0018, 0.018)
        .edges("|Y")
        .fillet(0.0008)
    )

    mic_bump = (
        cq.Workplane("XY")
        .transformed(offset=(0.006, -0.006, BODY_TOP_Z - 0.002))
        .box(0.024, 0.012, 0.005)
        .edges("|Y")
        .fillet(0.002)
    )

    side_recess = (
        cq.Workplane("XY")
        .transformed(offset=(DOOR_HINGE_X + DOOR_W / 2.0, BODY_SIDE_Y - 0.0048, DOOR_CENTER_Z))
        .box(DOOR_W + 0.008, 0.012, DOOR_H + 0.004)
        .edges("|Y")
        .fillet(0.005)
    )

    body = main_shell.union(rear_hump).cut(side_recess)
    body = body.union(lens_collar).union(dial_pedestal).union(hinge_post).union(hinge_bridge).union(mic_bump)
    return body
def _strap_pad_shape() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .transformed(offset=(0.012, -BODY_SIDE_Y - 0.0016, -0.002))
        .box(0.076, 0.0032, 0.044)
        .edges("|Y")
        .fillet(0.003)
    )
def _objective_shape() -> cq.Workplane:
    barrel = (
        cq.Workplane("XY")
        .transformed(rotate=(0.0, 90.0, 0.0))
        .circle(OBJECTIVE_RADIUS)
        .extrude(OBJECTIVE_LENGTH)
    )
    front_ring = (
        cq.Workplane("XY")
        .transformed(offset=(OBJECTIVE_LENGTH - 0.014, 0.0, 0.0), rotate=(0.0, 90.0, 0.0))
        .circle(0.027)
        .extrude(0.014)
    )
    focus_ring = (
        cq.Workplane("XY")
        .transformed(offset=(0.010, 0.0, 0.0), rotate=(0.0, 90.0, 0.0))
        .circle(0.0255)
        .extrude(0.010)
    )
    return barrel.union(front_ring).union(focus_ring)
def _door_shape() -> cq.Workplane:
    panel_start_x = 0.0030
    panel_width = DOOR_W - panel_start_x
    panel = (
        cq.Workplane("XY")
        .transformed(offset=(panel_start_x + panel_width / 2.0, 0.0, 0.0))
        .box(panel_width, DOOR_T, DOOR_H)
        .edges("|Y")
        .fillet(0.0045)
    )

    finger_notch = (
        cq.Workplane("XY")
        .transformed(offset=(DOOR_W - 0.0015, 0.0, -0.010))
        .circle(0.007)
        .extrude(0.020)
    )

    hinge_spine = (
        cq.Workplane("XY")
        .transformed(offset=(0.0, 0.0, -0.030))
        .circle(0.0032)
        .extrude(0.060)
    )

    return panel.cut(finger_notch).union(hinge_spine)
def _screen_shape() -> cq.Workplane:
    panel = (
        cq.Workplane("XY")
        .transformed(offset=(0.031, -0.0022, 0.0))
        .box(SCREEN_W, SCREEN_T, SCREEN_H)
        .edges("|Y")
        .fillet(0.003)
    )

    swivel_hub = (
        cq.Workplane("XY")
        .transformed(offset=(0.0, -0.0024, -0.023))
        .circle(0.0024)
        .extrude(0.046)
    )

    arm = (
        cq.Workplane("XY")
        .transformed(offset=(0.012, -0.0021, 0.0))
        .box(0.018, 0.0024, 0.022)
        .edges("|Y")
        .fillet(0.0012)
    )

    stem = (
        cq.Workplane("XY")
        .transformed(offset=(0.0055, -0.0022, 0.0))
        .box(0.011, 0.0018, 0.018)
        .edges("|Y")
        .fillet(0.0008)
    )

    contact_pad = (
        cq.Workplane("XY")
        .transformed(offset=(0.0018, -0.0001, 0.0))
        .box(0.0045, 0.0002, 0.018)
    )

    return swivel_hub.union(stem).union(arm).union(panel).union(contact_pad)
def _dial_shape() -> cq.Workplane:
    dial = cq.Workplane("XY").circle(0.0105).extrude(0.0062)
    top_cap = (
        cq.Workplane("XY")
        .transformed(offset=(0.0, 0.0, 0.0062))
        .circle(0.0087)
        .extrude(0.0014)
    )
    thumb_tab = (
        cq.Workplane("XY")
        .transformed(offset=(0.0092, 0.0022, 0.0069))
        .box(0.008, 0.0044, 0.0026)
        .edges("|Z")
        .fillet(0.001)
    )
    return dial.union(top_cap).union(thumb_tab)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="family_camcorder")

    shell_finish = model.material("shell_finish", rgba=(0.23, 0.24, 0.26, 1.0))
    trim_finish = model.material("trim_finish", rgba=(0.11, 0.12, 0.13, 1.0))
    strap_finish = model.material("strap_finish", rgba=(0.14, 0.14, 0.15, 1.0))
    dial_finish = model.material("dial_finish", rgba=(0.17, 0.18, 0.19, 1.0))
    body = model.part("body")
    body.visual(mesh_from_cadquery(_body_shape(), "body_shell"), material=shell_finish, name="shell")
    body.visual(mesh_from_cadquery(_strap_pad_shape(), "hand_strap"), material=strap_finish, name="strap")

    objective = model.part("objective")
    objective.visual(mesh_from_cadquery(_objective_shape(), "objective_barrel"), material=trim_finish, name="barrel")

    screen_door = model.part("screen_door")
    screen_door.visual(mesh_from_cadquery(_door_shape(), "screen_door"), material=shell_finish, name="door")

    screen_panel = model.part("screen_panel")
    screen_panel.visual(mesh_from_cadquery(_screen_shape(), "screen_panel"), material=trim_finish, name="panel")

    mode_dial = model.part("mode_dial")
    mode_dial.visual(mesh_from_cadquery(_dial_shape(), "mode_dial"), material=dial_finish, name="dial")

    model.articulation(
        "body_to_objective",
        ArticulationType.FIXED,
        parent=body,
        child=objective,
        origin=Origin(xyz=(BODY_FRONT_X + 0.0006, OBJECTIVE_Y, OBJECTIVE_Z)),
    )

    model.articulation(
        "body_to_screen_door",
        ArticulationType.REVOLUTE,
        parent=body,
        child=screen_door,
        origin=Origin(xyz=(DOOR_HINGE_X, DOOR_HINGE_Y, DOOR_CENTER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=2.15, effort=2.0, velocity=1.8),
    )

    model.articulation(
        "door_to_screen",
        ArticulationType.REVOLUTE,
        parent=screen_door,
        child=screen_panel,
        origin=Origin(xyz=(SCREEN_PIVOT_X, SCREEN_PIVOT_Y, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=3.05, effort=1.0, velocity=2.2),
    )

    model.articulation(
        "body_to_mode_dial",
        ArticulationType.REVOLUTE,
        parent=body,
        child=mode_dial,
        origin=Origin(xyz=(DIAL_X, DIAL_Y, DIAL_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=-1.85, upper=1.40, effort=0.8, velocity=3.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
