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
def _extruded_loop_x(
    yz_points: list[tuple[float, float]],
    *,
    x_center: float,
    thickness: float,
) -> MeshGeometry:
    """Extrude a closed YZ profile along local/global X."""
    geom = MeshGeometry()
    half = thickness / 2.0
    front: list[int] = []
    back: list[int] = []
    for y, z in yz_points:
        front.append(geom.add_vertex(x_center + half, y, z))
    for y, z in yz_points:
        back.append(geom.add_vertex(x_center - half, y, z))

    n = len(yz_points)
    # Side faces.
    for i in range(n):
        j = (i + 1) % n
        geom.add_face(front[i], front[j], back[j])
        geom.add_face(front[i], back[j], back[i])

    # Fan caps.  Profiles used here are convex or nearly convex.
    for i in range(1, n - 1):
        geom.add_face(front[0], front[i], front[i + 1])
        geom.add_face(back[0], back[i + 1], back[i])
    return geom
def _tube_x_mesh(
    *,
    x_center: float,
    length: float,
    outer_radius: float,
    inner_radius: float,
    segments: int = 72,
) -> MeshGeometry:
    """A hollow cylinder/tube with its axis along X."""
    geom = MeshGeometry()
    x0 = x_center - length / 2.0
    x1 = x_center + length / 2.0
    outer0: list[int] = []
    outer1: list[int] = []
    inner0: list[int] = []
    inner1: list[int] = []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        ca, sa = math.cos(a), math.sin(a)
        outer0.append(geom.add_vertex(x0, outer_radius * ca, outer_radius * sa))
        outer1.append(geom.add_vertex(x1, outer_radius * ca, outer_radius * sa))
        inner0.append(geom.add_vertex(x0, inner_radius * ca, inner_radius * sa))
        inner1.append(geom.add_vertex(x1, inner_radius * ca, inner_radius * sa))

    for i in range(segments):
        j = (i + 1) % segments
        # Outside skin.
        geom.add_face(outer0[i], outer0[j], outer1[j])
        geom.add_face(outer0[i], outer1[j], outer1[i])
        # Inside bore.
        geom.add_face(inner0[i], inner1[j], inner0[j])
        geom.add_face(inner0[i], inner1[i], inner1[j])
        # End annuli.
        geom.add_face(outer0[i], inner0[j], outer0[j])
        geom.add_face(outer0[i], inner0[i], inner0[j])
        geom.add_face(outer1[i], outer1[j], inner1[j])
        geom.add_face(outer1[i], inner1[j], inner1[i])
    return geom
def _toothed_chainring_mesh(
    *,
    x_center: float,
    thickness: float,
    tooth_count: int,
    tip_radius: float,
    root_radius: float,
    inner_radius: float,
) -> MeshGeometry:
    """Flat chainring in the YZ plane with alternating tooth-tip/root radii."""
    geom = MeshGeometry()
    n = tooth_count * 2
    xf = x_center + thickness / 2.0
    xb = x_center - thickness / 2.0
    outer_f: list[int] = []
    outer_b: list[int] = []
    inner_f: list[int] = []
    inner_b: list[int] = []

    for i in range(n):
        a = 2.0 * math.pi * i / n
        # Narrow, pointed teeth with valleys between them.
        r = tip_radius if i % 2 == 0 else root_radius
        ca, sa = math.cos(a), math.sin(a)
        outer_f.append(geom.add_vertex(xf, r * ca, r * sa))
        outer_b.append(geom.add_vertex(xb, r * ca, r * sa))
        inner_f.append(geom.add_vertex(xf, inner_radius * ca, inner_radius * sa))
        inner_b.append(geom.add_vertex(xb, inner_radius * ca, inner_radius * sa))

    for i in range(n):
        j = (i + 1) % n
        # Front and back annular faces.
        geom.add_face(outer_f[i], outer_f[j], inner_f[j])
        geom.add_face(outer_f[i], inner_f[j], inner_f[i])
        geom.add_face(outer_b[i], inner_b[j], outer_b[j])
        geom.add_face(outer_b[i], inner_b[i], inner_b[j])
        # Outer tooth wall and inner bore wall.
        geom.add_face(outer_f[i], outer_b[j], outer_f[j])
        geom.add_face(outer_f[i], outer_b[i], outer_b[j])
        geom.add_face(inner_f[i], inner_f[j], inner_b[j])
        geom.add_face(inner_f[i], inner_b[j], inner_b[i])
    return geom
