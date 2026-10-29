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
FRAME_FOOT_LENGTH = 0.26
FRAME_FOOT_HEIGHT = 0.03
FRAME_POST_HEIGHT = 0.62
FRAME_POST_X = -0.08
FRAME_POST_SPAN_Y = 0.24
FRAME_MID_Z = 0.23
SHOULDER_X = 0.08
SHOULDER_Y = 0.184
SHOULDER_Z = 0.56
UPPER_LINK_LENGTH = 0.78
FORELINK_LENGTH = 0.46
LUG_WIDTH_Y = 0.018
EAR_WIDTH_Y = 0.014
EAR_OFFSET_Y = (LUG_WIDTH_Y + EAR_WIDTH_Y) / 2.0
PIVOT_HOLE_RADIUS = 0.010
def _box(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    sx, sy, sz = size
    return cq.Workplane("XY").box(sx, sy, sz).translate(center)
def _cylinder_y(radius: float, length: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XZ").circle(radius).extrude(length / 2.0, both=True).translate(center)
def _center_lug(
    start_x: float,
    end_x: float,
    *,
    width_y: float = LUG_WIDTH_Y,
    height_z: float = 0.064,
    center_z: float = 0.0,
) -> cq.Workplane:
    return _box((end_x - start_x, width_y, height_z), ((start_x + end_x) / 2.0, 0.0, center_z))
def _fork_ears(
    start_x: float,
    end_x: float,
    *,
    width_y: float = EAR_WIDTH_Y,
    offset_y: float = EAR_OFFSET_Y,
    height_z: float = 0.072,
    center_z: float = 0.0,
) -> cq.Workplane:
    lower = _box((end_x - start_x, width_y, height_z), ((start_x + end_x) / 2.0, -offset_y, center_z))
    upper = _box((end_x - start_x, width_y, height_z), ((start_x + end_x) / 2.0, offset_y, center_z))
    return lower.union(upper)
def _pivot_hole(x_center: float, *, y_center: float = 0.0, z_center: float = 0.0, length: float = 0.080) -> cq.Workplane:
    return _cylinder_y(PIVOT_HOLE_RADIUS, length, (x_center, y_center, z_center))
def _rear_frame_shape() -> cq.Workplane:
    left_y = -FRAME_POST_SPAN_Y / 2.0
    right_y = FRAME_POST_SPAN_Y / 2.0
    shoulder_bracket_y = SHOULDER_Y - 0.016
    shoulder_support_front = SHOULDER_X

    frame = _box((FRAME_FOOT_LENGTH, 0.07, FRAME_FOOT_HEIGHT), (-0.05, left_y, 0.015))
    frame = frame.union(_box((FRAME_FOOT_LENGTH, 0.07, FRAME_FOOT_HEIGHT), (-0.05, right_y, 0.015)))
    frame = frame.union(_box((0.10, FRAME_POST_SPAN_Y + 0.07, 0.05), (-0.15, 0.0, 0.03)))
    frame = frame.union(_box((0.12, FRAME_POST_SPAN_Y - 0.02, 0.04), (-0.01, 0.0, 0.02)))
    frame = frame.union(_box((0.06, 0.06, FRAME_POST_HEIGHT), (FRAME_POST_X, left_y, FRAME_POST_HEIGHT / 2.0)))
    frame = frame.union(_box((0.06, 0.06, FRAME_POST_HEIGHT), (FRAME_POST_X, right_y, FRAME_POST_HEIGHT / 2.0)))
    frame = frame.union(_box((0.06, FRAME_POST_SPAN_Y + 0.06, 0.06), (FRAME_POST_X, 0.0, 0.63)))
    frame = frame.union(_box((0.04, FRAME_POST_SPAN_Y + 0.04, 0.04), (FRAME_POST_X, 0.0, FRAME_MID_Z)))
    frame = frame.union(_box((0.12, 0.05, 0.20), (shoulder_support_front - 0.12, 0.138, 0.44)))
    frame = frame.union(_box((0.10, 0.040, 0.13), (shoulder_support_front - 0.09, 0.140, SHOULDER_Z)))
    frame = frame.union(_box((0.05, 0.032, 0.090), (shoulder_support_front - 0.025, SHOULDER_Y - 0.026, SHOULDER_Z)))
    frame = frame.union(_box((0.050, EAR_WIDTH_Y, 0.078), (shoulder_support_front - 0.025, shoulder_bracket_y, SHOULDER_Z)))

    return frame
def _upper_link_shape() -> cq.Workplane:
    link = _center_lug(0.000, 0.095, height_z=0.068)
    link = link.union(_box((0.52, LUG_WIDTH_Y, 0.086), (0.355, 0.0, 0.0)))
    link = link.union(_box((0.16, 0.048, 0.074), (0.620, 0.0, 0.0)))
    link = link.union(_box((0.06, 0.048, 0.070), (0.730, 0.0, 0.0)))
    link = link.union(_fork_ears(0.700, UPPER_LINK_LENGTH, height_z=0.074))
    link = link.cut(_pivot_hole(0.0, length=LUG_WIDTH_Y + 0.004))
    link = link.cut(_pivot_hole(UPPER_LINK_LENGTH, y_center=-EAR_OFFSET_Y, length=EAR_WIDTH_Y + 0.004))
    link = link.cut(_pivot_hole(UPPER_LINK_LENGTH, y_center=EAR_OFFSET_Y, length=EAR_WIDTH_Y + 0.004))
    return link
def _forelink_shape() -> cq.Workplane:
    link = _center_lug(0.000, 0.090, height_z=0.064)
    link = link.union(_box((0.28, LUG_WIDTH_Y, 0.074), (0.220, 0.0, 0.0)))
    link = link.union(_box((0.10, 0.044, 0.068), (0.340, 0.0, 0.0)))
    link = link.union(_box((0.06, 0.044, 0.064), (0.415, 0.0, 0.0)))
    link = link.union(_fork_ears(0.400, FORELINK_LENGTH, height_z=0.070))
    link = link.cut(_pivot_hole(0.0, length=LUG_WIDTH_Y + 0.004))
    link = link.cut(_pivot_hole(FORELINK_LENGTH, y_center=-EAR_OFFSET_Y, length=EAR_WIDTH_Y + 0.004))
    link = link.cut(_pivot_hole(FORELINK_LENGTH, y_center=EAR_OFFSET_Y, length=EAR_WIDTH_Y + 0.004))
    return link
def _wrist_plate_shape() -> cq.Workplane:
    plate = _center_lug(0.000, 0.070, height_z=0.054)
    plate = plate.union(_box((0.11, 0.014, 0.090), (0.105, 0.0, 0.0)))
    plate = plate.union(_box((0.050, 0.026, 0.032), (0.080, 0.0, -0.020)))
    plate = plate.cut(_pivot_hole(0.0, length=LUG_WIDTH_Y + 0.004))

    return plate
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bridge_supported_cantilever_arm")

    model.material("powder_steel", rgba=(0.22, 0.24, 0.27, 1.0))
    model.material("aluminum", rgba=(0.73, 0.75, 0.78, 1.0))
    model.material("anodized_dark", rgba=(0.24, 0.26, 0.29, 1.0))

    rear_frame = model.part("rear_frame")
    rear_frame.visual(
        mesh_from_cadquery(_rear_frame_shape(), "rear_frame"),
        material="powder_steel",
        name="rear_frame_shell",
    )

    upper_link = model.part("upper_link")
    upper_link.visual(
        mesh_from_cadquery(_upper_link_shape(), "upper_link"),
        material="aluminum",
        name="upper_link_shell",
    )

    forelink = model.part("forelink")
    forelink.visual(
        mesh_from_cadquery(_forelink_shape(), "forelink"),
        material="aluminum",
        name="forelink_shell",
    )

    wrist_plate = model.part("wrist_plate")
    wrist_plate.visual(
        mesh_from_cadquery(_wrist_plate_shape(), "wrist_plate"),
        material="anodized_dark",
        name="wrist_plate_shell",
    )

    model.articulation(
        "shoulder_joint",
        ArticulationType.REVOLUTE,
        parent=rear_frame,
        child=upper_link,
        origin=Origin(xyz=(SHOULDER_X, SHOULDER_Y, SHOULDER_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.45, upper=1.15, effort=65.0, velocity=1.5),
    )
    model.articulation(
        "elbow_joint",
        ArticulationType.REVOLUTE,
        parent=upper_link,
        child=forelink,
        origin=Origin(xyz=(UPPER_LINK_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.55, effort=45.0, velocity=1.8),
    )
    model.articulation(
        "wrist_joint",
        ArticulationType.REVOLUTE,
        parent=forelink,
        child=wrist_plate,
        origin=Origin(xyz=(FORELINK_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-1.0, upper=1.05, effort=20.0, velocity=2.4),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
