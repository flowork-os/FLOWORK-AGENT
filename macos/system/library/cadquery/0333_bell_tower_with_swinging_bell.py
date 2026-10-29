# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bell_tower_with_swinging_bell, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bell_tower_with_swinging_bell

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

# ===== model =====
import math
def _triangular_gusset(width: float, height: float, thickness: float) -> MeshGeometry:
    """Right-triangular welded plate in local XZ, extruded through local Y."""
    y0 = -thickness / 2.0
    y1 = thickness / 2.0
    pts = [
        (0.0, y0, 0.0),
        (width, y0, 0.0),
        (0.0, y0, height),
        (0.0, y1, 0.0),
        (width, y1, 0.0),
        (0.0, y1, height),
    ]
    geom = MeshGeometry()
    for p in pts:
        geom.add_vertex(*p)
    # Back/front triangular faces and three rectangular edge faces.
    faces = [
        (0, 2, 1),
        (3, 4, 5),
        (0, 1, 4),
        (0, 4, 3),
        (1, 2, 5),
        (1, 5, 4),
        (2, 0, 3),
        (2, 3, 5),
    ]
    for face in faces:
        geom.add_face(*face)
    return geom
def _bell_shell(segments: int = 80) -> MeshGeometry:
    """A hollow lathed bronze bell: flared rim, waist, shoulder, and crown."""
    outer = [
        (0.335, -1.055),
        (0.350, -1.005),
        (0.318, -0.930),
        (0.280, -0.815),
        (0.232, -0.660),
        (0.182, -0.500),
        (0.138, -0.360),
    ]
    inner = [
        (0.270, -1.015),
        (0.262, -0.930),
        (0.236, -0.805),
        (0.198, -0.640),
        (0.150, -0.480),
        (0.075, -0.360),
    ]
    geom = MeshGeometry()

    def add_ring(radius: float, z: float) -> list[int]:
        ids: list[int] = []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            ids.append(geom.add_vertex(radius * math.cos(a), radius * math.sin(a), z))
        return ids

    def connect(a: list[int], b: list[int], *, reverse: bool = False) -> None:
        for i in range(segments):
            j = (i + 1) % segments
            if reverse:
                geom.add_face(a[i], b[j], a[j])
                geom.add_face(a[i], b[i], b[j])
            else:
                geom.add_face(a[i], a[j], b[j])
                geom.add_face(a[i], b[j], b[i])

    outer_rings = [add_ring(r, z) for r, z in outer]
    inner_rings = [add_ring(r, z) for r, z in inner]

    for low, high in zip(outer_rings[:-1], outer_rings[1:]):
        connect(low, high)
    for low, high in zip(inner_rings[:-1], inner_rings[1:]):
        connect(low, high, reverse=True)

    # Thick, rounded-looking mouth lip and a closed crown annulus; the center
    # remains open inside so the dark clapper is visible through the mouth.
    connect(outer_rings[0], inner_rings[0], reverse=True)
    connect(outer_rings[-1], inner_rings[-1])
    return geom
