# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bicycle_crankset_and_pedal_assembly, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bicycle_crankset_and_pedal_assembly

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
def _add_quad(mesh: MeshGeometry, a: int, b: int, c: int, d: int) -> None:
    mesh.add_face(a, b, c)
    mesh.add_face(a, c, d)
def _stepped_tube_x(
    stations: list[tuple[float, float]],
    inner_radius: float,
    *,
    segments: int = 72,
) -> MeshGeometry:
    """Hollow tube with varying outside radius, aligned to global X."""
    mesh = MeshGeometry()
    outer: list[list[int]] = []
    inner: list[list[int]] = []
    for x, outer_radius in stations:
        outer_ring: list[int] = []
        inner_ring: list[int] = []
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            y = math.cos(angle)
            z = math.sin(angle)
            outer_ring.append(mesh.add_vertex(x, outer_radius * y, outer_radius * z))
            inner_ring.append(mesh.add_vertex(x, inner_radius * y, inner_radius * z))
        outer.append(outer_ring)
        inner.append(inner_ring)

    for ring in range(len(stations) - 1):
        for i in range(segments):
            j = (i + 1) % segments
            _add_quad(mesh, outer[ring][i], outer[ring + 1][i], outer[ring + 1][j], outer[ring][j])
            _add_quad(mesh, inner[ring][j], inner[ring + 1][j], inner[ring + 1][i], inner[ring][i])

    first = 0
    last = len(stations) - 1
    for i in range(segments):
        j = (i + 1) % segments
        _add_quad(mesh, outer[first][j], outer[first][i], inner[first][i], inner[first][j])
        _add_quad(mesh, outer[last][i], outer[last][j], inner[last][j], inner[last][i])
    return mesh
def _annular_disk_x(
    thickness: float,
    outer_radius: float,
    inner_radius: float,
    *,
    segments: int = 96,
    tooth_count: int | None = None,
    tooth_depth: float = 0.0,
) -> MeshGeometry:
    """Flat annulus in the YZ plane, with optional small radial teeth."""
    mesh = MeshGeometry()
    x_values = (-thickness / 2.0, thickness / 2.0)
    outer: list[list[int]] = []
    inner: list[list[int]] = []
    for x in x_values:
        outer_ring: list[int] = []
        inner_ring: list[int] = []
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            radius = outer_radius
            if tooth_count:
                # Alternate every half-tooth so the perimeter reads as a real chainring.
                phase = (angle * tooth_count / (2.0 * math.pi)) % 1.0
                crown = 1.0 - abs(phase - 0.5) * 2.0
                radius += tooth_depth * max(0.0, crown)
            y = math.cos(angle)
            z = math.sin(angle)
            outer_ring.append(mesh.add_vertex(x, radius * y, radius * z))
            inner_ring.append(mesh.add_vertex(x, inner_radius * y, inner_radius * z))
        outer.append(outer_ring)
        inner.append(inner_ring)

    for i in range(segments):
        j = (i + 1) % segments
        _add_quad(mesh, outer[0][i], outer[1][i], outer[1][j], outer[0][j])
        _add_quad(mesh, inner[0][j], inner[1][j], inner[1][i], inner[0][i])
        _add_quad(mesh, outer[1][i], inner[1][i], inner[1][j], outer[1][j])
        _add_quad(mesh, outer[0][j], inner[0][j], inner[0][i], outer[0][i])
    return mesh
def _solid_cylinder_x(length: float, radius: float, *, segments: int = 72) -> MeshGeometry:
    mesh = MeshGeometry()
    xs = (-length / 2.0, length / 2.0)
    rings: list[list[int]] = []
    for x in xs:
        ring: list[int] = []
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            ring.append(mesh.add_vertex(x, radius * math.cos(angle), radius * math.sin(angle)))
        rings.append(ring)
    for i in range(segments):
        j = (i + 1) % segments
        _add_quad(mesh, rings[0][i], rings[1][i], rings[1][j], rings[0][j])
    c0 = mesh.add_vertex(xs[0], 0.0, 0.0)
    c1 = mesh.add_vertex(xs[1], 0.0, 0.0)
    for i in range(segments):
        j = (i + 1) % segments
        mesh.add_face(c1, rings[1][i], rings[1][j])
        mesh.add_face(c0, rings[0][j], rings[0][i])
    return mesh
