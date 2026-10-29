# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cannon, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cannon

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
class TorusGeometry(MeshGeometry):
    def __init__(self, radius, tube, *, radial_segments=16, tubular_segments=32):
        super().__init__()
        radius = float(radius)
        tube = float(tube)
        # ring radius `radius` in XY plane, tube radius `tube`, centered at origin
        solid = cq.Solid.makeTorus(radius, tube, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
        self._set(solid)

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
from math import cos, pi, sin
def _mesh(name: str, geometry):
    return mesh_from_geometry(geometry, name)
def _add_spoked_wheel(
    part,
    mesh_prefix: str,
    *,
    tire_major_radius: float,
    tire_tube_radius: float,
    rim_major_radius: float,
    rim_tube_radius: float,
    hub_radius: float,
    hub_width: float,
    spoke_count: int,
    tire_material,
    wheel_material,
    metal_material,
) -> None:
    tire_mesh = _mesh(
        f"{mesh_prefix}_tire",
        TorusGeometry(
            radius=tire_major_radius,
            tube=tire_tube_radius,
            radial_segments=18,
            tubular_segments=72,
        ).rotate_y(pi / 2.0),
    )
    rim_mesh = _mesh(
        f"{mesh_prefix}_rim",
        TorusGeometry(
            radius=rim_major_radius,
            tube=rim_tube_radius,
            radial_segments=16,
            tubular_segments=72,
        ).rotate_y(pi / 2.0),
    )

    part.visual(tire_mesh, material=tire_material, name="tire")
    part.visual(rim_mesh, material=wheel_material, name="rim")
    part.visual(
        Cylinder(radius=hub_radius, length=hub_width),
        origin=Origin(rpy=(0.0, pi / 2.0, 0.0)),
        material=wheel_material,
        name="hub",
    )
    part.visual(
        Cylinder(radius=hub_radius * 1.45, length=0.018),
        origin=Origin(xyz=(hub_width * 0.18, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material=wheel_material,
        name="inner_flange",
    )
    part.visual(
        Cylinder(radius=hub_radius * 1.45, length=0.018),
        origin=Origin(xyz=(-hub_width * 0.18, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material=wheel_material,
        name="outer_flange",
    )
    part.visual(
        Cylinder(radius=hub_radius * 0.32, length=hub_width * 0.92),
        origin=Origin(rpy=(0.0, pi / 2.0, 0.0)),
        material=metal_material,
        name="axle_bore_cap",
    )

    spoke_length = rim_major_radius - hub_radius * 1.20
    spoke_mid_radius = hub_radius * 1.20 + spoke_length * 0.5
    for spoke_index in range(spoke_count):
        angle = 2.0 * pi * spoke_index / spoke_count
        part.visual(
            Box((hub_width * 0.46, 0.022, spoke_length)),
            origin=Origin(
                xyz=(0.0, spoke_mid_radius * cos(angle), spoke_mid_radius * sin(angle)),
                rpy=(angle - pi / 2.0, 0.0, 0.0),
            ),
            material=wheel_material,
            name=f"spoke_{spoke_index:02d}",
        )
def _add_trail_leg(
    part,
    *,
    side_sign: float,
    trail_material,
    metal_material,
) -> None:
    part.visual(
        Cylinder(radius=0.055, length=0.12),
        origin=Origin(),
        material=metal_material,
        name="hinge_knuckle",
    )
    part.visual(
        Box((0.10, 0.18, 0.12)),
        origin=Origin(xyz=(0.0, -0.11, -0.01)),
        material=trail_material,
        name="junction_block",
    )
    part.visual(
        Box((0.09, 1.00, 0.08)),
        origin=Origin(xyz=(0.0, -0.62, -0.10), rpy=(0.10, 0.0, 0.0)),
        material=trail_material,
        name="main_beam",
    )
    part.visual(
        Box((0.06, 0.42, 0.05)),
        origin=Origin(xyz=(0.0, -0.34, 0.03), rpy=(0.18, 0.0, 0.0)),
        material=trail_material,
        name="upper_brace",
    )
    part.visual(
        Box((0.16, 0.10, 0.16)),
        origin=Origin(xyz=(0.0, -1.12, -0.22), rpy=(0.22, 0.0, 0.0)),
        material=metal_material,
        name="spade",
    )
    part.visual(
        Cylinder(radius=0.016, length=0.18),
        origin=Origin(
            xyz=(0.0, -1.02, -0.12),
            rpy=(0.0, pi / 2.0, 0.0),
        ),
        material=metal_material,
        name="handspike",
    )
    part.visual(
        Box((0.08, 0.24, 0.08)),
        origin=Origin(xyz=(0.0, -0.98, -0.17), rpy=(0.20, 0.0, 0.0)),
        material=trail_material,
        name="tail_bridge",
    )
    part.visual(
        Box((0.02, 0.16, 0.08)),
        origin=Origin(xyz=(0.018 * side_sign, -0.22, 0.01), rpy=(0.18, 0.0, 0.0)),
        material=metal_material,
        name="brace_lug",
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="mountain_pack_howitzer")

    olive_drab = model.material("olive_drab", rgba=(0.37, 0.40, 0.27, 1.0))
    dark_olive = model.material("dark_olive", rgba=(0.24, 0.27, 0.18, 1.0))
    gunmetal = model.material("gunmetal", rgba=(0.34, 0.36, 0.39, 1.0))
    steel = model.material("steel", rgba=(0.60, 0.62, 0.65, 1.0))
    tire_black = model.material("tire_black", rgba=(0.07, 0.07, 0.07, 1.0))

    carriage = model.part("carriage")
    carriage.inertial = Inertial.from_geometry(
        Box((1.55, 0.95, 0.90)),
        mass=540.0,
        origin=Origin(xyz=(0.0, -0.10, 0.45)),
    )
    carriage.visual(
        Cylinder(radius=0.050, length=1.26),
        origin=Origin(xyz=(0.0, 0.0, 0.46), rpy=(0.0, pi / 2.0, 0.0)),
        material=gunmetal,
        name="axle_beam",
    )
    carriage.visual(
        Cylinder(radius=0.062, length=0.042),
        origin=Origin(xyz=(0.63, 0.0, 0.46), rpy=(0.0, pi / 2.0, 0.0)),
        material=steel,
        name="left_spindle_stub",
    )
    carriage.visual(
        Cylinder(radius=0.062, length=0.042),
        origin=Origin(xyz=(-0.63, 0.0, 0.46), rpy=(0.0, pi / 2.0, 0.0)),
        material=steel,
        name="right_spindle_stub",
    )
    carriage.visual(
        Box((0.38, 0.24, 0.16)),
        origin=Origin(xyz=(0.0, -0.01, 0.44)),
        material=olive_drab,
        name="center_bed",
    )
    carriage.visual(
        Box((0.20, 0.12, 0.08)),
        origin=Origin(xyz=(0.0, 0.05, 0.56)),
        material=olive_drab,
        name="center_arch",
    )
    carriage.visual(
        Box((0.06, 0.24, 0.18)),
        origin=Origin(xyz=(0.0, -0.29, 0.31)),
        material=olive_drab,
        name="trail_junction",
    )
    carriage.visual(
        Box((0.14, 0.22, 0.08)),
        origin=Origin(xyz=(0.0, -0.19, 0.34), rpy=(-0.18, 0.0, 0.0)),
        material=olive_drab,
        name="drag_beam",
    )
    carriage.visual(
        Box((0.045, 0.28, 0.11)),
        origin=Origin(xyz=(0.195, 0.11, 0.57), rpy=(0.42, 0.0, 0.0)),
        material=olive_drab,
        name="left_cradle_brace",
    )
    carriage.visual(
        Box((0.045, 0.28, 0.11)),
        origin=Origin(xyz=(-0.195, 0.11, 0.57), rpy=(0.42, 0.0, 0.0)),
        material=olive_drab,
        name="right_cradle_brace",
    )
    carriage.visual(
        Box((0.06, 0.24, 0.18)),
        origin=Origin(xyz=(0.17, 0.22, 0.72)),
        material=olive_drab,
        name="left_cradle_cheek",
    )
    carriage.visual(
        Box((0.06, 0.24, 0.18)),
        origin=Origin(xyz=(-0.17, 0.22, 0.72)),
        material=olive_drab,
        name="right_cradle_cheek",
    )
    carriage.visual(
        Box((0.031, 0.22, 0.14)),
        origin=Origin(xyz=(0.0195, -0.31, 0.28)),
        material=gunmetal,
        name="left_trail_inner_cheek",
    )
    carriage.visual(
        Box((0.031, 0.22, 0.14)),
        origin=Origin(xyz=(0.1605, -0.31, 0.28)),
        material=gunmetal,
        name="left_trail_outer_cheek",
    )
    carriage.visual(
        Box((0.126, 0.10, 0.04)),
        origin=Origin(xyz=(0.090, -0.24, 0.35)),
        material=gunmetal,
        name="left_trail_bridge",
    )
    carriage.visual(
        Box((0.031, 0.22, 0.14)),
        origin=Origin(xyz=(-0.0195, -0.31, 0.28)),
        material=gunmetal,
        name="right_trail_inner_cheek",
    )
    carriage.visual(
        Box((0.031, 0.22, 0.14)),
        origin=Origin(xyz=(-0.1605, -0.31, 0.28)),
        material=gunmetal,
        name="right_trail_outer_cheek",
    )
    carriage.visual(
        Box((0.126, 0.10, 0.04)),
        origin=Origin(xyz=(-0.090, -0.24, 0.35)),
        material=gunmetal,
        name="right_trail_bridge",
    )
    barrel = model.part("barrel")
    barrel.inertial = Inertial.from_geometry(
        Box((0.28, 1.38, 0.28)),
        mass=235.0,
        origin=Origin(xyz=(0.0, 0.40, 0.0)),
    )
    barrel.visual(
        Cylinder(radius=0.055, length=0.28),
        origin=Origin(rpy=(0.0, pi / 2.0, 0.0)),
        material=gunmetal,
        name="trunnion_shaft",
    )
    barrel.visual(
        Box((0.20, 0.20, 0.18)),
        origin=Origin(xyz=(0.0, -0.14, 0.0)),
        material=dark_olive,
        name="breech_block",
    )
    barrel.visual(
        Box((0.14, 0.08, 0.16)),
        origin=Origin(xyz=(0.0, -0.26, 0.0)),
        material=gunmetal,
        name="breech_wedge",
    )
    barrel.visual(
        Cylinder(radius=0.095, length=0.40),
        origin=Origin(xyz=(0.0, 0.14, 0.0), rpy=(pi / 2.0, 0.0, 0.0)),
        material=olive_drab,
        name="recoil_sleeve",
    )
    barrel.visual(
        Cylinder(radius=0.050, length=0.84),
        origin=Origin(xyz=(0.0, 0.56, 0.0), rpy=(pi / 2.0, 0.0, 0.0)),
        material=gunmetal,
        name="tube",
    )
    barrel.visual(
        Cylinder(radius=0.060, length=0.12),
        origin=Origin(xyz=(0.0, 1.04, 0.0), rpy=(pi / 2.0, 0.0, 0.0)),
        material=gunmetal,
        name="muzzle_reinforce",
    )
    barrel.visual(
        Cylinder(radius=0.040, length=0.36),
        origin=Origin(xyz=(0.0, 0.18, -0.10), rpy=(pi / 2.0, 0.0, 0.0)),
        material=olive_drab,
        name="recuperator",
    )
    barrel.visual(
        Box((0.05, 0.12, 0.10)),
        origin=Origin(xyz=(0.10, -0.02, 0.10)),
        material=dark_olive,
        name="sight_block",
    )

    left_trail = model.part("left_trail")
    left_trail.inertial = Inertial.from_geometry(
        Box((0.18, 1.34, 0.34)),
        mass=78.0,
        origin=Origin(xyz=(0.0, -0.64, -0.08)),
    )
    _add_trail_leg(
        left_trail,
        side_sign=1.0,
        trail_material=olive_drab,
        metal_material=gunmetal,
    )

    right_trail = model.part("right_trail")
    right_trail.inertial = Inertial.from_geometry(
        Box((0.18, 1.34, 0.34)),
        mass=78.0,
        origin=Origin(xyz=(0.0, -0.64, -0.08)),
    )
    _add_trail_leg(
        right_trail,
        side_sign=-1.0,
        trail_material=olive_drab,
        metal_material=gunmetal,
    )

    left_wheel = model.part("left_wheel")
    left_wheel.inertial = Inertial.from_geometry(
        Cylinder(radius=0.46, length=0.11),
        mass=48.0,
        origin=Origin(rpy=(0.0, pi / 2.0, 0.0)),
    )
    _add_spoked_wheel(
        left_wheel,
        "left_wheel",
        tire_major_radius=0.38,
        tire_tube_radius=0.050,
        rim_major_radius=0.33,
        rim_tube_radius=0.020,
        hub_radius=0.072,
        hub_width=0.11,
        spoke_count=12,
        tire_material=tire_black,
        wheel_material=olive_drab,
        metal_material=steel,
    )

    right_wheel = model.part("right_wheel")
    right_wheel.inertial = Inertial.from_geometry(
        Cylinder(radius=0.46, length=0.11),
        mass=48.0,
        origin=Origin(rpy=(0.0, pi / 2.0, 0.0)),
    )
    _add_spoked_wheel(
        right_wheel,
        "right_wheel",
        tire_major_radius=0.38,
        tire_tube_radius=0.050,
        rim_major_radius=0.33,
        rim_tube_radius=0.020,
        hub_radius=0.072,
        hub_width=0.11,
        spoke_count=12,
        tire_material=tire_black,
        wheel_material=olive_drab,
        metal_material=steel,
    )

    model.articulation(
        "barrel_elevation",
        ArticulationType.REVOLUTE,
        parent=carriage,
        child=barrel,
        origin=Origin(xyz=(0.0, 0.24, 0.71)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=2200.0,
            velocity=0.9,
            lower=-0.10,
            upper=0.92,
        ),
    )
    model.articulation(
        "left_trail_spread",
        ArticulationType.REVOLUTE,
        parent=carriage,
        child=left_trail,
        origin=Origin(xyz=(0.09, -0.40, 0.28)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=1600.0,
            velocity=0.8,
            lower=0.0,
            upper=0.62,
        ),
    )
    model.articulation(
        "right_trail_spread",
        ArticulationType.REVOLUTE,
        parent=carriage,
        child=right_trail,
        origin=Origin(xyz=(-0.09, -0.40, 0.28)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=1600.0,
            velocity=0.8,
            lower=0.0,
            upper=0.62,
        ),
    )
    model.articulation(
        "left_wheel_spin",
        ArticulationType.CONTINUOUS,
        parent=carriage,
        child=left_wheel,
        origin=Origin(xyz=(0.706, 0.0, 0.46)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=320.0, velocity=18.0),
    )
    model.articulation(
        "right_wheel_spin",
        ArticulationType.CONTINUOUS,
        parent=carriage,
        child=right_wheel,
        origin=Origin(xyz=(-0.706, 0.0, 0.46)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=320.0, velocity=18.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
