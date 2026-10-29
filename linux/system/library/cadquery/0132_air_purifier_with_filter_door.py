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
BODY_W = 0.50
BODY_H = 0.80
BODY_D = 0.18
SHELL_T = 0.0045
BEZEL_T = 0.014
DOOR_W = 0.418
DOOR_H = 0.470
DOOR_T = 0.018
DOOR_CENTER_Z = 0.041
DOOR_OPEN_W = DOOR_W + 0.004
DOOR_OPEN_H = DOOR_H + 0.004
DOOR_HINGE_X = BODY_D / 2.0 - 0.002
DOOR_HINGE_Y = DOOR_OPEN_W / 2.0
DOOR_OPEN_ANGLE = 1.32
DRAWER_W = 0.410
DRAWER_H = 0.140
DRAWER_FACE_T = 0.020
DRAWER_CENTER_Z = -0.282
DRAWER_OPEN_W = DRAWER_W + 0.004
DRAWER_OPEN_H = DRAWER_H + 0.002
DRAWER_TRAVEL = 0.100
FLAP_W = 0.120
FLAP_H = 0.038
FLAP_T = 0.010
FLAP_CENTER_Z = 0.313
FLAP_OPEN_W = FLAP_W + 0.002
FLAP_OPEN_H = FLAP_H
FLAP_OPEN_ANGLE = 1.05
def _body_shape() -> cq.Workplane:
    outer_shell = cq.Workplane("XY").box(BODY_D, BODY_W, BODY_H).faces(">X").shell(-SHELL_T)

    bezel = (
        cq.Workplane("XY")
        .box(BEZEL_T, BODY_W - 0.014, BODY_H - 0.014)
        .translate((BODY_D / 2.0 - BEZEL_T / 2.0, 0.0, 0.0))
    )
    bezel = bezel.cut(
        cq.Workplane("XY")
        .box(BEZEL_T + 0.020, DOOR_OPEN_W, DOOR_OPEN_H)
        .translate((BODY_D / 2.0 - BEZEL_T / 2.0, 0.0, DOOR_CENTER_Z))
    )
    bezel = bezel.cut(
        cq.Workplane("XY")
        .box(BEZEL_T + 0.020, DRAWER_OPEN_W, DRAWER_OPEN_H)
        .translate((BODY_D / 2.0 - BEZEL_T / 2.0, 0.0, DRAWER_CENTER_Z))
    )
    bezel = bezel.cut(
        cq.Workplane("XY")
        .box(BEZEL_T + 0.020, FLAP_OPEN_W, FLAP_OPEN_H)
        .translate((BODY_D / 2.0 - BEZEL_T / 2.0, 0.0, FLAP_CENTER_Z))
    )

    divider = (
        cq.Workplane("XY")
        .box(BODY_D - 2.0 * SHELL_T, BODY_W - 2.0 * SHELL_T, 0.008)
        .translate((0.000, 0.000, DRAWER_CENTER_Z + DRAWER_H / 2.0 + 0.014))
    )

    upper_backplate = (
        cq.Workplane("XY")
        .box(0.010, DOOR_W - 0.050, DOOR_H - 0.080)
        .translate((-BODY_D / 2.0 + SHELL_T + 0.005, 0.0, DOOR_CENTER_Z))
    )

    return outer_shell.union(bezel).union(divider).union(upper_backplate)
def _door_shape() -> cq.Workplane:
    panel = cq.Workplane("XY").box(DOOR_T, DOOR_W, DOOR_H).translate((0.000, -DOOR_W / 2.0, 0.0))
    inner_pocket = (
        cq.Workplane("XY")
        .box(DOOR_T - 0.004, DOOR_W - 0.050, DOOR_H - 0.055)
        .translate((-0.002, -DOOR_W / 2.0, -0.004))
    )
    front_recess = (
        cq.Workplane("XY")
        .box(0.003, DOOR_W - 0.090, DOOR_H - 0.120)
        .translate((DOOR_T / 2.0 - 0.0015, -DOOR_W / 2.0 - 0.006, 0.0))
    )
    return panel.cut(inner_pocket).cut(front_recess).translate((0.011, 0.0, 0.0))
def _drawer_shape() -> cq.Workplane:
    tray_outer_w = DRAWER_W - 0.036
    tray_outer_h = DRAWER_H - 0.030
    tray_depth = 0.126
    tray = (
        cq.Workplane("XY")
        .box(tray_depth, tray_outer_w, tray_outer_h)
        .translate((-DRAWER_FACE_T / 2.0 - tray_depth / 2.0, 0.0, -0.0055))
    )
    tray_cavity = (
        cq.Workplane("XY")
        .box(tray_depth - 0.016, tray_outer_w - 0.030, tray_outer_h - 0.018)
        .translate((-DRAWER_FACE_T / 2.0 - tray_depth / 2.0 - 0.002, 0.0, 0.008))
    )
    face = cq.Workplane("XY").box(DRAWER_FACE_T, DRAWER_W, DRAWER_H)
    finger_recess = (
        cq.Workplane("XY")
        .box(0.008, 0.165, 0.024)
        .translate((DRAWER_FACE_T / 2.0 - 0.002, 0.0, 0.024))
    )
    filter_block = (
        cq.Workplane("XY")
        .box(0.055, tray_outer_w - 0.040, tray_outer_h - 0.038)
        .translate((-0.072, 0.0, -0.0095))
    )
    return face.union(tray.cut(tray_cavity)).union(filter_block).cut(finger_recess)
