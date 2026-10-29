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

class Sphere:
    __slots__ = ("radius",)

    def __init__(self, radius):
        self.radius = float(radius)

    def _cq(self):
        return cq.Solid.makeSphere(self.radius, angleDegrees1=-90, angleDegrees2=90,
                                   angleDegrees3=360)

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

# ===== brackets_hinges_bezels (1 syms) =====
def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

# ===== model =====
import math
def _normalize(vec: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)
    if length <= 1e-9:
        return (1.0, 0.0, 0.0)
    return (vec[0] / length, vec[1] / length, vec[2] / length)
def _cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )
def _curved_hollow_tube_mesh(
    path_points: list[tuple[float, float, float]],
    outer_radii: list[float],
    inner_radii: list[float],
    *,
    radial_segments: int = 40,
) -> MeshGeometry:
    geom = MeshGeometry()
    outer_rings: list[list[int]] = []
    inner_rings: list[list[int]] = []
    y_axis = (0.0, 1.0, 0.0)

    for index, point in enumerate(path_points):
        prev_pt = path_points[index - 1] if index > 0 else path_points[index]
        next_pt = path_points[index + 1] if index < len(path_points) - 1 else path_points[index]
        tangent = _normalize(
            (
                next_pt[0] - prev_pt[0],
                next_pt[1] - prev_pt[1],
                next_pt[2] - prev_pt[2],
            )
        )
        xz_normal = _normalize(_cross(y_axis, tangent))
        outer_ring: list[int] = []
        inner_ring: list[int] = []
        for seg in range(radial_segments):
            angle = 2.0 * math.pi * seg / radial_segments
            c = math.cos(angle)
            s = math.sin(angle)
            direction = (
                y_axis[0] * c + xz_normal[0] * s,
                y_axis[1] * c + xz_normal[1] * s,
                y_axis[2] * c + xz_normal[2] * s,
            )
            outer_ring.append(
                geom.add_vertex(
                    point[0] + direction[0] * outer_radii[index],
                    point[1] + direction[1] * outer_radii[index],
                    point[2] + direction[2] * outer_radii[index],
                )
            )
            inner_ring.append(
                geom.add_vertex(
                    point[0] + direction[0] * inner_radii[index],
                    point[1] + direction[1] * inner_radii[index],
                    point[2] + direction[2] * inner_radii[index],
                )
            )
        outer_rings.append(outer_ring)
        inner_rings.append(inner_ring)

    for ring_index in range(len(path_points) - 1):
        outer_a = outer_rings[ring_index]
        outer_b = outer_rings[ring_index + 1]
        inner_a = inner_rings[ring_index]
        inner_b = inner_rings[ring_index + 1]
        for seg in range(radial_segments):
            nxt = (seg + 1) % radial_segments

            geom.add_face(outer_a[seg], outer_a[nxt], outer_b[nxt])
            geom.add_face(outer_a[seg], outer_b[nxt], outer_b[seg])

            geom.add_face(inner_a[seg], inner_b[seg], inner_b[nxt])
            geom.add_face(inner_a[seg], inner_b[nxt], inner_a[nxt])

    start_outer = outer_rings[0]
    start_inner = inner_rings[0]
    end_outer = outer_rings[-1]
    end_inner = inner_rings[-1]
    for seg in range(radial_segments):
        nxt = (seg + 1) % radial_segments

        geom.add_face(start_outer[seg], start_inner[nxt], start_outer[nxt])
        geom.add_face(start_outer[seg], start_inner[seg], start_inner[nxt])

        geom.add_face(end_outer[seg], end_outer[nxt], end_inner[nxt])
        geom.add_face(end_outer[seg], end_inner[nxt], end_inner[seg])

    return geom
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="de_dion_rear_axle")

    chassis_black = model.material("chassis_black", rgba=(0.13, 0.13, 0.14, 1.0))
    painted_steel = model.material("painted_steel", rgba=(0.20, 0.21, 0.23, 1.0))
    machined_steel = model.material("machined_steel", rgba=(0.68, 0.70, 0.73, 1.0))
    dark_steel = model.material("dark_steel", rgba=(0.34, 0.35, 0.38, 1.0))
    rubber = model.material("rubber", rgba=(0.08, 0.08, 0.09, 1.0))

    chassis_mount = model.part("chassis_mount")
    chassis_mount.visual(
        Box((1.02, 0.16, 0.08)),
        origin=Origin(xyz=(0.0, 0.0, 0.39)),
        material=chassis_black,
        name="elem_crossmember",
    )
    chassis_mount.visual(
        Box((0.54, 0.14, 0.12)),
        origin=Origin(xyz=(0.0, 0.0, 0.29)),
        material=painted_steel,
        name="elem_subframe_bridge",
    )
    chassis_mount.visual(
        Sphere(radius=0.078),
        origin=Origin(xyz=(0.0, 0.0, 0.304)),
        material=dark_steel,
        name="elem_differential_housing",
    )
    chassis_mount.visual(
        Cylinder(radius=0.040, length=0.11),
        origin=Origin(xyz=(0.0, 0.072, 0.302), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_steel,
        name="elem_pinion_nose",
    )
    chassis_mount.visual(
        Box((0.08, 0.06, 0.16)),
        origin=Origin(xyz=(-0.28, 0.0, 0.29)),
        material=painted_steel,
        name="elem_left_drop_link",
    )
    chassis_mount.visual(
        Box((0.08, 0.06, 0.16)),
        origin=Origin(xyz=(0.28, 0.0, 0.29)),
        material=painted_steel,
        name="elem_right_drop_link",
    )
    chassis_mount.inertial = Inertial.from_geometry(
        Box((1.10, 0.24, 0.42)),
        mass=62.0,
        origin=Origin(xyz=(0.0, 0.0, 0.24)),
    )

    de_dion_tube = model.part("de_dion_tube")
    tube_path = [
        (-0.78, 0.0, 0.130),
        (-0.66, 0.0, 0.130),
        (-0.48, 0.0, 0.132),
        (-0.24, 0.0, 0.138),
        (0.00, 0.0, 0.143),
        (0.24, 0.0, 0.138),
        (0.48, 0.0, 0.132),
        (0.66, 0.0, 0.130),
        (0.78, 0.0, 0.130),
    ]
    tube_outer = [0.073, 0.066, 0.052, 0.050, 0.051, 0.050, 0.052, 0.066, 0.073]
    tube_inner = [0.043, 0.041, 0.040, 0.040, 0.040, 0.040, 0.040, 0.041, 0.043]
    axle_shell = mesh_from_geometry(
        _curved_hollow_tube_mesh(tube_path, tube_outer, tube_inner, radial_segments=42),
        "de_dion_axle_shell",
    )
    de_dion_tube.visual(
        axle_shell,
        material=painted_steel,
        name="elem_axle_shell",
    )
    de_dion_tube.visual(
        Box((0.09, 0.07, 0.028)),
        origin=Origin(xyz=(-0.28, 0.0, 0.196)),
        material=painted_steel,
        name="elem_left_saddle",
    )
    de_dion_tube.visual(
        Box((0.09, 0.07, 0.028)),
        origin=Origin(xyz=(0.28, 0.0, 0.196)),
        material=painted_steel,
        name="elem_right_saddle",
    )
    de_dion_tube.visual(
        Box((0.16, 0.08, 0.030)),
        origin=Origin(xyz=(0.0, 0.0, 0.182)),
        material=painted_steel,
        name="elem_center_bridge",
    )
    de_dion_tube.inertial = Inertial.from_geometry(
        Box((1.66, 0.18, 0.16)),
        mass=38.0,
        origin=Origin(xyz=(0.0, 0.0, 0.145)),
    )

    left_half_shaft = model.part("left_half_shaft")
    left_half_shaft.visual(
        Sphere(radius=0.024),
        material=rubber,
        name="elem_inner_cv",
    )
    left_half_shaft.visual(
        Cylinder(radius=0.021, length=0.060),
        origin=Origin(xyz=(-0.030, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_steel,
        name="elem_inner_tulip",
    )
    left_half_shaft.visual(
        Cylinder(radius=0.014, length=0.600),
        origin=Origin(xyz=(-0.260, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=machined_steel,
        name="elem_shaft_core",
    )
    left_half_shaft.visual(
        Sphere(radius=0.026),
        origin=Origin(xyz=(-0.520, 0.0, 0.0)),
        material=rubber,
        name="elem_outer_cv",
    )
    left_half_shaft.visual(
        Cylinder(radius=0.022, length=0.060),
        origin=Origin(xyz=(-0.550, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_steel,
        name="elem_outer_tulip",
    )
    left_half_shaft.visual(
        Cylinder(radius=0.016, length=0.060),
        origin=Origin(xyz=(-0.610, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=machined_steel,
        name="elem_outer_stub",
    )
    left_half_shaft.inertial = Inertial.from_geometry(
        Box((0.77, 0.07, 0.07)),
        mass=8.0,
        origin=Origin(xyz=(-0.36, 0.0, 0.0)),
    )

    right_half_shaft = model.part("right_half_shaft")
    right_half_shaft.visual(
        Sphere(radius=0.024),
        material=rubber,
        name="elem_inner_cv",
    )
    right_half_shaft.visual(
        Cylinder(radius=0.021, length=0.060),
        origin=Origin(xyz=(0.030, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_steel,
        name="elem_inner_tulip",
    )
    right_half_shaft.visual(
        Cylinder(radius=0.014, length=0.600),
        origin=Origin(xyz=(0.260, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=machined_steel,
        name="elem_shaft_core",
    )
    right_half_shaft.visual(
        Sphere(radius=0.026),
        origin=Origin(xyz=(0.520, 0.0, 0.0)),
        material=rubber,
        name="elem_outer_cv",
    )
    right_half_shaft.visual(
        Cylinder(radius=0.022, length=0.060),
        origin=Origin(xyz=(0.550, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_steel,
        name="elem_outer_tulip",
    )
    right_half_shaft.visual(
        Cylinder(radius=0.016, length=0.060),
        origin=Origin(xyz=(0.610, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=machined_steel,
        name="elem_outer_stub",
    )
    right_half_shaft.inertial = Inertial.from_geometry(
        Box((0.77, 0.07, 0.07)),
        mass=8.0,
        origin=Origin(xyz=(0.36, 0.0, 0.0)),
    )

    left_hub = model.part("left_hub")
    left_hub.visual(
        Cylinder(radius=0.028, length=0.050),
        origin=Origin(xyz=(-0.025, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=machined_steel,
        name="elem_hub_journal",
    )
    left_hub.visual(
        Cylinder(radius=0.062, length=0.016),
        origin=Origin(xyz=(-0.008, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_steel,
        name="elem_bearing_land",
    )
    left_hub.visual(
        Cylinder(radius=0.058, length=0.018),
        origin=Origin(xyz=(-0.059, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_steel,
        name="elem_hub_barrel",
    )
    left_hub.visual(
        Cylinder(radius=0.082, length=0.012),
        origin=Origin(xyz=(-0.074, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=machined_steel,
        name="elem_hub_flange",
    )
    left_hub.visual(
        Sphere(radius=0.024),
        origin=Origin(xyz=(-0.096, 0.0, 0.0)),
        material=dark_steel,
        name="elem_hub_cap",
    )
    left_hub.inertial = Inertial.from_geometry(
        Box((0.13, 0.17, 0.17)),
        mass=6.0,
        origin=Origin(xyz=(-0.050, 0.0, 0.0)),
    )

    right_hub = model.part("right_hub")
    right_hub.visual(
        Cylinder(radius=0.028, length=0.050),
        origin=Origin(xyz=(0.025, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=machined_steel,
        name="elem_hub_journal",
    )
    right_hub.visual(
        Cylinder(radius=0.062, length=0.016),
        origin=Origin(xyz=(0.008, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_steel,
        name="elem_bearing_land",
    )
    right_hub.visual(
        Cylinder(radius=0.058, length=0.018),
        origin=Origin(xyz=(0.059, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_steel,
        name="elem_hub_barrel",
    )
    right_hub.visual(
        Cylinder(radius=0.082, length=0.012),
        origin=Origin(xyz=(0.074, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=machined_steel,
        name="elem_hub_flange",
    )
    right_hub.visual(
        Sphere(radius=0.024),
        origin=Origin(xyz=(0.096, 0.0, 0.0)),
        material=dark_steel,
        name="elem_hub_cap",
    )
    right_hub.inertial = Inertial.from_geometry(
        Box((0.13, 0.17, 0.17)),
        mass=6.0,
        origin=Origin(xyz=(0.050, 0.0, 0.0)),
    )

    model.articulation(
        "chassis_to_axle",
        ArticulationType.FIXED,
        parent=chassis_mount,
        child=de_dion_tube,
        origin=Origin(),
    )
    model.articulation(
        "left_half_shaft_spin",
        ArticulationType.CONTINUOUS,
        parent=de_dion_tube,
        child=left_half_shaft,
        origin=Origin(xyz=(-0.140, 0.0, 0.130)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=450.0, velocity=60.0),
    )
    model.articulation(
        "right_half_shaft_spin",
        ArticulationType.CONTINUOUS,
        parent=de_dion_tube,
        child=right_half_shaft,
        origin=Origin(xyz=(0.140, 0.0, 0.130)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=450.0, velocity=60.0),
    )
    model.articulation(
        "left_hub_spin",
        ArticulationType.CONTINUOUS,
        parent=de_dion_tube,
        child=left_hub,
        origin=Origin(xyz=(-0.780, 0.0, 0.130)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=300.0, velocity=80.0),
    )
    model.articulation(
        "right_hub_spin",
        ArticulationType.CONTINUOUS,
        parent=de_dion_tube,
        child=right_hub,
        origin=Origin(xyz=(0.780, 0.0, 0.130)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=300.0, velocity=80.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
