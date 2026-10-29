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
BASE_FOOT_X = 0.160
BASE_FOOT_Y = 0.120
BASE_FOOT_T = 0.014
COLUMN_X = 0.060
COLUMN_Y = 0.056
COLUMN_Z = 0.088
SHOULDER_X = 0.094
SHOULDER_Z = BASE_FOOT_T + COLUMN_Z + 0.002
LINK1_LEN = 0.170
LINK2_LEN = 0.145
BASE_YOKE_GAP = 0.028
BASE_CHEEK_T = 0.010
ELBOW_GAP = 0.024
ELBOW_CHEEK_T = 0.009
WRIST_GAP = 0.022
WRIST_CHEEK_T = 0.008
def _box(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    sx, sy, sz = size
    cx, cy, cz = center
    return cq.Workplane("XY").box(sx, sy, sz).translate((cx, cy, cz))
def _base_shape() -> cq.Workplane:
    foot = (
        cq.Workplane("XY")
        .box(BASE_FOOT_X, BASE_FOOT_Y, BASE_FOOT_T)
        .faces(">Z")
        .workplane()
        .pushPoints([(-0.048, -0.036), (-0.048, 0.036), (0.048, -0.036), (0.048, 0.036)])
        .hole(0.010)
        .edges("|Z")
        .fillet(0.008)
        .translate((0.0, 0.0, BASE_FOOT_T / 2.0))
    )

    column = _box((COLUMN_X, COLUMN_Y, COLUMN_Z), (-0.036, 0.0, BASE_FOOT_T + COLUMN_Z / 2.0))
    arm_stem = _box((0.118, 0.034, 0.018), (0.016, 0.0, SHOULDER_Z - 0.031))
    shoulder_pad = _box((0.032, 0.040, 0.018), (0.074, 0.0, SHOULDER_Z - 0.011))
    top_cap = _box((0.018, 0.040, 0.010), (0.085, 0.0, SHOULDER_Z + 0.015))

    gusset = (
        cq.Workplane("XZ")
        .polyline(
            [
                (-0.050, BASE_FOOT_T + 0.010),
                (-0.022, BASE_FOOT_T + 0.010),
                (0.042, SHOULDER_Z - 0.040),
                (0.012, SHOULDER_Z - 0.040),
            ]
        )
        .close()
        .extrude(0.046)
        .translate((0.0, -0.023, 0.0))
    )

    base = foot.union(column).union(arm_stem).union(shoulder_pad).union(top_cap).union(gusset)

    cheek_y = BASE_YOKE_GAP / 2.0 + BASE_CHEEK_T / 2.0
    bridge = _box((0.016, 0.048, 0.018), (SHOULDER_X - 0.016, 0.0, SHOULDER_Z))
    base = base.union(bridge)
    for sign in (-1.0, 1.0):
        y_center = sign * cheek_y
        cheek = _box(
            (0.020, BASE_CHEEK_T, 0.044),
            (SHOULDER_X - 0.010, y_center, SHOULDER_Z),
        )
        base = base.union(cheek)

    return base
def _primary_link_shape() -> cq.Workplane:
    root_lug = _box((0.020, 0.020, 0.036), (0.010, 0.0, 0.0))
    root_body = _box((0.028, 0.026, 0.024), (0.030, 0.0, 0.0))
    beam = _box((0.112, 0.022, 0.018), (0.086, 0.0, 0.0))
    spine = _box((0.060, 0.014, 0.012), (0.094, 0.0, 0.012))
    elbow_bridge = _box((0.024, 0.040, 0.018), (LINK1_LEN - 0.022, 0.0, 0.0))
    link = root_lug.union(root_body).union(beam).union(spine).union(elbow_bridge)

    cheek_y = ELBOW_GAP / 2.0 + ELBOW_CHEEK_T / 2.0
    for sign in (-1.0, 1.0):
        y_center = sign * cheek_y
        cheek = _box((0.016, ELBOW_CHEEK_T, 0.036), (LINK1_LEN - 0.008, y_center, 0.0))
        link = link.union(cheek)

    return link
def _secondary_link_shape() -> cq.Workplane:
    root_lug = _box((0.022, ELBOW_GAP, 0.028), (0.001, 0.0, 0.0))
    root_body = _box((0.034, 0.020, 0.022), (0.024, 0.0, 0.0))
    beam = _box((0.094, 0.020, 0.017), (0.077, 0.0, 0.0))
    spine = _box((0.050, 0.014, 0.011), (0.084, 0.0, 0.011))
    wrist_bridge = _box((0.020, 0.036, 0.016), (LINK2_LEN - 0.020, 0.0, 0.0))
    link = root_lug.union(root_body).union(beam).union(spine).union(wrist_bridge)

    cheek_y = WRIST_GAP / 2.0 + WRIST_CHEEK_T / 2.0
    for sign in (-1.0, 1.0):
        y_center = sign * cheek_y
        cheek = _box((0.014, WRIST_CHEEK_T, 0.030), (LINK2_LEN - 0.007, y_center, 0.0))
        link = link.union(cheek)

    return link
def _wrist_shape() -> cq.Workplane:
    root_lug = _box((0.020, WRIST_GAP, 0.024), (0.000, 0.0, 0.0))
    neck = _box((0.034, 0.020, 0.018), (0.024, 0.0, 0.0))
    brace = _box((0.014, 0.034, 0.034), (0.040, 0.0, 0.0))
    face_plate = _box((0.012, 0.052, 0.052), (0.053, 0.0, 0.0))
    return root_lug.union(neck).union(brace).union(face_plate)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bench_cantilever_arm")

    model.material("powder_graphite", rgba=(0.20, 0.22, 0.25, 1.0))
    model.material("machined_aluminum", rgba=(0.73, 0.75, 0.78, 1.0))
    model.material("dark_anodized", rgba=(0.32, 0.35, 0.38, 1.0))

    base = model.part("base")
    base.visual(mesh_from_cadquery(_base_shape(), "cantilever_base"), material="powder_graphite", name="base_shell")
    base.inertial = Inertial.from_geometry(
        Box((0.160, 0.120, 0.104)),
        mass=4.8,
        origin=Origin(xyz=(-0.010, 0.0, 0.052)),
    )

    primary_link = model.part("primary_link")
    primary_link.visual(
        mesh_from_cadquery(_primary_link_shape(), "cantilever_primary_link"),
        material="machined_aluminum",
        name="primary_link_body",
    )
    primary_link.inertial = Inertial.from_geometry(
        Box((0.170, 0.048, 0.048)),
        mass=1.1,
        origin=Origin(xyz=(0.085, 0.0, 0.0)),
    )

    secondary_link = model.part("secondary_link")
    secondary_link.visual(
        mesh_from_cadquery(_secondary_link_shape(), "cantilever_secondary_link"),
        material="machined_aluminum",
        name="secondary_link_body",
    )
    secondary_link.inertial = Inertial.from_geometry(
        Box((0.145, 0.042, 0.042)),
        mass=0.8,
        origin=Origin(xyz=(0.0725, 0.0, 0.0)),
    )

    wrist_face = model.part("wrist_face")
    wrist_face.visual(
        mesh_from_cadquery(_wrist_shape(), "cantilever_wrist_face"),
        material="dark_anodized",
        name="wrist_face_body",
    )
    wrist_face.inertial = Inertial.from_geometry(
        Box((0.060, 0.060, 0.060)),
        mass=0.35,
        origin=Origin(xyz=(0.030, 0.0, 0.0)),
    )

    model.articulation(
        "shoulder_pitch",
        ArticulationType.REVOLUTE,
        parent=base,
        child=primary_link,
        origin=Origin(xyz=(SHOULDER_X, 0.0, SHOULDER_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.45, upper=1.15, effort=35.0, velocity=1.2),
    )
    model.articulation(
        "elbow_pitch",
        ArticulationType.REVOLUTE,
        parent=primary_link,
        child=secondary_link,
        origin=Origin(xyz=(LINK1_LEN, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.20, upper=1.45, effort=22.0, velocity=1.5),
    )
    model.articulation(
        "wrist_pitch",
        ArticulationType.REVOLUTE,
        parent=secondary_link,
        child=wrist_face,
        origin=Origin(xyz=(LINK2_LEN, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-1.10, upper=1.10, effort=10.0, velocity=2.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
