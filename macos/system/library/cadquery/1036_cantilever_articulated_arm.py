# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cantilever_articulated_arm, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cantilever_articulated_arm

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

class Inertia:
    def __init__(self, ixx=0.0, ixy=0.0, ixz=0.0, iyy=0.0, iyz=0.0, izz=0.0):
        self.ixx, self.ixy, self.ixz = ixx, ixy, ixz
        self.iyy, self.iyz, self.izz = iyy, iyz, izz

class Inertial:
    def __init__(self, mass=1.0, inertia=None, origin=None):
        self.mass = float(mass)
        self.inertia = inertia
        self.origin = origin or Origin()

    @staticmethod
    def from_geometry(geometry, mass, *, origin=None):
        return Inertial(mass=mass, inertia=Inertia(), origin=origin or Origin())

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
from math import isclose
import cadquery as cq
BACKPLATE_THICKNESS = 0.014
BACKPLATE_WIDTH = 0.180
BACKPLATE_HEIGHT = 0.280
SHOULDER_GAP = 0.040
SHOULDER_CHEEK_THICKNESS = 0.022
SHOULDER_CHEEK_HEIGHT = 0.132
FIRST_LINK_LENGTH = 0.330
ELBOW_GAP = 0.038
ELBOW_CHEEK_THICKNESS = 0.018
FOREARM_LENGTH = 0.260
WRIST_GAP = 0.022
WRIST_CHEEK_THICKNESS = 0.014
END_PLATE_SIZE = 0.090
END_PLATE_THICKNESS = 0.012
SHOULDER_BARREL_RADIUS = 0.018
ELBOW_BARREL_RADIUS = 0.024
WRIST_BARREL_RADIUS = 0.012
def _union_all(*shapes: cq.Workplane) -> cq.Workplane:
    result = shapes[0]
    for shape in shapes[1:]:
        result = result.union(shape)
    return result
def _y_cylinder(
    radius: float,
    length: float,
    *,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
) -> cq.Workplane:
    return (
        cq.Workplane("XZ")
        .circle(radius)
        .extrude(length)
        .translate((x, y - length / 2.0, z))
    )
def _x_cylinder(
    radius: float,
    length: float,
    *,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
) -> cq.Workplane:
    return (
        cq.Workplane("YZ")
        .circle(radius)
        .extrude(length)
        .translate((x - length / 2.0, y, z))
    )
def _wall_mount_shape() -> cq.Workplane:
    backplate = (
        cq.Workplane("XY")
        .box(BACKPLATE_THICKNESS, BACKPLATE_WIDTH, BACKPLATE_HEIGHT)
        .translate((-0.102, 0.0, 0.0))
        .edges("|X")
        .fillet(0.008)
    )
    rear_mass = (
        cq.Workplane("YZ")
        .rect(0.154, 0.224)
        .workplane(offset=0.050)
        .rect(0.122, 0.186)
        .loft(combine=True)
        .translate((-0.092, 0.0, 0.0))
    )
    shoulder_wedge = (
        cq.Workplane("YZ")
        .rect(0.110, 0.158)
        .workplane(offset=0.032)
        .rect(0.080, 0.120)
        .loft(combine=True)
        .translate((-0.038, 0.0, 0.0))
    )

    cheek_offset = SHOULDER_GAP / 2.0 + SHOULDER_CHEEK_THICKNESS / 2.0
    shoulder_cheek_left = (
        cq.Workplane("XY")
        .box(0.040, SHOULDER_CHEEK_THICKNESS, SHOULDER_CHEEK_HEIGHT)
        .translate((-0.020, cheek_offset, 0.0))
    )
    shoulder_cheek_right = (
        cq.Workplane("XY")
        .box(0.040, SHOULDER_CHEEK_THICKNESS, SHOULDER_CHEEK_HEIGHT)
        .translate((-0.020, -cheek_offset, 0.0))
    )
    top_bridge = cq.Workplane("XY").box(0.062, 0.118, 0.018).translate((-0.032, 0.0, 0.058))
    bottom_bridge = cq.Workplane("XY").box(0.062, 0.118, 0.018).translate((-0.032, 0.0, -0.058))
    side_web_left = cq.Workplane("XY").box(0.050, 0.012, 0.050).translate((-0.024, 0.028, 0.0))
    side_web_right = cq.Workplane("XY").box(0.050, 0.012, 0.050).translate((-0.024, -0.028, 0.0))

    cap_y = SHOULDER_GAP / 2.0 + SHOULDER_CHEEK_THICKNESS + 0.003
    shoulder_caps = _union_all(
        _y_cylinder(0.030, 0.006, x=-0.030, y=cap_y, z=0.0),
        _y_cylinder(0.030, 0.006, x=-0.030, y=-cap_y, z=0.0),
    )
    mount_bolts = (
        cq.Workplane("YZ")
        .pushPoints([(-0.075, -0.098), (0.075, -0.098), (-0.075, 0.098), (0.075, 0.098)])
        .circle(0.008)
        .extrude(0.006)
        .translate((-0.095, 0.0, 0.0))
    )
    cap_bolts = _union_all(
        cq.Workplane("XZ")
        .pushPoints([(-0.044, -0.032), (-0.022, -0.032), (-0.044, 0.032), (-0.022, 0.032)])
        .circle(0.0038)
        .extrude(0.005)
        .translate((0.0, SHOULDER_GAP / 2.0 + SHOULDER_CHEEK_THICKNESS, 0.0)),
        cq.Workplane("XZ")
        .pushPoints([(-0.044, -0.032), (-0.022, -0.032), (-0.044, 0.032), (-0.022, 0.032)])
        .circle(0.0038)
        .extrude(0.005)
        .translate((0.0, -(SHOULDER_GAP / 2.0 + SHOULDER_CHEEK_THICKNESS + 0.005), 0.0)),
    )

    return _union_all(
        backplate,
        rear_mass,
        shoulder_wedge,
        shoulder_cheek_left,
        shoulder_cheek_right,
        top_bridge,
        bottom_bridge,
        side_web_left,
        side_web_right,
        shoulder_caps,
        mount_bolts,
        cap_bolts,
    ).clean()
