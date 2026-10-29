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
import cadquery as cq
BACKPLATE_SIZE = (0.024, 0.240, 0.420)
SHOULDER_ORIGIN = (0.205, 0.0, 0.086)
ELBOW_ORIGIN = (0.540, 0.0, -0.032)
WRIST_ORIGIN = (0.745, 0.0, 0.026)
def box_at(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).translate(center)
def xz_prism(points: list[tuple[float, float]], width: float) -> cq.Workplane:
    return cq.Workplane("XZ").polyline(points).close().extrude(width).translate((0.0, width / 2.0, 0.0))
def add_all(base: cq.Workplane, *others: cq.Workplane) -> cq.Workplane:
    result = base
    for other in others:
        result = result.union(other)
    return result
def make_backplate() -> cq.Workplane:
    plate = box_at(BACKPLATE_SIZE, (0.0, 0.0, 0.0))
    center_spine = box_at((0.032, 0.100, 0.300), (0.024, 0.0, 0.0))
    upper_pad = box_at((0.032, 0.160, 0.085), (0.024, 0.0, 0.145))
    lower_pad = box_at((0.032, 0.160, 0.085), (0.024, 0.0, -0.145))
    return add_all(plate, center_spine, upper_pad, lower_pad)
def make_shoulder_bracket() -> cq.Workplane:
    web_profile = [
        (0.072, -0.082),
        (0.072, 0.098),
        (0.108, 0.098),
        (0.146, 0.086),
        (0.176, 0.068),
        (0.176, 0.024),
        (0.154, 0.016),
        (0.122, -0.010),
        (0.102, -0.082),
    ]
    rear_core = box_at((0.072, 0.140, 0.240), (0.072, 0.0, 0.0))
    web = xz_prism(web_profile, 0.060)
    left_cheek = box_at((0.050, 0.018, 0.112), (SHOULDER_ORIGIN[0] - 0.025, 0.029, SHOULDER_ORIGIN[2]))
    right_cheek = box_at((0.050, 0.018, 0.112), (SHOULDER_ORIGIN[0] - 0.025, -0.029, SHOULDER_ORIGIN[2]))
    lower_bridge = box_at((0.036, 0.076, 0.036), (SHOULDER_ORIGIN[0] - 0.043, 0.0, SHOULDER_ORIGIN[2] - 0.046))
    upper_bridge = box_at((0.024, 0.064, 0.024), (SHOULDER_ORIGIN[0] - 0.055, 0.0, SHOULDER_ORIGIN[2] + 0.046))
    return add_all(rear_core, web, left_cheek, right_cheek, lower_bridge, upper_bridge)
def make_first_link() -> cq.Workplane:
    shoulder_tongue = box_at((0.040, 0.040, 0.072), (0.020, 0.0, 0.0))
    beam = xz_prism(
        [
            (0.036, -0.046),
            (0.036, 0.046),
            (0.152, 0.052),
            (0.336, 0.044),
            (0.486, 0.026),
            (0.486, -0.024),
            (0.334, -0.040),
            (0.152, -0.052),
        ],
        0.042,
    )
    top_rib = box_at((0.190, 0.016, 0.018), (0.238, 0.0, 0.030))
    elbow_left = box_at((0.092, 0.018, 0.112), (ELBOW_ORIGIN[0] - 0.046, 0.029, ELBOW_ORIGIN[2] - 0.002))
    elbow_right = box_at((0.092, 0.018, 0.112), (ELBOW_ORIGIN[0] - 0.046, -0.029, ELBOW_ORIGIN[2] - 0.002))
    elbow_bridge = box_at((0.030, 0.070, 0.034), (ELBOW_ORIGIN[0] - 0.072, 0.0, ELBOW_ORIGIN[2] - 0.042))
    return add_all(shoulder_tongue, beam, top_rib, elbow_left, elbow_right, elbow_bridge)
def make_forearm_link() -> cq.Workplane:
    elbow_knuckle = box_at((0.050, 0.040, 0.120), (0.025, 0.0, 0.0))
    elbow_pack = box_at((0.120, 0.070, 0.156), (0.090, 0.0, -0.028))
    beam = xz_prism(
        [
            (0.122, -0.018),
            (0.122, 0.074),
            (0.264, 0.072),
            (0.560, 0.056),
            (0.706, 0.040),
            (0.706, 0.008),
            (0.564, -0.010),
            (0.258, 0.000),
        ],
        0.042,
    )
    top_rib = box_at((0.240, 0.016, 0.018), (0.366, 0.0, 0.046))
    wrist_left = box_at((0.080, 0.018, 0.100), (WRIST_ORIGIN[0] - 0.040, 0.029, WRIST_ORIGIN[2]))
    wrist_right = box_at((0.080, 0.018, 0.100), (WRIST_ORIGIN[0] - 0.040, -0.029, WRIST_ORIGIN[2]))
    wrist_bridge = box_at((0.028, 0.070, 0.032), (WRIST_ORIGIN[0] - 0.070, 0.0, WRIST_ORIGIN[2] - 0.038))
    return add_all(elbow_knuckle, elbow_pack, beam, top_rib, wrist_left, wrist_right, wrist_bridge)