def _flap_shape() -> cq.Workplane:
    flap = cq.Workplane("XY").box(FLAP_T, FLAP_W, FLAP_H).translate((0.000, 0.000, -FLAP_H / 2.0))
    rear_relief = (
        cq.Workplane("XY")
        .box(FLAP_T - 0.003, FLAP_W - 0.020, FLAP_H - 0.010)
        .translate((-0.0015, 0.000, -FLAP_H / 2.0 - 0.001))
    )
    finger_lip = (
        cq.Workplane("XY")
        .box(0.004, 0.060, 0.008)
        .translate((FLAP_T / 2.0 + 0.001, 0.000, -FLAP_H + 0.007))
    )
    return flap.cut(rear_relief).union(finger_lip).translate((0.007, 0.0, 0.0))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="wall_panel_purifier")

    shell_finish = model.material("shell_finish", rgba=(0.93, 0.94, 0.95, 1.0))
    door_finish = model.material("door_finish", rgba=(0.96, 0.97, 0.98, 1.0))
    drawer_finish = model.material("drawer_finish", rgba=(0.87, 0.89, 0.91, 1.0))
    flap_finish = model.material("flap_finish", rgba=(0.82, 0.84, 0.86, 1.0))
    rail_finish = model.material("rail_finish", rgba=(0.22, 0.24, 0.27, 1.0))

    guide_y = DRAWER_W / 2.0 - 0.060
    guide_height = 0.051
    guide_z = -BODY_H / 2.0 + SHELL_T + guide_height / 2.0
    guide_length = 0.120
    runner_x = -0.070
    runner_z = -0.0575

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shape(), "purifier_body"),
        material=shell_finish,
        name="body_shell",
    )
    body.visual(
        Box((guide_length, 0.024, guide_height)),
        origin=Origin(xyz=(-0.004, guide_y, guide_z)),
        material=rail_finish,
        name="guide_0",
    )
    body.visual(
        Box((guide_length, 0.024, guide_height)),
        origin=Origin(xyz=(-0.004, -guide_y, guide_z)),
        material=rail_finish,
        name="guide_1",
    )

    door = model.part("door")
    door.visual(
        mesh_from_cadquery(_door_shape(), "purifier_door"),
        material=door_finish,
        name="door_panel",
    )

    filter_drawer = model.part("filter_drawer")
    filter_drawer.visual(
        mesh_from_cadquery(_drawer_shape(), "purifier_filter_drawer"),
        material=drawer_finish,
        name="drawer_shell",
    )
    filter_drawer.visual(
        Box((0.110, 0.018, 0.010)),
        origin=Origin(xyz=(runner_x, guide_y, runner_z)),
        material=rail_finish,
        name="runner_0",
    )
    filter_drawer.visual(
        Box((0.110, 0.018, 0.010)),
        origin=Origin(xyz=(runner_x, -guide_y, runner_z)),
        material=rail_finish,
        name="runner_1",
    )

    latch_flap = model.part("latch_flap")
    latch_flap.visual(
        mesh_from_cadquery(_flap_shape(), "purifier_latch_flap"),
        material=flap_finish,
        name="flap_panel",
    )

    model.articulation(
        "body_to_door",
        ArticulationType.REVOLUTE,
        parent=body,
        child=door,
        origin=Origin(xyz=(DOOR_HINGE_X, DOOR_HINGE_Y, DOOR_CENTER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=1.5,
            lower=0.0,
            upper=DOOR_OPEN_ANGLE,
        ),
    )
    model.articulation(
        "body_to_filter_drawer",
        ArticulationType.PRISMATIC,
        parent=body,
        child=filter_drawer,
        origin=Origin(xyz=(BODY_D / 2.0 - DRAWER_FACE_T / 2.0, 0.0, DRAWER_CENTER_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=45.0,
            velocity=0.25,
            lower=0.0,
            upper=DRAWER_TRAVEL,
        ),
    )
    model.articulation(
        "body_to_latch_flap",
        ArticulationType.REVOLUTE,
        parent=body,
        child=latch_flap,
        origin=Origin(xyz=(BODY_D / 2.0 - 0.002, 0.0, FLAP_CENTER_Z + FLAP_H / 2.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=4.0,
            velocity=1.8,
            lower=0.0,
            upper=FLAP_OPEN_ANGLE,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
