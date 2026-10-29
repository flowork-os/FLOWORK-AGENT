# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, car_axles, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: car_axles

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

def mesh_from_geometry(geometry, name=None, **kwargs):
    return _CQMesh(_to_shape(geometry), name=name if isinstance(name, str) else None)

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

def _solid_from_triangles(vertices, faces):
    """Fallback: wrap a raw triangle soup as a B-rep solid (for MeshGeometry
    instances that are authored vertex/face directly)."""
    tri_faces = []
    for (a, b, c) in faces:
        va, vb, vc = vertices[a], vertices[b], vertices[c]
        if va == vb or vb == vc or vc == va:
            continue
        w = cq.Wire.makePolygon([cq.Vector(*va), cq.Vector(*vb), cq.Vector(*vc)], close=True)
        try:
            tri_faces.append(cq.Face.makeFromWires(w))
        except Exception:
            continue
    if not tri_faces:
        raise ValidationError("MeshGeometry: no valid triangles to build a solid")
    shell = cq.Shell.makeShell(tri_faces)
    try:
        return cq.Solid.makeSolid(shell)
    except Exception:
        return cq.Compound.makeCompound(tri_faces)

class MeshGeometry:
    """Base for all geometry families. Subclasses build parametric CadQuery
    B-rep and call ``self._set(shape)``. Supports the mesh-style manipulation
    API (translate/rotate/scale/merge/copy) used by Articraft model scripts,
    applied to the underlying CadQuery shape."""

    def __init__(self, vertices=None, faces=None):
        self.vertices = list(vertices or [])
        self.faces = list(faces or [])
        self._shape = None

    # subclasses call this with their cadquery shape
    def _set(self, shape):
        self._shape = _to_shape(shape) if not isinstance(shape, cq.Shape) else shape
        return self

    def _cq(self):
        if self._shape is not None:
            return self._shape
        return _solid_from_triangles(self.vertices, self.faces)

    # ---- mesh-style authoring (raw triangle fallback path) ----
    def add_vertex(self, x, y, z):
        self.vertices.append((float(x), float(y), float(z)))
        return len(self.vertices) - 1

    def add_face(self, a, b, c):
        self.faces.append((int(a), int(b), int(c)))

    def copy(self):
        g = MeshGeometry(self.vertices, self.faces)
        g._shape = self._shape
        return g

    clone = copy

    # ---- rigid / affine transforms (operate on the cadquery shape) ----
    def translate(self, dx, dy=None, dz=None):
        if dy is None:
            dx, dy, dz = dx
        self._shape = self._cq().translate(cq.Vector(float(dx), float(dy), float(dz)))
        return self

    def rotate(self, axis, angle, *, origin=(0.0, 0.0, 0.0)):
        # Articraft angles are RADIANS; cadquery rotate takes degrees about a line.
        o = cq.Vector(float(origin[0]), float(origin[1]), float(origin[2]))
        a = cq.Vector(float(axis[0]), float(axis[1]), float(axis[2]))
        self._shape = self._cq().rotate(o, o + a, math.degrees(float(angle)))
        return self

    def scale(self, sx, sy=None, sz=None):
        if sy is None:
            sy = sz = sx
        if sz is None:
            sz = sx
        m = cq.Matrix([[float(sx), 0, 0, 0], [0, float(sy), 0, 0], [0, 0, float(sz), 0]])
        self._shape = self._cq().transformGeometry(m)
        return self

    def rotate_x(self, angle):
        return self.rotate((1.0, 0.0, 0.0), angle)

    def rotate_y(self, angle):
        return self.rotate((0.0, 1.0, 0.0), angle)

    def rotate_z(self, angle):
        return self.rotate((0.0, 0.0, 1.0), angle)

    def merge(self, other):
        o = _to_shape(other)
        if self._shape is None and not self.faces:
            self._shape = o          # empty accumulator: adopt other's shape
        else:
            self._shape = self._cq().fuse(o)
        return self

    union = merge

    def cut(self, other):
        self._shape = self._cq().cut(_to_shape(other))
        return self

    def difference(self, other):
        return self.cut(other)

    def intersect(self, other):
        self._shape = self._cq().intersect(_to_shape(other))
        return self