def make_end_plate() -> cq.Workplane:
    wrist_tongue = box_at((0.040, 0.040, 0.092), (0.020, 0.0, 0.0))
    adapter = box_at((0.100, 0.080, 0.100), (0.068, 0.0, 0.0))
    plate = box_at((0.018, 0.180, 0.180), (0.118, 0.0, 0.0))
    hole_pattern = (
        cq.Workplane("YZ")
        .pushPoints([(-0.055, -0.055), (-0.055, 0.055), (0.055, -0.055), (0.055, 0.055)])
        .circle(0.010)
        .extrude(0.040)
        .translate((0.096, 0.0, 0.0))
    )
    return add_all(wrist_tongue, adapter, plate).cut(hole_pattern)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="wall_transfer_arm")

    graphite = model.material("graphite", color=(0.18, 0.19, 0.21))
    bracket_gray = model.material("bracket_gray", color=(0.30, 0.32, 0.35))
    arm_orange = model.material("arm_orange", color=(0.76, 0.50, 0.16))
    endplate_dark = model.material("endplate_dark", color=(0.24, 0.25, 0.27))

    backplate = model.part("backplate")
    backplate.visual(
        mesh_from_cadquery(make_backplate(), "backplate"),
        material=graphite,
        name="backplate_shell",
    )
    backplate.inertial = Inertial.from_geometry(
        Box((0.040, 0.240, 0.420)),
        mass=18.0,
        origin=Origin(xyz=(0.014, 0.0, 0.0)),
    )

    shoulder_bracket = model.part("shoulder_bracket")
    shoulder_bracket.visual(
        mesh_from_cadquery(make_shoulder_bracket(), "shoulder_bracket"),
        material=bracket_gray,
        name="shoulder_bracket_shell",
    )
    shoulder_bracket.inertial = Inertial.from_geometry(
        Box((0.235, 0.140, 0.235)),
        mass=9.0,
        origin=Origin(xyz=(0.135, 0.0, 0.020)),
    )

    first_link = model.part("first_link")
    first_link.visual(
        mesh_from_cadquery(make_first_link(), "first_link"),
        material=arm_orange,
        name="first_link_shell",
    )
    first_link.inertial = Inertial.from_geometry(
        Box((0.600, 0.120, 0.125)),
        mass=10.0,
        origin=Origin(xyz=(0.300, 0.0, -0.006)),
    )

    forearm_link = model.part("forearm_link")
    forearm_link.visual(
        mesh_from_cadquery(make_forearm_link(), "forearm_link"),
        material=arm_orange,
        name="forearm_link_shell",
    )
    forearm_link.inertial = Inertial.from_geometry(
        Box((0.820, 0.120, 0.170)),
        mass=13.0,
        origin=Origin(xyz=(0.360, 0.0, -0.005)),
    )

    end_plate = model.part("end_plate")
    end_plate.visual(
        mesh_from_cadquery(make_end_plate(), "end_plate"),
        material=endplate_dark,
        name="end_plate_shell",
    )
    end_plate.inertial = Inertial.from_geometry(
        Box((0.130, 0.180, 0.180)),
        mass=4.0,
        origin=Origin(xyz=(0.085, 0.0, 0.0)),
    )

    model.articulation(
        "backplate_to_shoulder_bracket",
        ArticulationType.FIXED,
        parent=backplate,
        child=shoulder_bracket,
        origin=Origin(),
    )
    model.articulation(
        "shoulder_joint",
        ArticulationType.REVOLUTE,
        parent=shoulder_bracket,
        child=first_link,
        origin=Origin(xyz=SHOULDER_ORIGIN),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=180.0, velocity=1.2, lower=-1.0, upper=0.75),
    )
    model.articulation(
        "elbow_joint",
        ArticulationType.REVOLUTE,
        parent=first_link,
        child=forearm_link,
        origin=Origin(xyz=ELBOW_ORIGIN),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=160.0, velocity=1.4, lower=-1.35, upper=1.1),
    )
    model.articulation(
        "wrist_joint",
        ArticulationType.REVOLUTE,
        parent=forearm_link,
        child=end_plate,
        origin=Origin(xyz=WRIST_ORIGIN),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=70.0, velocity=1.8, lower=-1.3, upper=1.3),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
