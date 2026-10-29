# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_conditioning_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_conditioning_machine

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
BODY_WIDTH = 0.94
BODY_HEIGHT = 0.295
SIDE_WALL = 0.014
OUTER_PROFILE = [
    (0.000, 0.000),
    (0.000, BODY_HEIGHT),
    (0.090, BODY_HEIGHT),
    (0.145, 0.291),
    (0.188, 0.277),
    (0.220, 0.243),
    (0.236, 0.197),
    (0.233, 0.150),
    (0.218, 0.109),
    (0.193, 0.079),
    (0.156, 0.049),
    (0.106, 0.022),
    (0.050, 0.010),
]
INNER_PROFILE = [
    (0.006, 0.015),
    (0.006, BODY_HEIGHT - 0.018),
    (0.074, BODY_HEIGHT - 0.018),
    (0.126, 0.272),
    (0.166, 0.258),
    (0.196, 0.227),
    (0.209, 0.188),
    (0.206, 0.146),
    (0.194, 0.112),
    (0.172, 0.087),
    (0.134, 0.061),
    (0.088, 0.036),
    (0.046, 0.020),
]
OUTLET_WIDTH = 0.842
OUTLET_HEIGHT = 0.038
OUTLET_DEPTH = 0.116
OUTLET_Y_CENTER = 0.147
OUTLET_Z_CENTER = 0.072
OUTLET_FRONT_Y = OUTLET_Y_CENTER + OUTLET_DEPTH / 2.0
OUTLET_BOTTOM_Z = OUTLET_Z_CENTER - OUTLET_HEIGHT / 2.0
FLAP_WIDTH = OUTLET_WIDTH - 0.004
FLAP_CHORD = 0.062
FLAP_THICKNESS = 0.0032
FLAP_ROD_RADIUS = 0.0028
FLAP_REST_OPEN_RAD = 0.30
FLAP_JOURNAL_LENGTH = 0.037
FLAP_JOURNAL_SIZE = 0.0065
FLAP_JOURNAL_CENTER_X = FLAP_WIDTH / 2.0 + FLAP_JOURNAL_LENGTH / 2.0
FLAP_MOUNT_LENGTH = 0.010
FLAP_MOUNT_DEPTH = 0.060
VANE_HEIGHT = 0.032
VANE_SHAFT_LENGTH = 0.036
VANE_THICKNESS = 0.0055
VANE_CHORD = 0.014
VANE_SHAFT_RADIUS = 0.0024
VANE_Y = 0.154
VANE_Z = OUTLET_Z_CENTER
VANE_X_OFFSET = 0.145
def _extruded_profile(points: list[tuple[float, float]], width: float):
    return cq.Workplane("YZ").polyline(points).close().extrude(width, both=True)
def _build_body_shape():
    outer = _extruded_profile(OUTER_PROFILE, BODY_WIDTH / 2.0)
    inner = _extruded_profile(INNER_PROFILE, (BODY_WIDTH - 2.0 * SIDE_WALL) / 2.0)

    shell = outer.cut(inner)

    outlet_cut = (
        cq.Workplane("XY")
        .box(OUTLET_WIDTH, OUTLET_DEPTH, OUTLET_HEIGHT)
        .translate((0.0, OUTLET_Y_CENTER, OUTLET_Z_CENTER))
    )
    top_seam = (
        cq.Workplane("XY")
        .box(BODY_WIDTH * 0.78, 0.004, 0.018)
        .translate((0.0, 0.184, 0.243))
    )

    return shell.cut(outlet_cut).cut(top_seam)
def _build_flap_shape():
    hinge_rod = cq.Workplane("YZ").circle(FLAP_ROD_RADIUS).extrude(FLAP_WIDTH / 2.0, both=True)
    end_journal = (
        cq.Workplane("XY")
        .box(FLAP_JOURNAL_LENGTH, FLAP_JOURNAL_SIZE, FLAP_JOURNAL_SIZE)
        .translate((FLAP_JOURNAL_CENTER_X, 0.0, 0.0))
    )
    mirrored_end_journal = end_journal.mirror("YZ")
    flap_panel = (
        cq.Workplane("XY")
        .box(FLAP_WIDTH, FLAP_CHORD, FLAP_THICKNESS)
        .translate((0.0, FLAP_CHORD / 2.0, -0.0015))
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -FLAP_REST_OPEN_RAD * 180.0 / 3.141592653589793)
    )
    return hinge_rod.union(end_journal).union(mirrored_end_journal).union(flap_panel)