def _first_link_shape() -> cq.Workplane:
    shoulder_knuckle = _union_all(
        _y_cylinder(SHOULDER_BARREL_RADIUS, SHOULDER_GAP, x=SHOULDER_BARREL_RADIUS, y=0.0, z=0.0),
        cq.Workplane("XY").box(0.028, 0.022, 0.036).translate((0.028, 0.0, 0.0)),
    )
    beam = (
        cq.Workplane("YZ")
        .rect(0.060, 0.086)
        .workplane(offset=0.210)
        .rect(0.042, 0.064)
        .loft(combine=True)
        .translate((0.055, 0.0, 0.0))
    )
    rib_left = cq.Workplane("XY").box(0.188, 0.005, 0.030).translate((0.166, 0.024, 0.0))
    rib_right = cq.Workplane("XY").box(0.188, 0.005, 0.030).translate((0.166, -0.024, 0.0))

    elbow_center_x = FIRST_LINK_LENGTH - 0.024
    elbow_bridge = cq.Workplane("XY").box(0.040, 0.034, 0.050).translate((FIRST_LINK_LENGTH - 0.050, 0.0, 0.0))
    elbow_top = cq.Workplane("XY").box(0.046, 0.060, 0.014).translate((FIRST_LINK_LENGTH - 0.042, 0.0, 0.048))
    elbow_bottom = cq.Workplane("XY").box(0.046, 0.060, 0.014).translate((FIRST_LINK_LENGTH - 0.042, 0.0, -0.048))
    elbow_cheek_offset = ELBOW_GAP / 2.0 + ELBOW_CHEEK_THICKNESS / 2.0
    elbow_cheek_left = cq.Workplane("XY").box(0.048, ELBOW_CHEEK_THICKNESS, 0.110).translate((elbow_center_x, elbow_cheek_offset, 0.0))
    elbow_cheek_right = cq.Workplane("XY").box(0.048, ELBOW_CHEEK_THICKNESS, 0.110).translate((elbow_center_x, -elbow_cheek_offset, 0.0))
    elbow_caps = _union_all(
        _y_cylinder(0.028, 0.006, x=FIRST_LINK_LENGTH - 0.028, y=ELBOW_GAP / 2.0 + ELBOW_CHEEK_THICKNESS + 0.003, z=0.0),
        _y_cylinder(0.028, 0.006, x=FIRST_LINK_LENGTH - 0.028, y=-(ELBOW_GAP / 2.0 + ELBOW_CHEEK_THICKNESS + 0.003), z=0.0),
    )
    elbow_cap_bolts = _union_all(
        cq.Workplane("XZ")
        .pushPoints(
            [
                (FIRST_LINK_LENGTH - 0.046, -0.034),
                (FIRST_LINK_LENGTH - 0.022, -0.034),
                (FIRST_LINK_LENGTH - 0.046, 0.034),
                (FIRST_LINK_LENGTH - 0.022, 0.034),
            ]
        )
        .circle(0.0035)
        .extrude(0.005)
        .translate((0.0, ELBOW_GAP / 2.0 + ELBOW_CHEEK_THICKNESS, 0.0)),
        cq.Workplane("XZ")
        .pushPoints(
            [
                (FIRST_LINK_LENGTH - 0.046, -0.034),
                (FIRST_LINK_LENGTH - 0.022, -0.034),
                (FIRST_LINK_LENGTH - 0.046, 0.034),
                (FIRST_LINK_LENGTH - 0.022, 0.034),
            ]
        )
        .circle(0.0035)
        .extrude(0.005)
        .translate((0.0, -(ELBOW_GAP / 2.0 + ELBOW_CHEEK_THICKNESS + 0.005), 0.0)),
    )

    return _union_all(
        shoulder_knuckle,
        beam,
        rib_left,
        rib_right,
        elbow_bridge,
        elbow_top,
        elbow_bottom,
        elbow_cheek_left,
        elbow_cheek_right,
        elbow_caps,
        elbow_cap_bolts,
    ).clean()