def _radial_spoke_mesh(
    *,
    angle: float,
    x_center: float,
    thickness: float,
    r0: float,
    r1: float,
    width0: float,
    width1: float,
) -> MeshGeometry:
    """Tapered spider arm profile in the YZ plane, extruded along X."""
    ca, sa = math.cos(angle), math.sin(angle)
    # radial and perpendicular unit vectors in the YZ plane
    ry, rz = ca, sa
    py, pz = -sa, ca

    def pt(radius: float, half_width: float, sign: float) -> tuple[float, float]:
        return (
            radius * ry + sign * half_width * py,
            radius * rz + sign * half_width * pz,
        )

    profile = [
        pt(r0, width0 / 2.0, -1.0),
        pt(r1, width1 / 2.0, -1.0),
        pt(r1, width1 / 2.0, 1.0),
        pt(r0, width0 / 2.0, 1.0),
    ]
    return _extruded_loop_x(profile, x_center=x_center, thickness=thickness)
def _crank_arm_mesh(
    *,
    x_center: float,
    thickness: float,
    y_start: float,
    y_end: float,
    width_start: float,
    width_end: float,
) -> MeshGeometry:
    """A long forged crank arm, tapered in Z and extruded along X."""
    sign = 1.0 if y_end > y_start else -1.0
    cap_len = 0.012 * sign
    profile = [
        (y_start - cap_len, -width_start / 2.0),
        (y_start + 0.010 * sign, -width_start / 2.0),
        (y_end - 0.012 * sign, -width_end / 2.0),
        (y_end + 0.010 * sign, -width_end / 2.0),
        (y_end + 0.016 * sign, 0.0),
        (y_end + 0.010 * sign, width_end / 2.0),
        (y_end - 0.012 * sign, width_end / 2.0),
        (y_start + 0.010 * sign, width_start / 2.0),
        (y_start - cap_len, width_start / 2.0),
        (y_start - 0.018 * sign, 0.0),
    ]
    return _extruded_loop_x(profile, x_center=x_center, thickness=thickness)