def _build_vane_shape():
    shaft = cq.Workplane("XY").circle(VANE_SHAFT_RADIUS).extrude(VANE_SHAFT_LENGTH / 2.0, both=True)
    blade = (
        cq.Workplane("XY")
        .box(VANE_THICKNESS, VANE_CHORD, VANE_HEIGHT)
        .translate((0.0, VANE_CHORD / 2.0, 0.0))
    )
    return shaft.union(blade)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="ductless_mini_split")

    model.material("housing_white", rgba=(0.95, 0.95, 0.93, 1.0))
    model.material("flap_white", rgba=(0.92, 0.92, 0.90, 1.0))
    model.material("vane_gray", rgba=(0.63, 0.66, 0.69, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_build_body_shape(), "body_shell"),
        material="housing_white",
        name="shell",
    )
    flap_mount_y = OUTLET_FRONT_Y - 0.024
    flap_mount_z = OUTLET_BOTTOM_Z + 0.010
    for side, suffix in ((-1.0, "0"), (1.0, "1")):
        body.visual(
            Box((FLAP_MOUNT_LENGTH, FLAP_MOUNT_DEPTH, FLAP_JOURNAL_SIZE)),
            origin=Origin(xyz=(side * (FLAP_JOURNAL_CENTER_X + 0.0235), flap_mount_y, flap_mount_z)),
            material="housing_white",
            name=f"flap_mount_{suffix}",
        )

    for vane_name, vane_x in (("vane_0", -VANE_X_OFFSET), ("vane_1", VANE_X_OFFSET)):
        for z_sign, suffix in ((-1.0, "lower"), (1.0, "upper")):
            mount_length = 0.006 if suffix == "upper" else 0.004
            mount_offset = VANE_SHAFT_LENGTH / 2.0 + mount_length / 2.0
            body.visual(
                Cylinder(radius=0.0032, length=mount_length),
                origin=Origin(
                    xyz=(
                        vane_x,
                        VANE_Y,
                        VANE_Z + z_sign * mount_offset,
                    )
                ),
                material="housing_white",
                name=f"{vane_name}_{suffix}_mount",
            )
        body.visual(
            Box((0.012, 0.064, 0.008)),
            origin=Origin(xyz=(vane_x, 0.182, 0.096)),
            material="housing_white",
            name=f"{vane_name}_roof_bridge",
        )

    flap = model.part("flap")
    flap.visual(
        mesh_from_cadquery(_build_flap_shape(), "outlet_flap"),
        material="flap_white",
        name="blade",
    )

    for vane_name in ("vane_0", "vane_1"):
        vane = model.part(vane_name)
        vane.visual(
            mesh_from_cadquery(_build_vane_shape(), vane_name),
            material="vane_gray",
            name="blade",
        )

    model.articulation(
        "body_to_flap",
        ArticulationType.REVOLUTE,
        parent=body,
        child=flap,
        origin=Origin(xyz=(0.0, flap_mount_y, flap_mount_z)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=-0.28, upper=0.78, effort=10.0, velocity=1.6),
    )

    model.articulation(
        "body_to_vane_0",
        ArticulationType.REVOLUTE,
        parent=body,
        child="vane_0",
        origin=Origin(xyz=(-VANE_X_OFFSET, VANE_Y, VANE_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=-0.65, upper=0.65, effort=3.0, velocity=2.5),
    )

    model.articulation(
        "body_to_vane_1",
        ArticulationType.REVOLUTE,
        parent=body,
        child="vane_1",
        origin=Origin(xyz=(VANE_X_OFFSET, VANE_Y, VANE_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=-0.65, upper=0.65, effort=3.0, velocity=2.5),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