def _add_cylinder_between(part, name: str, p0, p1, radius: float, material: Material) -> None:
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length <= 0.0:
        return
    yaw = math.atan2(dy, dx)
    pitch = math.acos(max(-1.0, min(1.0, dz / length)))
    part.visual(
        Cylinder(radius, length),
        origin=Origin(
            xyz=((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0),
            rpy=(0.0, pitch, yaw),
        ),
        material=material,
        name=name,
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="welded_bell_tower")

    painted_steel = Material("blackened_welded_steel", rgba=(0.045, 0.050, 0.050, 1.0))
    edge_worn_steel = Material("worn_steel_edges", rgba=(0.18, 0.19, 0.18, 1.0))
    cast_iron = Material("dark_cast_yoke", rgba=(0.025, 0.027, 0.028, 1.0))
    bronze = Material("aged_bell_bronze", rgba=(0.78, 0.53, 0.22, 1.0))
    dark_bronze = Material("shadowed_bronze", rgba=(0.36, 0.24, 0.11, 1.0))

    frame = model.part("frame")

    # Square welded baseplate.
    frame.visual(
        Box((1.80, 1.80, 0.040)),
        origin=Origin(xyz=(0.0, 0.0, 0.020)),
        material=painted_steel,
        name="baseplate",
    )

    post_xy = 0.65
    post_bottom = 0.020
    post_top = 2.090
    post_len = post_top - post_bottom
    post_positions = [
        (-post_xy, -post_xy),
        (post_xy, -post_xy),
        (post_xy, post_xy),
        (-post_xy, post_xy),
    ]
    for idx, (x, y) in enumerate(post_positions):
        frame.visual(
            Cylinder(0.035, post_len),
            origin=Origin(xyz=(x, y, (post_top + post_bottom) / 2.0)),
            material=painted_steel,
            name=f"post_{idx}",
        )

    # Top perimeter tubes tie all four posts together.
    top_z = 2.100
    frame.visual(
        Box((1.42, 0.12, 0.12)),
        origin=Origin(xyz=(0.0, post_xy, top_z)),
        material=painted_steel,
        name="top_front_beam",
    )
    frame.visual(
        Box((1.42, 0.12, 0.12)),
        origin=Origin(xyz=(0.0, -post_xy, top_z)),
        material=painted_steel,
        name="top_rear_beam",
    )
    frame.visual(
        Box((0.12, 1.42, 0.12)),
        origin=Origin(xyz=(post_xy, 0.0, top_z)),
        material=painted_steel,
        name="top_side_beam_0",
    )
    frame.visual(
        Box((0.12, 1.42, 0.12)),
        origin=Origin(xyz=(-post_xy, 0.0, top_z)),
        material=painted_steel,
        name="top_side_beam_1",
    )

    # The central horizontal box-section crossbeam is modeled as a hollow
    # rectangular tube with visible web and flange thickness.
    beam_len = 1.58
    beam_depth = 0.16
    beam_height = 0.14
    wall = 0.018
    frame.visual(
        Box((beam_len, beam_depth, wall)),
        origin=Origin(xyz=(0.0, 0.0, top_z + beam_height / 2.0 - wall / 2.0)),
        material=painted_steel,
        name="crossbeam_top",
    )
    frame.visual(
        Box((beam_len, beam_depth, wall)),
        origin=Origin(xyz=(0.0, 0.0, top_z - beam_height / 2.0 + wall / 2.0)),
        material=painted_steel,
        name="crossbeam_bottom",
    )
    frame.visual(
        Box((beam_len, wall, beam_height)),
        origin=Origin(xyz=(0.0, beam_depth / 2.0 - wall / 2.0, top_z)),
        material=painted_steel,
        name="crossbeam_front_web",
    )
    frame.visual(
        Box((beam_len, wall, beam_height)),
        origin=Origin(xyz=(0.0, -beam_depth / 2.0 + wall / 2.0, top_z)),
        material=painted_steel,
        name="crossbeam_rear_web",
    )

    # X-bracing on all four tower faces, made from smaller round tube.
    brace_r = 0.018
    z_low = 0.135
    z_high = 1.925
    side_specs = [
        ((-post_xy, post_xy, z_low), (post_xy, post_xy, z_high), "front_brace_0"),
        ((post_xy, post_xy, z_low), (-post_xy, post_xy, z_high), "front_brace_1"),
        ((-post_xy, -post_xy, z_low), (post_xy, -post_xy, z_high), "rear_brace_0"),
        ((post_xy, -post_xy, z_low), (-post_xy, -post_xy, z_high), "rear_brace_1"),
        ((post_xy, -post_xy, z_low), (post_xy, post_xy, z_high), "side_brace_0"),
        ((post_xy, post_xy, z_low), (post_xy, -post_xy, z_high), "side_brace_1"),
        ((-post_xy, -post_xy, z_low), (-post_xy, post_xy, z_high), "side_brace_2"),
        ((-post_xy, post_xy, z_low), (-post_xy, -post_xy, z_high), "side_brace_3"),
    ]
    for p0, p1, name in side_specs:
        _add_cylinder_between(frame, name, p0, p1, brace_r, painted_steel)

    # Visible triangular gusset plates at the post bases and under the top frame.
    base_gusset = _triangular_gusset(0.18, 0.22, 0.012)
    top_gusset = _triangular_gusset(0.16, 0.20, 0.012)
    for idx, (x, y) in enumerate(post_positions):
        yaw = math.atan2(-y, -x)
        frame.visual(
            mesh_from_geometry(base_gusset, f"base_gusset_mesh_{idx}"),
            origin=Origin(xyz=(x, y, 0.035), rpy=(0.0, 0.0, yaw)),
            material=edge_worn_steel,
            name=f"base_gusset_{idx}",
        )
        frame.visual(
            mesh_from_geometry(top_gusset, f"top_gusset_mesh_{idx}"),
            origin=Origin(xyz=(x, y, 2.105), rpy=(math.pi, 0.0, yaw)),
            material=edge_worn_steel,
            name=f"top_gusset_{idx}",
        )

    # Bearing hanger plates and the through-bolt that carries the swinging yoke.
    pivot_z = 1.740
    for idx, x in enumerate((-0.55, 0.55)):
        frame.visual(
            Box((0.035, 0.22, 0.50)),
            origin=Origin(xyz=(x, 0.0, 1.865)),
            material=painted_steel,
            name=f"bearing_plate_{idx}",
        )
    frame.visual(
        Cylinder(0.018, 1.16),
        origin=Origin(xyz=(0.0, 0.0, pivot_z), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=edge_worn_steel,
        name="pivot_bolt",
    )
    frame.visual(
        Cylinder(0.040, 0.040),
        origin=Origin(xyz=(-0.595, 0.0, pivot_z), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=edge_worn_steel,
        name="bolt_head_0",
    )
    frame.visual(
        Cylinder(0.040, 0.040),
        origin=Origin(xyz=(0.595, 0.0, pivot_z), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=edge_worn_steel,
        name="bolt_head_1",
    )

    bell = model.part("bell")
    bell.visual(
        mesh_from_geometry(_bell_shell(), "bell_body_mesh"),
        origin=Origin(),
        material=bronze,
        name="bell_body",
    )
    bell.visual(
        Cylinder(0.112, 0.120),
        origin=Origin(xyz=(0.0, 0.0, -0.390)),
        material=dark_bronze,
        name="crown_saddle",
    )
    bell.visual(
        Box((0.80, 0.14, 0.080)),
        origin=Origin(xyz=(0.0, 0.0, -0.335)),
        material=cast_iron,
        name="yoke_bar",
    )
    for idx, x in enumerate((-0.38, 0.38)):
        bell.visual(
            Cylinder(0.060, 0.120),
            origin=Origin(xyz=(x, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=cast_iron,
            name=f"hub_{idx}",
        )
        bell.visual(
            Box((0.060, 0.115, 0.340)),
            origin=Origin(xyz=(x, 0.0, -0.200)),
            material=cast_iron,
            name=f"yoke_arm_{idx}",
        )
    bell.visual(
        Cylinder(0.010, 0.570),
        origin=Origin(xyz=(0.0, 0.0, -0.655)),
        material=cast_iron,
        name="clapper_stem",
    )
    bell.visual(
        Sphere(0.055),
        origin=Origin(xyz=(0.0, 0.0, -0.965)),
        material=cast_iron,
        name="clapper_ball",
    )

    model.articulation(
        "bell_pivot",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=bell,
        origin=Origin(xyz=(0.0, 0.0, pivot_z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=120.0, velocity=1.5, lower=-0.28, upper=0.28),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
