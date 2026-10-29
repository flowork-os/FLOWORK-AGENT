# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, blimp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: blimp

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
GONDOLA_Z = -2.95
def _normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = vector
    length = math.sqrt((x * x) + (y * y) + (z * z))
    return (x / length, y / length, z / length)
def _axis_to_rpy(axis: tuple[float, float, float]) -> tuple[float, float, float]:
    ax, ay, az = _normalize(axis)
    yaw = math.atan2(ay, ax)
    pitch = math.atan2(math.sqrt((ax * ax) + (ay * ay)), az)
    return (0.0, pitch, yaw)
def _circle_loft_x(stations: list[tuple[float, float]]):
    loft = cq.Workplane("YZ", origin=(stations[0][0], 0.0, 0.0)).circle(stations[0][1])
    previous_x = stations[0][0]
    for x_pos, radius in stations[1:]:
        loft = loft.workplane(offset=x_pos - previous_x).circle(radius)
        previous_x = x_pos
    return loft.loft(combine=True, ruled=False)
def _build_envelope_shape():
    return _circle_loft_x(
        [
            (-9.00, 0.10),
            (-8.10, 0.62),
            (-6.60, 1.48),
            (-3.20, 2.05),
            (0.00, 2.20),
            (3.00, 2.08),
            (5.90, 1.68),
            (7.80, 0.96),
            (9.00, 0.16),
        ]
    )
def _build_nacelle_shape():
    return _circle_loft_x(
        [
            (-0.72, 0.10),
            (-0.50, 0.22),
            (-0.10, 0.30),
            (0.28, 0.31),
            (0.56, 0.24),
            (0.72, 0.12),
        ]
    )
def _build_rudder_surface_shape():
    return (
        cq.Workplane("XZ")
        .polyline(
            [
                (0.0, 0.0),
                (-0.16, 0.0),
                (-0.56, 0.26),
                (-0.49, 1.08),
                (-0.22, 1.36),
                (0.0, 1.36),
            ]
        )
        .close()
        .extrude(0.05, both=True)
    )
def _build_elevator_surface_shape():
    return (
        cq.Workplane("XY")
        .polyline(
            [
                (0.0, -0.63),
                (-0.16, -0.63),
                (-0.62, -0.22),
                (-0.58, 0.22),
                (-0.18, 0.63),
                (0.0, 0.63),
            ]
        )
        .close()
        .extrude(0.06, both=True)
    )
def _rod_origin(start: tuple[float, float, float], end: tuple[float, float, float]) -> Origin:
    axis = (end[0] - start[0], end[1] - start[1], end[2] - start[2])
    mid = (
        0.5 * (start[0] + end[0]),
        0.5 * (start[1] + end[1]),
        0.5 * (start[2] + end[2]),
    )
    return Origin(xyz=mid, rpy=_axis_to_rpy(axis))