def _forearm_shape() -> cq.Workplane:
    elbow_knuckle = _union_all(
        _y_cylinder(ELBOW_BARREL_RADIUS, ELBOW_GAP, x=ELBOW_BARREL_RADIUS, y=0.0, z=0.0),
        cq.Workplane("XY").box(0.028, 0.020, 0.048).translate((0.030, 0.0, 0.0)),
        cq.Workplane("XY").box(0.020, 0.018, 0.016).translate((0.018, 0.0, -0.030)),
    )
    beam = (
        cq.Workplane("YZ")
        .rect(0.046, 0.066)
        .workplane(offset=0.172)
        .rect(0.032, 0.048)
        .loft(combine=True)
        .translate((0.052, 0.0, 0.0))
    )
    rib_left = cq.Workplane("XY").box(0.120, 0.004, 0.022).translate((0.138, 0.018, 0.0))
    rib_right = cq.Workplane("XY").box(0.120, 0.004, 0.022).translate((0.138, -0.018, 0.0))

    wrist_center_x = FOREARM_LENGTH - 0.020
    wrist_bridge = cq.Workplane("XY").box(0.030, 0.024, 0.032).translate((FOREARM_LENGTH - 0.046, 0.0, 0.0))
    wrist_top = cq.Workplane("XY").box(0.036, 0.044, 0.012).translate((FOREARM_LENGTH - 0.034, 0.0, 0.032))
    wrist_bottom = cq.Workplane("XY").box(0.036, 0.044, 0.012).translate((FOREARM_LENGTH - 0.034, 0.0, -0.032))
    wrist_cheek_offset = WRIST_GAP / 2.0 + WRIST_CHEEK_THICKNESS / 2.0
    wrist_cheek_left = cq.Workplane("XY").box(0.040, WRIST_CHEEK_THICKNESS, 0.066).translate((wrist_center_x, wrist_cheek_offset, 0.0))
    wrist_cheek_right = cq.Workplane("XY").box(0.040, WRIST_CHEEK_THICKNESS, 0.066).translate((wrist_center_x, -wrist_cheek_offset, 0.0))
    wrist_caps = _union_all(
        _y_cylinder(0.020, 0.005, x=FOREARM_LENGTH - 0.020, y=WRIST_GAP / 2.0 + WRIST_CHEEK_THICKNESS + 0.0025, z=0.0),
        _y_cylinder(0.020, 0.005, x=FOREARM_LENGTH - 0.020, y=-(WRIST_GAP / 2.0 + WRIST_CHEEK_THICKNESS + 0.0025), z=0.0),
    )

    return _union_all(
        elbow_knuckle,
        beam,
        rib_left,
        rib_right,
        wrist_bridge,
        wrist_top,
        wrist_bottom,
        wrist_cheek_left,
        wrist_cheek_right,
        wrist_caps,
    ).clean()
