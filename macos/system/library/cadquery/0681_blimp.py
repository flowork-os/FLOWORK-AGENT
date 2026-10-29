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
def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2)
def _midpoint(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5)
def _rpy_for_cylinder(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dz = b[2] - a[2]
    length_xy = math.hypot(dx, dy)
    yaw = math.atan2(dy, dx)
    pitch = math.atan2(length_xy, dz)
    return (0.0, pitch, yaw)
def _add_member(part, a, b, radius: float, material, name: str | None = None) -> None:
    part.visual(
        Cylinder(radius=radius, length=_distance(a, b)),
        origin=Origin(xyz=_midpoint(a, b), rpy=_rpy_for_cylinder(a, b)),
        material=material,
        name=name,
    )
def _revolved_x(profile: list[tuple[float, float]]) -> cq.Workplane:
    return (
        cq.Workplane("XZ")
        .moveTo(profile[0][0], profile[0][1])
        .spline(profile[1:])
        .close()
        .revolve(360, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    )
def _horizontal_surface(
    *,
    span: float,
    root_chord: float,
    tip_chord: float,
    thickness: float,
    side_sign: float,
) -> cq.Workplane:
    y_mid = side_sign * span * 0.58
    y_tip = side_sign * span
    outline = [
        (0.0, 0.0),
        (-0.16 * root_chord, y_mid),
        (-0.26 * tip_chord, y_tip),
        (-tip_chord, y_tip),
        (-root_chord, 0.0),
    ]
    return (
        cq.Workplane("XY")
        .polyline(outline)
        .close()
        .extrude(thickness, both=True)
        .edges("|Z")
        .fillet(min(thickness * 0.45, 0.02))
    )
def _vertical_root_surface(
    *,
    span: float,
    root_chord: float,
    tip_chord: float,
    thickness: float,
    z_sign: float,
) -> cq.Workplane:
    z_mid = z_sign * span * 0.56
    z_tip = z_sign * span
    outline = [
        (0.0, 0.0),
        (-0.16 * root_chord, z_mid),
        (-0.28 * tip_chord, z_tip),
        (-tip_chord, z_tip),
        (-root_chord, 0.0),
    ]
    return (
        cq.Workplane("XZ")
        .polyline(outline)
        .close()
        .extrude(thickness, both=True)
        .edges("|Y")
        .fillet(min(thickness * 0.45, 0.02))
    )
def _rudder_surface(*, thickness: float) -> cq.Workplane:
    outline = [
        (0.0, 0.92),
        (-0.22, 0.74),
        (-0.96, 0.18),
        (-1.02, 0.0),
        (-0.96, -0.18),
        (-0.22, -0.74),
        (0.0, -0.92),
    ]
    return (
        cq.Workplane("XZ")
        .polyline(outline)
        .close()
        .extrude(thickness, both=True)
        .edges("|Y")
        .fillet(min(thickness * 0.45, 0.025))
    )
def _propeller_shape() -> cq.Workplane:
    hub = cq.Workplane("YZ").circle(0.055).extrude(0.08, both=True)
    blade = (
        cq.Workplane("XY")
        .box(0.018, 0.34, 0.058, centered=(True, False, True))
        .translate((0.0, 0.035, 0.0))
        .edges("|X")
        .fillet(0.012)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 18.0)
    )
    assembly = hub
    for angle in (0.0, 120.0, 240.0):
        assembly = assembly.union(blade.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle))
    return assembly
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="sightseeing_blimp")

    envelope_white = model.material("envelope_white", rgba=(0.92, 0.93, 0.90, 1.0))
    cabin_white = model.material("cabin_white", rgba=(0.86, 0.87, 0.85, 1.0))
    accent_blue = model.material("accent_blue", rgba=(0.18, 0.32, 0.54, 1.0))
    strut_grey = model.material("strut_grey", rgba=(0.43, 0.46, 0.49, 1.0))
    glass_tint = model.material("glass_tint", rgba=(0.30, 0.42, 0.50, 0.72))
    prop_black = model.material("prop_black", rgba=(0.10, 0.10, 0.11, 1.0))
    rubber = model.material("rubber", rgba=(0.05, 0.05, 0.05, 1.0))
    hub_silver = model.material("hub_silver", rgba=(0.63, 0.65, 0.68, 1.0))

    hull_profile = [
        (-6.65, 0.0),
        (-6.48, 0.08),
        (-5.92, 0.34),
        (-4.40, 0.94),
        (-1.40, 1.48),
        (1.70, 1.60),
        (4.55, 1.33),
        (6.10, 0.82),
        (6.88, 0.19),
        (7.05, 0.0),
    ]
    hull_shape = _revolved_x(hull_profile)

    cabin_shape = (
        cq.Workplane("XY")
        .box(4.55, 1.34, 1.26)
        .edges("|Z")
        .fillet(0.16)
        .edges(">Z")
        .fillet(0.08)
    )
    cabin_nose = (
        cq.Workplane("XY")
        .box(0.95, 1.18, 0.92)
        .translate((2.20, 0.0, 0.02))
        .edges("|Z")
        .fillet(0.10)
    )
    cabin_tail = (
        cq.Workplane("XY")
        .box(0.70, 1.06, 0.84)
        .translate((-2.25, 0.0, -0.08))
        .edges("|Z")
        .fillet(0.08)
    )
    gondola_shape = cabin_shape.union(cabin_nose).union(cabin_tail)

    left_root_shape = _horizontal_surface(
        span=0.24,
        root_chord=0.42,
        tip_chord=0.16,
        thickness=0.08,
        side_sign=1.0,
    )
    right_root_shape = _horizontal_surface(
        span=0.24,
        root_chord=0.42,
        tip_chord=0.16,
        thickness=0.08,
        side_sign=-1.0,
    )
    dorsal_root_shape = _vertical_root_surface(
        span=0.34,
        root_chord=0.50,
        tip_chord=0.16,
        thickness=0.08,
        z_sign=1.0,
    )
    ventral_root_shape = _vertical_root_surface(
        span=0.34,
        root_chord=0.50,
        tip_chord=0.16,
        thickness=0.08,
        z_sign=-1.0,
    )

    airframe = model.part("airframe")
    airframe.visual(
        mesh_from_cadquery(hull_shape, "blimp_hull"),
        material=envelope_white,
        name="hull_shell",
    )
    airframe.visual(
        mesh_from_cadquery(gondola_shape, "blimp_gondola"),
        origin=Origin(xyz=(0.15, 0.0, -2.22)),
        material=cabin_white,
        name="cabin_shell",
    )
    airframe.visual(
        Box((3.35, 0.14, 0.38)),
        origin=Origin(xyz=(0.20, 0.64, -2.07)),
        material=glass_tint,
        name="left_windows",
    )
    airframe.visual(
        Box((3.35, 0.14, 0.38)),
        origin=Origin(xyz=(0.20, -0.64, -2.07)),
        material=glass_tint,
        name="right_windows",
    )
    airframe.visual(
        Cylinder(radius=0.17, length=0.62),
        origin=Origin(xyz=(0.71, 1.30, -2.00), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=cabin_white,
        name="left_pod",
    )
    airframe.visual(
        Cylinder(radius=0.17, length=0.62),
        origin=Origin(xyz=(0.71, -1.30, -2.00), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=cabin_white,
        name="right_pod",
    )
    airframe.visual(
        Box((0.24, 0.34, 0.34)),
        origin=Origin(xyz=(1.00, 1.30, -2.00)),
        material=cabin_white,
        name="left_pod_nose",
    )
    airframe.visual(
        Box((0.24, 0.34, 0.34)),
        origin=Origin(xyz=(1.00, -1.30, -2.00)),
        material=cabin_white,
        name="right_pod_nose",
    )
    airframe.visual(
        Box((0.18, 0.24, 0.24)),
        origin=Origin(xyz=(0.40, 1.30, -2.00)),
        material=accent_blue,
        name="left_pod_tail",
    )
    airframe.visual(
        Box((0.18, 0.24, 0.24)),
        origin=Origin(xyz=(0.40, -1.30, -2.00)),
        material=accent_blue,
        name="right_pod_tail",
    )
    airframe.visual(
        mesh_from_cadquery(dorsal_root_shape, "dorsal_root"),
        origin=Origin(xyz=(-5.94, 0.0, 0.46)),
        material=envelope_white,
        name="dorsal_root",
    )
    airframe.visual(
        mesh_from_cadquery(ventral_root_shape, "ventral_root"),
        origin=Origin(xyz=(-5.94, 0.0, -0.46)),
        material=envelope_white,
        name="ventral_root",
    )
    airframe.visual(
        mesh_from_cadquery(left_root_shape, "left_tail_root"),
        origin=Origin(xyz=(-5.94, 0.42, 0.0)),
        material=envelope_white,
        name="left_tail_root",
    )
    airframe.visual(
        mesh_from_cadquery(right_root_shape, "right_tail_root"),
        origin=Origin(xyz=(-5.94, -0.42, 0.0)),
        material=envelope_white,
        name="right_tail_root",
    )

    for x_pos in (1.65, 0.35, -1.25):
        _add_member(
            airframe,
            (x_pos + 0.10, 0.26, -1.46 if x_pos > 0.0 else -1.40),
            (x_pos, 0.26, -1.61),
            radius=0.05,
            material=strut_grey,
        )
        _add_member(
            airframe,
            (x_pos + 0.10, -0.26, -1.46 if x_pos > 0.0 else -1.40),
            (x_pos, -0.26, -1.61),
            radius=0.05,
            material=strut_grey,
        )

    _add_member(
        airframe,
        (0.42, 0.62, -1.95),
        (0.56, 1.14, -2.00),
        radius=0.085,
        material=strut_grey,
        name="left_pod_boom",
    )
    _add_member(
        airframe,
        (0.42, -0.62, -1.95),
        (0.56, -1.14, -2.00),
        radius=0.085,
        material=strut_grey,
        name="right_pod_boom",
    )
    _add_member(
        airframe,
        (0.04, 0.54, -1.74),
        (0.28, 1.03, -1.92),
        radius=0.032,
        material=strut_grey,
    )
    _add_member(
        airframe,
        (0.04, -0.54, -1.74),
        (0.28, -1.03, -1.92),
        radius=0.032,
        material=strut_grey,
    )
    _add_member(
        airframe,
        (-6.10, 0.22, 0.00),
        (-5.96, 0.42, 0.00),
        radius=0.07,
        material=strut_grey,
        name="left_tail_mount",
    )
    _add_member(
        airframe,
        (-6.10, -0.22, 0.00),
        (-5.96, -0.42, 0.00),
        radius=0.07,
        material=strut_grey,
        name="right_tail_mount",
    )
    _add_member(
        airframe,
        (-6.10, 0.00, 0.20),
        (-5.98, 0.00, 0.48),
        radius=0.07,
        material=strut_grey,
        name="dorsal_mount",
    )
    _add_member(
        airframe,
        (-6.10, 0.00, -0.20),
        (-5.98, 0.00, -0.48),
        radius=0.07,
        material=strut_grey,
        name="ventral_mount",
    )

    airframe.visual(
        Box((0.16, 0.14, 0.12)),
        origin=Origin(xyz=(-2.22, 0.0, -3.02)),
        material=strut_grey,
        name="fork_crown",
    )
    _add_member(
        airframe,
        (-2.05, 0.0, -2.78),
        (-2.20, 0.0, -2.98),
        radius=0.05,
        material=strut_grey,
        name="wheel_post",
    )
    _add_member(
        airframe,
        (-2.22, 0.06, -3.02),
        (-2.46, 0.07, -3.18),
        radius=0.022,
        material=strut_grey,
        name="fork_arm_0",
    )
    _add_member(
        airframe,
        (-2.22, -0.06, -3.02),
        (-2.46, -0.07, -3.18),
        radius=0.022,
        material=strut_grey,
        name="fork_arm_1",
    )
    _add_member(
        airframe,
        (-2.46, 0.07, -3.18),
        (-2.46, 0.035, -3.18),
        radius=0.006,
        material=strut_grey,
        name="fork_stub_0",
    )
    _add_member(
        airframe,
        (-2.46, -0.07, -3.18),
        (-2.46, -0.035, -3.18),
        radius=0.006,
        material=strut_grey,
        name="fork_stub_1",
    )
    airframe.inertial = Inertial.from_geometry(
        Box((14.20, 3.30, 6.40)),
        mass=2800.0,
        origin=Origin(xyz=(0.0, 0.0, -0.55)),
    )

    propeller_mesh = mesh_from_cadquery(_propeller_shape(), "propeller")

    left_propeller = model.part("left_propeller")
    left_propeller.visual(
        propeller_mesh,
        origin=Origin(xyz=(0.18, 0.0, 0.0)),
        material=prop_black,
        name="propeller_assembly",
    )
    left_propeller.inertial = Inertial.from_geometry(
        Cylinder(radius=0.18, length=0.18),
        mass=10.0,
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
    )

    right_propeller = model.part("right_propeller")
    right_propeller.visual(
        propeller_mesh,
        origin=Origin(xyz=(0.18, 0.0, 0.0)),
        material=prop_black,
        name="propeller_assembly",
    )
    right_propeller.inertial = Inertial.from_geometry(
        Cylinder(radius=0.18, length=0.18),
        mass=10.0,
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
    )

    rudder = model.part("rudder")
    rudder.visual(
        mesh_from_cadquery(_rudder_surface(thickness=0.11), "rudder_surface"),
        material=envelope_white,
        name="rudder_surface",
    )
    rudder.inertial = Inertial.from_geometry(
        Box((1.05, 0.12, 1.90)),
        mass=24.0,
        origin=Origin(xyz=(-0.50, 0.0, 0.0)),
    )

    left_elevator = model.part("left_elevator")
    left_elevator.visual(
        mesh_from_cadquery(
            _horizontal_surface(
                span=1.18,
                root_chord=0.96,
                tip_chord=0.72,
                thickness=0.10,
                side_sign=1.0,
            ),
            "left_elevator_surface",
        ),
        material=envelope_white,
        name="left_elevator_surface",
    )
    left_elevator.inertial = Inertial.from_geometry(
        Box((0.96, 1.18, 0.10)),
        mass=18.0,
        origin=Origin(xyz=(-0.48, 0.59, 0.0)),
    )

    right_elevator = model.part("right_elevator")
    right_elevator.visual(
        mesh_from_cadquery(
            _horizontal_surface(
                span=1.18,
                root_chord=0.96,
                tip_chord=0.72,
                thickness=0.10,
                side_sign=-1.0,
            ),
            "right_elevator_surface",
        ),
        material=envelope_white,
        name="right_elevator_surface",
    )
    right_elevator.inertial = Inertial.from_geometry(
        Box((0.96, 1.18, 0.10)),
        mass=18.0,
        origin=Origin(xyz=(-0.48, -0.59, 0.0)),
    )

    mooring_wheel = model.part("mooring_wheel")
    mooring_wheel.visual(
        Cylinder(radius=0.18, length=0.07),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=rubber,
        name="wheel_tire",
    )
    mooring_wheel.visual(
        Cylinder(radius=0.075, length=0.060),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=hub_silver,
        name="wheel_hub",
    )
    mooring_wheel.inertial = Inertial.from_geometry(
        Cylinder(radius=0.18, length=0.07),
        mass=8.0,
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
    )

    model.articulation(
        "airframe_to_left_propeller",
        ArticulationType.CONTINUOUS,
        parent=airframe,
        child=left_propeller,
        origin=Origin(xyz=(1.02, 1.30, -2.00)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=25.0, velocity=30.0),
    )
    model.articulation(
        "airframe_to_right_propeller",
        ArticulationType.CONTINUOUS,
        parent=airframe,
        child=right_propeller,
        origin=Origin(xyz=(1.02, -1.30, -2.00)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=25.0, velocity=30.0),
    )
    model.articulation(
        "airframe_to_rudder",
        ArticulationType.REVOLUTE,
        parent=airframe,
        child=rudder,
        origin=Origin(xyz=(-6.48, 0.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=35.0,
            velocity=1.2,
            lower=-math.radians(35.0),
            upper=math.radians(35.0),
        ),
    )
    model.articulation(
        "airframe_to_left_elevator",
        ArticulationType.REVOLUTE,
        parent=airframe,
        child=left_elevator,
        origin=Origin(xyz=(-6.323, 0.42, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=24.0,
            velocity=1.2,
            lower=-math.radians(22.0),
            upper=math.radians(22.0),
        ),
    )
    model.articulation(
        "airframe_to_right_elevator",
        ArticulationType.REVOLUTE,
        parent=airframe,
        child=right_elevator,
        origin=Origin(xyz=(-6.323, -0.42, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=24.0,
            velocity=1.2,
            lower=-math.radians(22.0),
            upper=math.radians(22.0),
        ),
    )
    model.articulation(
        "airframe_to_mooring_wheel",
        ArticulationType.CONTINUOUS,
        parent=airframe,
        child=mooring_wheel,
        origin=Origin(xyz=(-2.46, 0.0, -3.18)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=15.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