def _groove_mesh(
    *,
    x_center: float,
    y_start: float,
    y_end: float,
    z_half_width: float,
    thickness: float = 0.0012,
) -> MeshGeometry:
    """Thin dark inset panel on the crank-arm face."""
    profile = [
        (y_start, -z_half_width),
        (y_end, -z_half_width * 0.72),
        (y_end, z_half_width * 0.72),
        (y_start, z_half_width),
    ]
    return _extruded_loop_x(profile, x_center=x_center, thickness=thickness)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="road_bike_triple_crankset")

    forged_alloy = model.material("brushed_forged_alloy", rgba=(0.78, 0.76, 0.70, 1.0))
    polished = model.material("polished_worn_edges", rgba=(0.92, 0.90, 0.84, 1.0))
    dark_anodized = model.material("black_anodized_aluminum", rgba=(0.015, 0.016, 0.018, 1.0))
    gunmetal = model.material("gunmetal_chainring", rgba=(0.30, 0.31, 0.32, 1.0))
    bearing_black = model.material("bearing_black", rgba=(0.02, 0.02, 0.022, 1.0))
    seal_blue = model.material("rubber_seal_blue", rgba=(0.03, 0.09, 0.16, 1.0))
    bolt_steel = model.material("stainless_bolts", rgba=(0.72, 0.72, 0.68, 1.0))
    recess_black = model.material("matte_black_recess", rgba=(0.0, 0.0, 0.0, 1.0))

    # Root: stationary outboard-bearing unit with visible hollow cups.
    bearing_unit = model.part("bearing_unit")
    bearing_unit.visual(
        mesh_from_geometry(
            _tube_x_mesh(
                x_center=0.0,
                length=0.044,
                outer_radius=0.018,
                inner_radius=0.0137,
                segments=80,
            ),
            "center_sleeve",
        ),
        material=bearing_black,
        name="center_sleeve",
    )
    for side, suffix in ((1.0, "drive"), (-1.0, "left")):
        bearing_unit.visual(
            mesh_from_geometry(
                _tube_x_mesh(
                    x_center=side * 0.034,
                    length=0.024,
                    outer_radius=0.028,
                    inner_radius=0.0137,
                    segments=96,
                ),
                f"{suffix}_bearing_cup",
            ),
            material=dark_anodized,
            name=f"{suffix}_bearing_cup",
        )
        bearing_unit.visual(
            mesh_from_geometry(
                _tube_x_mesh(
                    x_center=side * 0.047,
                    length=0.0025,
                    outer_radius=0.020,
                    inner_radius=0.0137,
                    segments=80,
                ),
                f"{suffix}_bearing_seal",
            ),
            material=seal_blue,
            name=f"{suffix}_bearing_seal",
        )

    # Child rotating assembly: hollow spindle, cranks, forged spider, triple rings.
    crankset = model.part("crankset")
    crankset.visual(
        mesh_from_geometry(
            _tube_x_mesh(
                x_center=0.0,
                length=0.164,
                outer_radius=0.012,
                inner_radius=0.0065,
                segments=72,
            ),
            "hollow_spindle",
        ),
        material=dark_anodized,
        name="hollow_spindle",
    )

    # Three differently offset and sized chainrings (outer/middle/granny).
    ring_specs = [
        ("outer_chainring", 50, 0.105, 0.100, 0.075, 0.052, gunmetal),
        ("middle_chainring", 39, 0.084, 0.080, 0.057, 0.046, forged_alloy),
        ("inner_chainring", 30, 0.064, 0.060, 0.040, 0.040, gunmetal),
    ]
    for name, tooth_count, tip_r, root_r, inner_r, x, mat in ring_specs:
        crankset.visual(
            mesh_from_geometry(
                _toothed_chainring_mesh(
                    x_center=x,
                    thickness=0.0032,
                    tooth_count=tooth_count,
                    tip_radius=tip_r,
                    root_radius=root_r,
                    inner_radius=inner_r,
                ),
                name,
            ),
            material=mat,
            name=name,
        )

    # Forged five-arm spider and chainring bolts.
    spider_angles = [math.pi + 2.0 * math.pi * i / 5.0 for i in range(5)]
    for idx, angle in enumerate(spider_angles):
        crankset.visual(
            mesh_from_geometry(
                _radial_spoke_mesh(
                    angle=angle,
                    x_center=0.054,
                    thickness=0.012,
                    r0=0.021,
                    r1=0.079,
                    width0=0.020,
                    width1=0.014,
                ),
                f"spider_arm_{idx}",
            ),
            material=forged_alloy,
            name=f"spider_arm_{idx}",
        )
        y = 0.079 * math.cos(angle)
        z = 0.079 * math.sin(angle)
        crankset.visual(
            Cylinder(radius=0.0085, length=0.024),
            origin=Origin(xyz=(0.050, y, z), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=bolt_steel,
            name=f"chainring_bolt_{idx}",
        )
        crankset.visual(
            Cylinder(radius=0.0048, length=0.006),
            origin=Origin(xyz=(0.0615, y, z), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=recess_black,
            name=f"bolt_hex_socket_{idx}",
        )
        crankset.visual(
            Cylinder(radius=0.0042, length=0.014),
            origin=Origin(
                xyz=(0.044, 0.052 * math.cos(angle), 0.052 * math.sin(angle)),
                rpy=(0.0, math.pi / 2.0, 0.0),
            ),
            material=bolt_steel,
            name=f"inner_ring_standoff_{idx}",
        )

    crankset.visual(
        Cylinder(radius=0.027, length=0.028),
        origin=Origin(xyz=(0.056, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=forged_alloy,
        name="drive_hub",
    )
    crankset.visual(
        Cylinder(radius=0.015, length=0.018),
        origin=Origin(xyz=(0.072, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=polished,
        name="crank_spline_cover",
    )

    # Right/drive crank arm with a black relief groove and pedal eye.
    crankset.visual(
        mesh_from_geometry(
            _crank_arm_mesh(
                x_center=0.071,
                thickness=0.016,
                y_start=-0.018,
                y_end=-0.172,
                width_start=0.034,
                width_end=0.021,
            ),
            "drive_crank_arm",
        ),
        material=forged_alloy,
        name="drive_crank_arm",
    )
    crankset.visual(
        mesh_from_geometry(
            _groove_mesh(x_center=0.0796, y_start=-0.045, y_end=-0.145, z_half_width=0.0055),
            "drive_arm_groove",
        ),
        material=recess_black,
        name="drive_arm_groove",
    )
    crankset.visual(
        Cylinder(radius=0.014, length=0.020),
        origin=Origin(xyz=(0.071, -0.172, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=forged_alloy,
        name="drive_pedal_eye",
    )

    # Opposed left arm with clamp features and the preload cap at the spindle end.
    crankset.visual(
        mesh_from_geometry(
            _crank_arm_mesh(
                x_center=-0.064,
                thickness=0.016,
                y_start=0.018,
                y_end=0.172,
                width_start=0.034,
                width_end=0.021,
            ),
            "left_crank_arm",
        ),
        material=forged_alloy,
        name="left_crank_arm",
    )
    crankset.visual(
        mesh_from_geometry(
            _groove_mesh(x_center=-0.0726, y_start=0.046, y_end=0.145, z_half_width=0.0055),
            "left_arm_groove",
        ),
        material=recess_black,
        name="left_arm_groove",
    )
    crankset.visual(
        Cylinder(radius=0.026, length=0.030),
        origin=Origin(xyz=(-0.067, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=forged_alloy,
        name="left_clamp_boss",
    )
    crankset.visual(
        Box((0.0014, 0.033, 0.004)),
        origin=Origin(xyz=(-0.0764, 0.012, 0.0)),
        material=recess_black,
        name="clamp_split_slot",
    )
    crankset.visual(
        Box((0.011, 0.014, 0.036)),
        origin=Origin(xyz=(-0.067, 0.027, 0.0)),
        material=forged_alloy,
        name="clamp_lug",
    )
    for z in (-0.011, 0.011):
        crankset.visual(
            Cylinder(radius=0.0048, length=0.008),
            origin=Origin(xyz=(-0.075, 0.029, z), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=bolt_steel,
            name=f"pinch_bolt_{'lower' if z < 0 else 'upper'}",
        )
    crankset.visual(
        Cylinder(radius=0.015, length=0.006),
        origin=Origin(xyz=(-0.0785, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=recess_black,
        name="preload_cap",
    )
    crankset.visual(
        Cylinder(radius=0.0065, length=0.0015),
        origin=Origin(xyz=(-0.082, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=bolt_steel,
        name="preload_cap_socket",
    )
    crankset.visual(
        Cylinder(radius=0.014, length=0.020),
        origin=Origin(xyz=(-0.064, 0.172, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=forged_alloy,
        name="left_pedal_eye",
    )

    spindle_joint = model.articulation(
        "spindle_spin",
        ArticulationType.CONTINUOUS,
        parent=bearing_unit,
        child=crankset,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=35.0, velocity=18.0),
    )
    spindle_joint.meta["qc_samples"] = [0.0, math.pi / 2.0, math.pi]

    def add_pedal(name: str, side: float, y: float) -> None:
        pedal = model.part(name)
        body_center_x = side * 0.058
        pedal.visual(
            Cylinder(radius=0.0048, length=0.092),
            origin=Origin(xyz=(side * 0.046, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=bolt_steel,
            name="pedal_axle",
        )
        pedal.visual(
            Box((0.074, 0.060, 0.014)),
            origin=Origin(xyz=(body_center_x, 0.0, 0.0)),
            material=dark_anodized,
            name="pedal_body",
        )
        # Top-face cleat-platform recess and retention jaws.
        pedal.visual(
            Box((0.046, 0.030, 0.0012)),
            origin=Origin(xyz=(body_center_x, 0.0, 0.0076)),
            material=recess_black,
            name="cleat_recess",
        )
        pedal.visual(
            Box((0.054, 0.006, 0.004)),
            origin=Origin(xyz=(body_center_x, 0.022, 0.009)),
            material=polished,
            name="front_cleat_jaw",
        )
        pedal.visual(
            Box((0.054, 0.006, 0.004)),
            origin=Origin(xyz=(body_center_x, -0.022, 0.009)),
            material=polished,
            name="rear_cleat_jaw",
        )
        # Black side windows make the small pedal read as lightweight/open.
        pedal.visual(
            Box((0.050, 0.0015, 0.006)),
            origin=Origin(xyz=(body_center_x, 0.03075, 0.0)),
            material=recess_black,
            name="front_window",
        )
        pedal.visual(
            Box((0.050, 0.0015, 0.006)),
            origin=Origin(xyz=(body_center_x, -0.03075, 0.0)),
            material=recess_black,
            name="rear_window",
        )

        joint = model.articulation(
            f"{name}_spin",
            ArticulationType.CONTINUOUS,
            parent=crankset,
            child=pedal,
            origin=Origin(xyz=((0.081 if side > 0.0 else -0.074), y, 0.0)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=8.0, velocity=22.0),
        )
        joint.meta["qc_samples"] = [0.0, math.pi / 2.0]

    add_pedal("drive_pedal", 1.0, -0.172)
    add_pedal("left_pedal", -1.0, 0.172)

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