# ===== primitives (1 syms) =====
class SphereGeometry(MeshGeometry):
    def __init__(self, radius, *, width_segments=24, height_segments=16):
        super().__init__()
        radius = float(radius)
        solid = cq.Solid.makeSphere(
            radius, angleDegrees1=-90, angleDegrees2=90, angleDegrees3=360
        )
        self._set(solid)

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
from math import cos, pi, sin
SPIN_X = (0.0, pi / 2.0, 0.0)
ALONG_Y = (pi / 2.0, 0.0, 0.0)
def _scaled_sphere(name: str, rx: float, ry: float, rz: float):
    return mesh_from_geometry(
        SphereGeometry(1.0, width_segments=36, height_segments=24).scale(rx, ry, rz),
        name,
    )
def _add_hub_visuals(part, side_sign: float, hub_steel, cap_steel) -> None:
    def sx(value: float) -> float:
        return side_sign * value

    part.visual(
        Cylinder(radius=0.062, length=0.030),
        origin=Origin(xyz=(sx(0.015), 0.0, 0.0), rpy=SPIN_X),
        material=hub_steel,
        name="inner_collar",
    )
    part.visual(
        Cylinder(radius=0.110, length=0.110),
        origin=Origin(xyz=(sx(0.078), 0.0, 0.0), rpy=SPIN_X),
        material=hub_steel,
        name="drum_shell",
    )
    part.visual(
        Cylinder(radius=0.145, length=0.018),
        origin=Origin(xyz=(sx(0.139), 0.0, 0.0), rpy=SPIN_X),
        material=hub_steel,
        name="wheel_flange",
    )
    part.visual(
        Cylinder(radius=0.052, length=0.060),
        origin=Origin(xyz=(sx(0.082), 0.0, 0.0), rpy=SPIN_X),
        material=cap_steel,
        name="grease_cap",
    )
    part.visual(
        Cylinder(radius=0.020, length=0.032),
        origin=Origin(xyz=(sx(0.152), 0.0, 0.0), rpy=SPIN_X),
        material=cap_steel,
        name="pilot_nose",
    )

    stud_radius = 0.074
    stud_x = sx(0.154)
    for stud_index in range(5):
        angle = (2.0 * pi * stud_index) / 5.0
        part.visual(
            Cylinder(radius=0.007, length=0.026),
            origin=Origin(
                xyz=(stud_x, cos(angle) * stud_radius, sin(angle) * stud_radius),
                rpy=SPIN_X,
            ),
            material=cap_steel,
            name=f"lug_{stud_index}",
        )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="torque_tube_rear_axle")

    housing_cast = model.material("housing_cast", rgba=(0.24, 0.25, 0.27, 1.0))
    cover_steel = model.material("cover_steel", rgba=(0.34, 0.35, 0.37, 1.0))
    machined_steel = model.material("machined_steel", rgba=(0.66, 0.68, 0.71, 1.0))
    oily_steel = model.material("oily_steel", rgba=(0.44, 0.45, 0.47, 1.0))

    banjo_center_mesh = _scaled_sphere("banjo_center", 0.205, 0.155, 0.175)
    rear_cover_mesh = _scaled_sphere("rear_cover", 0.155, 0.055, 0.145)
    pinion_bell_mesh = _scaled_sphere("pinion_bell", 0.105, 0.090, 0.105)
    front_ball_mesh = _scaled_sphere("front_ball_housing", 0.082, 0.082, 0.082)

    axle_housing = model.part("axle_housing")
    axle_housing.visual(
        banjo_center_mesh,
        material=housing_cast,
        name="banjo_center",
    )
    axle_housing.visual(
        rear_cover_mesh,
        origin=Origin(xyz=(0.0, 0.122, 0.0)),
        material=cover_steel,
        name="rear_cover",
    )
    axle_housing.visual(
        pinion_bell_mesh,
        origin=Origin(xyz=(0.0, -0.185, 0.040)),
        material=housing_cast,
        name="pinion_bell",
    )
    axle_housing.visual(
        Cylinder(radius=0.073, length=0.035),
        origin=Origin(xyz=(0.0, -0.282, 0.040), rpy=ALONG_Y),
        material=cover_steel,
        name="pinion_collar",
    )
    axle_housing.visual(
        Cylinder(radius=0.055, length=0.860),
        origin=Origin(xyz=(0.0, -0.700, 0.040), rpy=ALONG_Y),
        material=housing_cast,
        name="torque_tube_main",
    )
    axle_housing.visual(
        front_ball_mesh,
        origin=Origin(xyz=(0.0, -1.090, 0.040)),
        material=cover_steel,
        name="front_ball_housing",
    )
    axle_housing.visual(
        Cylinder(radius=0.070, length=0.070),
        origin=Origin(xyz=(0.0, -1.180, 0.040), rpy=ALONG_Y),
        material=cover_steel,
        name="front_coupling_collar",
    )

    axle_housing.visual(
        Cylinder(radius=0.046, length=0.700),
        origin=Origin(xyz=(-0.355, 0.0, 0.0), rpy=SPIN_X),
        material=housing_cast,
        name="left_axle_tube",
    )
    axle_housing.visual(
        Cylinder(radius=0.046, length=0.700),
        origin=Origin(xyz=(0.355, 0.0, 0.0), rpy=SPIN_X),
        material=housing_cast,
        name="right_axle_tube",
    )
    axle_housing.visual(
        Cylinder(radius=0.062, length=0.104),
        origin=Origin(xyz=(-0.657, 0.0, 0.0), rpy=SPIN_X),
        material=cover_steel,
        name="left_bearing_barrel",
    )
    axle_housing.visual(
        Cylinder(radius=0.062, length=0.104),
        origin=Origin(xyz=(0.657, 0.0, 0.0), rpy=SPIN_X),
        material=cover_steel,
        name="right_bearing_barrel",
    )
    axle_housing.visual(
        Cylinder(radius=0.085, length=0.024),
        origin=Origin(xyz=(-0.717, 0.0, 0.0), rpy=SPIN_X),
        material=cover_steel,
        name="left_end_flange",
    )
    axle_housing.visual(
        Cylinder(radius=0.085, length=0.024),
        origin=Origin(xyz=(0.717, 0.0, 0.0), rpy=SPIN_X),
        material=cover_steel,
        name="right_end_flange",
    )

    cover_bolt_radius_x = 0.118
    cover_bolt_radius_z = 0.106
    for bolt_index in range(10):
        angle = (2.0 * pi * bolt_index) / 10.0
        axle_housing.visual(
            Cylinder(radius=0.010, length=0.016),
            origin=Origin(
                xyz=(
                    cos(angle) * cover_bolt_radius_x,
                    0.164,
                    sin(angle) * cover_bolt_radius_z,
                ),
                rpy=ALONG_Y,
            ),
            material=machined_steel,
            name=f"rear_cover_bolt_{bolt_index}",
        )
    axle_housing.visual(
        Cylinder(radius=0.013, length=0.018),
        origin=Origin(xyz=(0.0, 0.165, -0.120), rpy=ALONG_Y),
        material=machined_steel,
        name="drain_plug",
    )

    left_hub = model.part("left_hub")
    _add_hub_visuals(left_hub, -1.0, machined_steel, oily_steel)

    right_hub = model.part("right_hub")
    _add_hub_visuals(right_hub, 1.0, machined_steel, oily_steel)

    model.articulation(
        "left_hub_spin",
        ArticulationType.CONTINUOUS,
        parent=axle_housing,
        child=left_hub,
        origin=Origin(xyz=(-0.729, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=1200.0, velocity=35.0),
    )
    model.articulation(
        "right_hub_spin",
        ArticulationType.CONTINUOUS,
        parent=axle_housing,
        child=right_hub,
        origin=Origin(xyz=(0.729, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=1200.0, velocity=35.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