def _rod_length(start: tuple[float, float, float], end: tuple[float, float, float]) -> float:
    axis = (end[0] - start[0], end[1] - start[1], end[2] - start[2])
    return math.sqrt((axis[0] * axis[0]) + (axis[1] * axis[1]) + (axis[2] * axis[2]))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="advertising_blimp")

    envelope_paint = model.material("envelope_paint", rgba=(0.95, 0.93, 0.86, 1.0))
    gondola_paint = model.material("gondola_paint", rgba=(0.82, 0.83, 0.86, 1.0))
    nacelle_paint = model.material("nacelle_paint", rgba=(0.86, 0.87, 0.90, 1.0))
    dark_window = model.material("dark_window", rgba=(0.15, 0.19, 0.24, 1.0))
    dark_metal = model.material("dark_metal", rgba=(0.28, 0.30, 0.33, 1.0))
    prop_paint = model.material("prop_paint", rgba=(0.16, 0.17, 0.18, 1.0))

    envelope = model.part("envelope")
    envelope.visual(
        mesh_from_cadquery(_build_envelope_shape(), "envelope_shell"),
        material=envelope_paint,
        name="envelope_shell",
    )
    envelope.visual(
        Box((1.15, 0.12, 1.55)),
        origin=Origin(xyz=(-7.54, 0.0, 1.42)),
        material=envelope_paint,
        name="upper_fin",
    )
    envelope.visual(
        Box((0.96, 0.10, 1.10)),
        origin=Origin(xyz=(-7.80, 0.0, -1.12)),
        material=envelope_paint,
        name="lower_fin",
    )
    envelope.visual(
        Box((0.18, 0.14, 2.55)),
        origin=Origin(xyz=(-8.18, 0.0, 0.12)),
        material=envelope_paint,
        name="fin_post",
    )
    envelope.visual(
        Box((1.08, 1.68, 0.10)),
        origin=Origin(xyz=(-7.62, 1.18, 0.04)),
        material=envelope_paint,
        name="stabilizer_0",
    )
    envelope.visual(
        Box((1.08, 1.68, 0.10)),
        origin=Origin(xyz=(-7.62, -1.18, 0.04)),
        material=envelope_paint,
        name="stabilizer_1",
    )
    envelope.visual(
        Cylinder(radius=0.035, length=1.32),
        origin=Origin(xyz=(-8.145, 0.0, 1.38)),
        material=dark_metal,
        name="rudder_hinge",
    )
    envelope.visual(
        Cylinder(radius=0.030, length=1.30),
        origin=Origin(xyz=(-8.145, 1.18, 0.04), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="elevator_hinge_0",
    )
    envelope.visual(
        Cylinder(radius=0.030, length=1.30),
        origin=Origin(xyz=(-8.145, -1.18, 0.04), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="elevator_hinge_1",
    )
    envelope.visual(
        Box((0.22, 0.18, 0.22)),
        origin=Origin(xyz=(1.06, 0.86, -2.03)),
        material=dark_metal,
        name="gondola_pad_front_0",
    )
    envelope.visual(
        Box((0.22, 0.18, 0.22)),
        origin=Origin(xyz=(1.06, -0.86, -2.03)),
        material=dark_metal,
        name="gondola_pad_front_1",
    )
    envelope.visual(
        Box((0.24, 0.18, 0.22)),
        origin=Origin(xyz=(-0.80, 0.70, -2.03)),
        material=dark_metal,
        name="gondola_pad_rear_0",
    )
    envelope.visual(
        Box((0.24, 0.18, 0.22)),
        origin=Origin(xyz=(-0.80, -0.70, -2.03)),
        material=dark_metal,
        name="gondola_pad_rear_1",
    )
    envelope.visual(
        Box((0.18, 0.16, 0.12)),
        origin=Origin(xyz=(-0.31, 2.10, -0.48)),
        material=dark_metal,
        name="nacelle_pad_front_0",
    )
    envelope.visual(
        Box((0.18, 0.16, 0.12)),
        origin=Origin(xyz=(-0.31, -2.10, -0.48)),
        material=dark_metal,
        name="nacelle_pad_front_1",
    )
    envelope.visual(
        Box((0.18, 0.16, 0.12)),
        origin=Origin(xyz=(-0.71, 2.10, -0.54)),
        material=dark_metal,
        name="nacelle_pad_rear_0",
    )
    envelope.visual(
        Box((0.18, 0.16, 0.12)),
        origin=Origin(xyz=(-0.71, -2.10, -0.54)),
        material=dark_metal,
        name="nacelle_pad_rear_1",
    )

    gondola = model.part("gondola")
    gondola.visual(
        Box((2.95, 0.95, 0.88)),
        origin=Origin(xyz=(0.15, 0.0, GONDOLA_Z)),
        material=gondola_paint,
        name="cabin_shell",
    )
    gondola.visual(
        Box((0.80, 0.90, 0.34)),
        origin=Origin(xyz=(1.20, 0.0, GONDOLA_Z + 0.14)),
        material=dark_window,
        name="windshield_band",
    )
    for name, size, xyz in (
        ("wheel_post", (0.12, 0.08, 0.40), (-1.07, 0.0, -3.34)),
        ("wheel_bridge", (0.34, 0.20, 0.10), (-1.24, 0.0, -3.26)),
        ("fork_arm_0", (0.22, 0.03, 0.34), (-1.34, 0.065, -3.43)),
        ("fork_arm_1", (0.22, 0.03, 0.34), (-1.34, -0.065, -3.43)),
    ):
        gondola.visual(
            Box(size),
            origin=Origin(xyz=xyz),
            material=dark_metal,
            name=name,
        )
    gondola.visual(
        Cylinder(radius=0.016, length=0.16),
        origin=Origin(xyz=(-1.34, 0.0, -3.58), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="wheel_axle",
    )
    front_strut_0_start = (0.95, 0.26, GONDOLA_Z + 0.46)
    front_strut_0_end = (1.06, 0.86, -2.14)
    gondola.visual(
        Cylinder(radius=0.055, length=_rod_length(front_strut_0_start, front_strut_0_end)),
        origin=_rod_origin(front_strut_0_start, front_strut_0_end),
        material=dark_metal,
        name="front_strut_0",
    )
    front_strut_1_start = (0.95, -0.26, GONDOLA_Z + 0.46)
    front_strut_1_end = (1.06, -0.86, -2.14)
    gondola.visual(
        Cylinder(radius=0.055, length=_rod_length(front_strut_1_start, front_strut_1_end)),
        origin=_rod_origin(front_strut_1_start, front_strut_1_end),
        material=dark_metal,
        name="front_strut_1",
    )
    rear_strut_0_start = (-0.60, 0.24, GONDOLA_Z + 0.46)
    rear_strut_0_end = (-0.80, 0.70, -2.14)
    gondola.visual(
        Cylinder(radius=0.055, length=_rod_length(rear_strut_0_start, rear_strut_0_end)),
        origin=_rod_origin(rear_strut_0_start, rear_strut_0_end),
        material=dark_metal,
        name="rear_strut_0",
    )
    rear_strut_1_start = (-0.60, -0.24, GONDOLA_Z + 0.46)
    rear_strut_1_end = (-0.80, -0.70, -2.14)
    gondola.visual(
        Cylinder(radius=0.055, length=_rod_length(rear_strut_1_start, rear_strut_1_end)),
        origin=_rod_origin(rear_strut_1_start, rear_strut_1_end),
        material=dark_metal,
        name="rear_strut_1",
    )

    model.articulation(
        "envelope_to_gondola",
        ArticulationType.FIXED,
        parent=envelope,
        child=gondola,
        origin=Origin(),
    )

    nacelle_centers = {
        "nacelle_0": (-0.45, 3.08, -1.05),
        "nacelle_1": (-0.45, -3.08, -1.05),
    }

    for index, (nacelle_name, center) in enumerate(nacelle_centers.items()):
        x_center, y_center, z_center = center
        nacelle = model.part(nacelle_name)
        nacelle.visual(
            mesh_from_cadquery(_build_nacelle_shape(), f"{nacelle_name}_shell"),
            origin=Origin(xyz=center),
            material=nacelle_paint,
            name="nacelle_shell",
        )
        nacelle.visual(
            Cylinder(radius=0.055, length=0.14),
            origin=Origin(xyz=(x_center + 0.67, y_center, z_center), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=dark_metal,
            name="prop_shaft",
        )
        mount_y = 2.18 if y_center > 0.0 else -2.18
        mount_front_start = (x_center + 0.22, y_center, z_center + 0.26)
        mount_front_end = (x_center + 0.14, mount_y, -0.48)
        nacelle.visual(
            Cylinder(radius=0.06, length=_rod_length(mount_front_start, mount_front_end)),
            origin=_rod_origin(mount_front_start, mount_front_end),
            material=dark_metal,
            name="mount_front",
        )
        mount_rear_start = (x_center - 0.18, y_center, z_center + 0.24)
        mount_rear_end = (x_center - 0.26, mount_y, -0.54)
        nacelle.visual(
            Cylinder(radius=0.06, length=_rod_length(mount_rear_start, mount_rear_end)),
            origin=_rod_origin(mount_rear_start, mount_rear_end),
            material=dark_metal,
            name="mount_rear",
        )

        propeller = model.part(f"propeller_{index}")
        propeller.visual(
            Cylinder(radius=0.11, length=0.12),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=dark_metal,
            name="hub",
        )
        propeller.visual(
            Box((0.04, 1.22, 0.14)),
            origin=Origin(rpy=(0.0, math.radians(12.0), 0.0)),
            material=prop_paint,
            name="blade_pair",
        )

        model.articulation(
            f"envelope_to_{nacelle_name}",
            ArticulationType.FIXED,
            parent=envelope,
            child=nacelle,
            origin=Origin(),
        )
        model.articulation(
            f"{nacelle_name}_to_propeller_{index}",
            ArticulationType.CONTINUOUS,
            parent=nacelle,
            child=propeller,
            origin=Origin(xyz=(x_center + 0.80, y_center, z_center)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=4.0, velocity=35.0),
        )

    rudder = model.part("rudder")
    rudder.visual(
        Cylinder(radius=0.020, length=1.28),
        origin=Origin(xyz=(0.0, 0.0, 0.66)),
        material=dark_metal,
        name="rudder_barrel",
    )
    rudder.visual(
        mesh_from_cadquery(_build_rudder_surface_shape(), "rudder_surface"),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=envelope_paint,
        name="rudder_surface",
    )

    for index, y_pos in enumerate((1.18, -1.18)):
        elevator = model.part(f"elevator_{index}")
        elevator.visual(
            Cylinder(radius=0.020, length=1.24),
            origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
            material=dark_metal,
            name="hinge_barrel",
        )
        elevator.visual(
            mesh_from_cadquery(_build_elevator_surface_shape(), f"elevator_surface_{index}"),
            origin=Origin(xyz=(0.0, 0.0, 0.0)),
            material=envelope_paint,
            name="elevator_surface",
        )
        model.articulation(
            f"envelope_to_elevator_{index}",
            ArticulationType.REVOLUTE,
            parent=envelope,
            child=elevator,
            origin=Origin(xyz=(-8.18, y_pos, 0.04)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(effort=8.0, velocity=1.5, lower=-0.45, upper=0.45),
        )

    mooring_wheel = model.part("mooring_wheel")
    mooring_wheel.visual(
        Cylinder(radius=0.18, length=0.10),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="wheel_tire",
    )
    mooring_wheel.visual(
        Cylinder(radius=0.055, length=0.08),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="wheel_hub",
    )

    model.articulation(
        "envelope_to_rudder",
        ArticulationType.REVOLUTE,
        parent=envelope,
        child=rudder,
        origin=Origin(xyz=(-8.18, 0.0, 0.72)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=8.0, velocity=1.2, lower=-0.55, upper=0.55),
    )
    model.articulation(
        "gondola_to_mooring_wheel",
        ArticulationType.CONTINUOUS,
        parent=gondola,
        child=mooring_wheel,
        origin=Origin(xyz=(-1.34, 0.0, -3.58)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=10.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