def _end_plate_shape() -> cq.Workplane:
    wrist_hub = _union_all(
        _y_cylinder(WRIST_BARREL_RADIUS, WRIST_GAP, x=WRIST_BARREL_RADIUS, y=0.0, z=0.0),
        cq.Workplane("XY").box(0.014, 0.012, 0.022).translate((0.014, 0.0, 0.0)),
    )
    standoff = (
        cq.Workplane("YZ")
        .rect(0.018, 0.028)
        .workplane(offset=0.050)
        .rect(0.040, 0.064)
        .loft(combine=True)
        .translate((0.032, 0.0, 0.0))
    )
    gusset_top = cq.Workplane("XY").box(0.030, 0.012, 0.014).translate((0.034, 0.0, 0.022))
    gusset_bottom = cq.Workplane("XY").box(0.030, 0.012, 0.014).translate((0.034, 0.0, -0.022))
    plate_body = (
        cq.Workplane("XY")
        .box(END_PLATE_THICKNESS, END_PLATE_SIZE, END_PLATE_SIZE)
        .translate((0.084, 0.0, 0.0))
        .edges("|X")
        .fillet(0.004)
    )
    rim = cq.Workplane("XY").box(0.006, 0.102, 0.102).translate((0.078, 0.0, 0.0))
    plate = _union_all(plate_body, rim)
    recess = cq.Workplane("XY").box(0.006, 0.060, 0.060).translate((0.087, 0.0, 0.0))
    center_hole = _x_cylinder(0.012, 0.036, x=0.084, y=0.0, z=0.0)
    corner_holes = (
        cq.Workplane("YZ")
        .pushPoints([(-0.028, -0.028), (0.028, -0.028), (-0.028, 0.028), (0.028, 0.028)])
        .circle(0.0042)
        .extrude(0.036)
        .translate((0.066, 0.0, 0.0))
    )
    tool_plate = plate.cut(recess).cut(center_hole).cut(corner_holes)

    return _union_all(wrist_hub, standoff, gusset_top, gusset_bottom, tool_plate).clean()
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="wall_mounted_transfer_arm")

    model.material("powder_steel", rgba=(0.21, 0.23, 0.26, 1.0))
    model.material("machine_gray", rgba=(0.47, 0.50, 0.54, 1.0))
    model.material("cast_aluminum", rgba=(0.63, 0.66, 0.70, 1.0))
    model.material("light_alloy", rgba=(0.76, 0.79, 0.82, 1.0))

    wall_mount = model.part("wall_mount")
    wall_mount.visual(
        mesh_from_cadquery(_wall_mount_shape(), "wall_mount"),
        material="powder_steel",
        name="wall_mount_shell",
    )
    wall_mount.inertial = Inertial.from_geometry(
        Box((0.160, 0.180, 0.300)),
        mass=18.0,
        origin=Origin(xyz=(-0.040, 0.0, 0.0)),
    )

    first_link = model.part("first_link")
    first_link.visual(
        mesh_from_cadquery(_first_link_shape(), "first_link"),
        material="machine_gray",
        name="first_link_shell",
    )
    first_link.inertial = Inertial.from_geometry(
        Box((FIRST_LINK_LENGTH + 0.050, 0.080, 0.120)),
        mass=9.0,
        origin=Origin(xyz=(FIRST_LINK_LENGTH / 2.0, 0.0, 0.0)),
    )

    forearm = model.part("forearm")
    forearm.visual(
        mesh_from_cadquery(_forearm_shape(), "forearm"),
        material="cast_aluminum",
        name="forearm_shell",
    )
    forearm.inertial = Inertial.from_geometry(
        Box((FOREARM_LENGTH + 0.050, 0.060, 0.120)),
        mass=5.8,
        origin=Origin(xyz=(FOREARM_LENGTH / 2.0, 0.0, 0.0)),
    )

    end_plate = model.part("end_plate")
    end_plate.visual(
        mesh_from_cadquery(_end_plate_shape(), "end_plate"),
        material="light_alloy",
        name="end_plate_shell",
    )
    end_plate.inertial = Inertial.from_geometry(
        Box((0.110, 0.102, 0.102)),
        mass=2.2,
        origin=Origin(xyz=(0.062, 0.0, 0.0)),
    )

    model.articulation(
        "shoulder_pitch",
        ArticulationType.REVOLUTE,
        parent=wall_mount,
        child=first_link,
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.30, upper=0.32, effort=140.0, velocity=1.2),
    )
    model.articulation(
        "elbow_pitch",
        ArticulationType.REVOLUTE,
        parent=first_link,
        child=forearm,
        origin=Origin(xyz=(FIRST_LINK_LENGTH, 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.70, upper=0.05, effort=95.0, velocity=1.5),
    )
    model.articulation(
        "wrist_pitch",
        ArticulationType.REVOLUTE,
        parent=forearm,
        child=end_plate,
        origin=Origin(xyz=(FOREARM_LENGTH, 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.40, upper=0.35, effort=36.0, velocity=2.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