def _capsule_prism_x(
    p0_yz: tuple[float, float],
    p1_yz: tuple[float, float],
    width: float,
    thickness: float,
    *,
    x_center: float = 0.0,
    arc_segments: int = 12,
) -> MeshGeometry:
    """Rounded-end bar between two YZ points, extruded along X."""
    y0, z0 = p0_yz
    y1, z1 = p1_yz
    dy = y1 - y0
    dz = z1 - z0
    length = math.hypot(dy, dz)
    if length <= 1e-9:
        raise ValueError("capsule endpoints must be distinct")
    theta = math.atan2(dz, dy)
    radius = width / 2.0
    profile: list[tuple[float, float]] = []

    # End cap at p1, from +normal to -normal through the forward side.
    for step in range(arc_segments + 1):
        angle = theta + math.pi / 2.0 - step * math.pi / arc_segments
        profile.append((y1 + radius * math.cos(angle), z1 + radius * math.sin(angle)))
    # Start cap at p0, from -normal to +normal through the rear side.
    for step in range(arc_segments + 1):
        angle = theta - math.pi / 2.0 - step * math.pi / arc_segments
        profile.append((y0 + radius * math.cos(angle), z0 + radius * math.sin(angle)))

    mesh = MeshGeometry()
    back: list[int] = []
    front: list[int] = []
    for y, z in profile:
        back.append(mesh.add_vertex(x_center - thickness / 2.0, y, z))
    for y, z in profile:
        front.append(mesh.add_vertex(x_center + thickness / 2.0, y, z))
    n = len(profile)
    for i in range(n):
        j = (i + 1) % n
        _add_quad(mesh, back[i], front[i], front[j], back[j])
    back_center = mesh.add_vertex(x_center - thickness / 2.0, sum(p[0] for p in profile) / n, sum(p[1] for p in profile) / n)
    front_center = mesh.add_vertex(x_center + thickness / 2.0, sum(p[0] for p in profile) / n, sum(p[1] for p in profile) / n)
    for i in range(n):
        j = (i + 1) % n
        mesh.add_face(front_center, front[i], front[j])
        mesh.add_face(back_center, back[j], back[i])
    return mesh
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="downhill_freeride_crankset")

    model.material("bb_black", rgba=(0.025, 0.027, 0.030, 1.0))
    model.material("matte_black", rgba=(0.035, 0.037, 0.040, 1.0))
    model.material("gunmetal", rgba=(0.22, 0.23, 0.25, 1.0))
    model.material("brushed_steel", rgba=(0.70, 0.72, 0.74, 1.0))
    model.material("guard_black", rgba=(0.01, 0.012, 0.014, 1.0))
    model.material("bolt_steel", rgba=(0.62, 0.64, 0.66, 1.0))
    model.material("rubber", rgba=(0.012, 0.012, 0.013, 1.0))

    shell = model.part("bottom_shell")
    shell.visual(
        mesh_from_geometry(
            _stepped_tube_x(
                [
                    (-0.066, 0.036),
                    (-0.054, 0.036),
                    (-0.048, 0.029),
                    (0.048, 0.029),
                    (0.054, 0.036),
                    (0.066, 0.036),
                ],
                inner_radius=0.020,
            ),
            "wide_bottom_bracket_shell",
        ),
        material="bb_black",
        name="bb_shell",
    )
    shell.visual(
        Box((0.128, 0.010, 0.008)),
        origin=Origin(xyz=(0.0, 0.0, 0.016)),
        material="gunmetal",
        name="bearing_pad_top",
    )
    shell.visual(
        Box((0.128, 0.010, 0.008)),
        origin=Origin(xyz=(0.0, 0.0, -0.016)),
        material="gunmetal",
        name="bearing_pad_bottom",
    )
    crank = model.part("crank")
    crank.visual(
        mesh_from_geometry(_solid_cylinder_x(0.245, 0.012), "hollowtech_spindle"),
        material="brushed_steel",
        name="spindle",
    )
    crank.visual(
        Cylinder(radius=0.033, length=0.050),
        origin=Origin(xyz=(0.092, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="gunmetal",
        name="drive_hub",
    )
    crank.visual(
        Cylinder(radius=0.031, length=0.036),
        origin=Origin(xyz=(-0.092, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="gunmetal",
        name="arm_hub",
    )
    crank.visual(
        mesh_from_geometry(
            _capsule_prism_x((0.0, -0.006), (0.0, -0.166), 0.036, 0.019, x_center=0.082),
            "oversized_crank_arm_down",
        ),
        material="matte_black",
        name="arm_down",
    )
    crank.visual(
        mesh_from_geometry(
            _capsule_prism_x((0.0, 0.006), (0.0, 0.166), 0.036, 0.019, x_center=-0.082),
            "oversized_crank_arm_up",
        ),
        material="matte_black",
        name="arm_up",
    )
    crank.visual(
        Cylinder(radius=0.026, length=0.022),
        origin=Origin(xyz=(0.082, 0.0, -0.166), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="matte_black",
        name="pedal_boss_down",
    )
    crank.visual(
        Cylinder(radius=0.026, length=0.022),
        origin=Origin(xyz=(-0.082, 0.0, 0.166), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="matte_black",
        name="pedal_boss_up",
    )
    crank.visual(
        mesh_from_geometry(
            _annular_disk_x(0.007, 0.101, 0.065, segments=120),
            "bash_guard_outer_ring",
        ),
        origin=Origin(xyz=(0.112, 0.0, 0.0)),
        material="guard_black",
        name="bash_guard",
    )
    crank.visual(
        mesh_from_geometry(
            _annular_disk_x(0.004, 0.077, 0.050, segments=128, tooth_count=32, tooth_depth=0.005),
            "toothed_chainring",
        ),
        origin=Origin(xyz=(0.101, 0.0, 0.0)),
        material="brushed_steel",
        name="chainring",
    )
    for index, angle in enumerate((math.pi / 4.0, 3.0 * math.pi / 4.0, 5.0 * math.pi / 4.0, 7.0 * math.pi / 4.0)):
        end = (0.074 * math.cos(angle), 0.074 * math.sin(angle))
        crank.visual(
            mesh_from_geometry(
                _capsule_prism_x((0.0, 0.0), end, 0.014, 0.012, x_center=0.104),
                f"spider_spoke_{index}",
            ),
            material="gunmetal",
            name=f"spider_spoke_{index}",
        )
        crank.visual(
            Cylinder(radius=0.0055, length=0.005),
            origin=Origin(
                xyz=(0.1175, end[0], end[1]),
                rpy=(0.0, math.pi / 2.0, 0.0),
            ),
            material="bolt_steel",
            name=f"guard_bolt_{index}",
        )

    for name, side in (("pedal_0", 1.0), ("pedal_1", -1.0)):
        pedal = model.part(name)
        pedal.visual(
            Cylinder(radius=0.0053, length=0.052),
            origin=Origin(xyz=(side * 0.026, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material="brushed_steel",
            name="axle",
        )
        pedal.visual(
            Box((0.022, 0.106, 0.056)),
            origin=Origin(xyz=(side * 0.058, 0.0, 0.0)),
            material="rubber",
            name="platform_body",
        )
        pedal.visual(
            Box((0.026, 0.010, 0.064)),
            origin=Origin(xyz=(side * 0.058, 0.050, 0.0)),
            material="matte_black",
            name="outer_rail_0",
        )
        pedal.visual(
            Box((0.026, 0.010, 0.064)),
            origin=Origin(xyz=(side * 0.058, -0.050, 0.0)),
            material="matte_black",
            name="outer_rail_1",
        )
        pedal.visual(
            Box((0.026, 0.088, 0.008)),
            origin=Origin(xyz=(side * 0.058, 0.0, 0.030)),
            material="matte_black",
            name="grip_bar_0",
        )
        pedal.visual(
            Box((0.026, 0.088, 0.008)),
            origin=Origin(xyz=(side * 0.058, 0.0, -0.030)),
            material="matte_black",
            name="grip_bar_1",
        )

    model.articulation(
        "spindle_spin",
        ArticulationType.CONTINUOUS,
        parent=shell,
        child=crank,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=120.0, velocity=18.0),
    )
    model.articulation(
        "pedal_0_spin",
        ArticulationType.CONTINUOUS,
        parent=crank,
        child="pedal_0",
        origin=Origin(xyz=(0.093, 0.0, -0.166)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=22.0),
    )
    model.articulation(
        "pedal_1_spin",
        ArticulationType.CONTINUOUS,
        parent=crank,
        child="pedal_1",
        origin=Origin(xyz=(-0.093, 0.0, 0.166)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=22.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
