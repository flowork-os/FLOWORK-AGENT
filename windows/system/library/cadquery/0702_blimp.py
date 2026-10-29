# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, blimp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: blimp

from __future__ import annotations

import cadquery as cq
import math
from dataclasses import dataclass, field

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

# ===== section_loft (16 syms) =====
def _cq_shapes():
    """The low-level cadquery shape helpers the real sdk lofts through."""
    from cadquery.occ_impl import shapes as cq_shapes
    return cq_shapes

def _as_vec3(values, *, name):
    if len(values) != 3:
        raise ValidationError("%s must have 3 elements" % name)
    return (float(values[0]), float(values[1]), float(values[2]))

def _normalize_section_points(points, *, name):
    raw = [_as_vec3(point, name=name) for point in points]
    if len(raw) < 3:
        raise ValidationError("%s must contain at least 3 points" % name)

    out = []
    for point in raw:
        if not out or point != out[-1]:
            out.append(point)

    if len(out) >= 2 and out[0] == out[-1]:
        out.pop()

    if len(out) < 3:
        raise ValidationError("%s must contain at least 3 distinct points" % name)
    return out

@dataclass(frozen=True)
class LoftTessellation:
    tolerance: float = 0.001
    angular_tolerance: float = 0.1

    def __post_init__(self):
        if float(self.tolerance) <= 0.0:
            raise ValidationError("tessellation.tolerance must be > 0")
        if float(self.angular_tolerance) <= 0.0:
            raise ValidationError("tessellation.angular_tolerance must be > 0")
        object.__setattr__(self, "tolerance", float(self.tolerance))
        object.__setattr__(self, "angular_tolerance", float(self.angular_tolerance))

@dataclass(frozen=True)
class LoftSection:
    points: tuple

    def __post_init__(self):
        coerced = tuple(_normalize_section_points(self.points, name="section.points"))
        object.__setattr__(self, "points", coerced)

@dataclass(frozen=True)
class SectionLoftSpec:
    sections: tuple
    path: tuple = None
    guide_curves: dict = None
    cap: bool = True
    solid: bool = True
    symmetry: str = None
    ruled: bool = False
    continuity: str = "C2"
    parametrization: str = "uniform"
    degree: int = 3
    compat: bool = True
    smoothing: bool = False
    weights: tuple = (1.0, 1.0, 1.0)
    repair: str = "auto"
    tessellation: LoftTessellation = field(default_factory=LoftTessellation)

    def __post_init__(self):
        sections = tuple(_coerce_loft_section(section) for section in self.sections)
        if len(sections) < 2:
            raise ValidationError("SectionLoftSpec.sections must contain at least two sections")
        object.__setattr__(self, "sections", sections)

        if self.path is not None:
            object.__setattr__(
                self, "path",
                tuple(_as_vec3(point, name="path[]") for point in self.path),
            )
        if self.guide_curves is not None:
            guide_curves = {
                str(name): tuple(_as_vec3(point, name="guide_curves[%r][]" % name) for point in pts)
                for name, pts in self.guide_curves.items()
            }
            object.__setattr__(self, "guide_curves", guide_curves)

        if self.symmetry is not None and self.symmetry != "mirror_yz":
            raise ValidationError("symmetry must be 'mirror_yz' or None")
        if self.degree < 1:
            raise ValidationError("degree must be >= 1")
        if len(self.weights) != 3:
            raise ValidationError("weights must contain exactly 3 values")
        object.__setattr__(self, "degree", int(self.degree))
        object.__setattr__(
            self, "weights",
            (float(self.weights[0]), float(self.weights[1]), float(self.weights[2])),
        )

def _coerce_loft_section(value):
    if isinstance(value, LoftSection):
        return value
    return LoftSection(points=tuple(value))

def _coerce_loft_spec(spec):
    if isinstance(spec, SectionLoftSpec):
        return spec
    return SectionLoftSpec(sections=tuple(_coerce_loft_section(section) for section in spec))

def _build_section_wires(spec):
    cq_shapes = _cq_shapes()
    wires = []
    for idx, section in enumerate(spec.sections):
        points = tuple(section.points)
        try:
            wire = cq_shapes.polygon(*points)
        except Exception as exc:
            raise ValidationError("Failed to build wire for section[%d]" % idx)
        wires.append(wire)
    return wires

def _curve_from_points(points, *, name):
    cq_shapes = _cq_shapes()
    if len(points) < 2:
        raise ValidationError("%s must contain at least 2 points" % name)
    if len(points) == 2:
        return cq_shapes.segment(points[0], points[1])
    try:
        return cq_shapes.spline(*points)
    except Exception:
        try:
            return cq_shapes.polyline(*points)
        except Exception as exc:
            raise ValidationError("Failed to build %s" % name)

def _resolve_path_points(spec):
    if spec.path is not None:
        return spec.path
    if spec.guide_curves is None:
        return None
    return spec.guide_curves.get("spine")

def _resolve_aux_spine_points(spec):
    if spec.guide_curves is None:
        return None
    aux = spec.guide_curves.get("aux_spine")
    if aux is not None:
        return aux
    return spec.guide_curves.get("binormal")

def _validate_guide_curve_names(spec):
    if spec.guide_curves is None:
        return
    supported = {"spine", "aux_spine", "binormal"}
    unsupported = sorted(set(spec.guide_curves) - supported)
    if unsupported:
        raise ValidationError(
            "Unsupported guide_curves keys: "
            + ", ".join(repr(name) for name in unsupported)
            + ". Supported keys are 'spine', 'aux_spine', and 'binormal'."
        )

def _apply_symmetry_shape(shape, *, symmetry):
    if symmetry is None:
        return shape
    if symmetry != "mirror_yz":
        raise ValidationError("Unsupported symmetry mode: %r" % symmetry)
    try:
        mirrored = shape.mirror("YZ")
        if hasattr(shape, "fuse"):
            fused = shape.fuse(mirrored, glue=True)
        else:
            fused = shape
        if hasattr(fused, "fix"):
            fused = fused.fix()
        if hasattr(fused, "clean"):
            fused = fused.clean()
        return fused
    except Exception as exc:
        raise ValidationError("Failed to apply mirror_yz symmetry")

def _heal_shape(shape, *, solid):
    cq_shapes = _cq_shapes()
    if hasattr(shape, "fix"):
        shape = shape.fix()
    if solid:
        try:
            shape = cq_shapes.solid(shape)
        except Exception:
            pass
        if hasattr(shape, "fix"):
            shape = shape.fix()
    return shape

def section_loft(spec, /, **overrides):
    if overrides:
        spec = SectionLoftSpec(**({**_coerce_loft_spec(spec).__dict__, **overrides}))
    else:
        spec = _coerce_loft_spec(spec)

    cq_shapes = _cq_shapes()
    _validate_guide_curve_names(spec)
    wires = _build_section_wires(spec)
    path_points = _resolve_path_points(spec)
    aux_spine_points = _resolve_aux_spine_points(spec)

    if path_points is None:
        shape = cq_shapes.loft(
            wires,
            cap=bool(spec.cap and spec.solid),
            ruled=bool(spec.ruled),
            continuity=spec.continuity,
            parametrization=spec.parametrization,
            degree=int(spec.degree),
            compat=bool(spec.compat),
            smoothing=bool(spec.smoothing),
            weights=spec.weights,
        )
    else:
        path_curve = _curve_from_points(path_points, name="path")
        mode = None
        if aux_spine_points is not None:
            mode = _curve_from_points(aux_spine_points, name="guide_curves['aux_spine']")
        shape = cq_shapes.Solid.sweep_multi(
            wires,
            path_curve,
            makeSolid=bool(spec.solid and spec.cap),
            isFrenet=False,
            mode=mode,
        )

    shape = _apply_symmetry_shape(shape, symmetry=spec.symmetry)

    if spec.repair in {"auto", "kernel"}:
        shape = _heal_shape(shape, solid=bool(spec.solid and spec.cap))

    return MeshGeometry()._set(shape)

# ===== model =====
import math
def _save_mesh(name: str, geometry):
    return mesh_from_geometry(geometry, name)
def _ellipse_section(x: float, ry: float, rz: float, *, segments: int = 32) -> list[tuple[float, float, float]]:
    return [
        (x, ry * math.cos(angle), rz * math.sin(angle))
        for angle in [2.0 * math.pi * i / segments for i in range(segments)]
    ]
def _midpoint(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5)
def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2)
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
def _add_member(
    part,
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    *,
    radius: float,
    material,
    name: str | None = None,
) -> None:
    part.visual(
        Cylinder(radius=radius, length=_distance(a, b)),
        origin=Origin(xyz=_midpoint(a, b), rpy=_rpy_for_cylinder(a, b)),
        material=material,
        name=name,
    )
def _build_propeller(model: ArticulatedObject, name: str, blade_material, hub_material):
    propeller = model.part(name)
    propeller.visual(
        Cylinder(radius=0.024, length=0.09),
        origin=Origin(xyz=(-0.045, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=hub_material,
        name="shaft",
    )
    propeller.visual(
        Cylinder(radius=0.06, length=0.12),
        origin=Origin(xyz=(0.03, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=hub_material,
        name="hub",
    )
    propeller.visual(
        Sphere(radius=0.05),
        origin=Origin(xyz=(0.08, 0.0, 0.0)),
        material=hub_material,
        name="spinner",
    )
    propeller.visual(
        Box((0.02, 0.82, 0.12)),
        material=blade_material,
        name="blade_y",
    )
    propeller.visual(
        Box((0.02, 0.12, 0.82)),
        material=blade_material,
        name="blade_z",
    )
    return propeller
def _build_wheel(model: ArticulatedObject, name: str, tire_material, hub_material):
    wheel = model.part(name)
    wheel.visual(
        Cylinder(radius=0.18, length=0.08),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=tire_material,
        name="tire",
    )
    wheel.visual(
        Cylinder(radius=0.065, length=0.08),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=hub_material,
        name="hub",
    )
    return wheel
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="surveillance_blimp")

    envelope_white = model.material("envelope_white", rgba=(0.93, 0.94, 0.95, 1.0))
    light_gray = model.material("light_gray", rgba=(0.73, 0.76, 0.79, 1.0))
    structure_gray = model.material("structure_gray", rgba=(0.43, 0.46, 0.50, 1.0))
    dark_metal = model.material("dark_metal", rgba=(0.18, 0.19, 0.21, 1.0))
    rubber = model.material("rubber", rgba=(0.05, 0.05, 0.06, 1.0))
    glass_blue = model.material("glass_blue", rgba=(0.40, 0.56, 0.67, 0.50))
    safety_orange = model.material("safety_orange", rgba=(0.82, 0.45, 0.14, 1.0))

    hull = model.part("hull")
    envelope_geom = section_loft(
        [
            _ellipse_section(-8.90, 0.04, 0.04),
            _ellipse_section(-7.70, 0.82, 0.82),
            _ellipse_section(-4.80, 1.65, 1.68),
            _ellipse_section(-0.40, 2.08, 2.10),
            _ellipse_section(3.20, 2.00, 2.02),
            _ellipse_section(6.80, 1.10, 1.10),
            _ellipse_section(8.95, 0.06, 0.06),
        ]
    )
    hull.visual(
        _save_mesh("blimp_envelope", envelope_geom),
        material=envelope_white,
        name="envelope",
    )

    gondola = model.part("gondola")
    gondola.visual(
        Box((0.72, 0.54, 0.08)),
        origin=Origin(xyz=(0.0, 0.0, -0.04)),
        material=structure_gray,
        name="roof_saddle",
    )
    for x_sign in (-1.0, 1.0):
        for y_sign in (-1.0, 1.0):
            _add_member(
                gondola,
                (0.24 * x_sign, 0.18 * y_sign, -0.08),
                (0.54 * x_sign, 0.30 * y_sign, -0.40),
                radius=0.040,
                material=structure_gray,
            )
    gondola.visual(
        Box((2.10, 0.96, 0.72)),
        origin=Origin(xyz=(0.0, 0.0, -0.74)),
        material=light_gray,
        name="cabin",
    )
    gondola.visual(
        Cylinder(radius=0.42, length=0.84),
        origin=Origin(xyz=(1.42, 0.0, -0.74), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=light_gray,
        name="nose_fairing",
    )
    gondola.visual(
        Cylinder(radius=0.30, length=0.58),
        origin=Origin(xyz=(-1.34, 0.0, -0.74), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=light_gray,
        name="tail_fairing",
    )
    gondola.visual(
        Box((0.90, 0.04, 0.28)),
        origin=Origin(xyz=(0.36, 0.50, -0.70)),
        material=glass_blue,
        name="port_window",
    )
    gondola.visual(
        Box((0.90, 0.04, 0.28)),
        origin=Origin(xyz=(0.36, -0.50, -0.70)),
        material=glass_blue,
        name="starboard_window",
    )
    gondola.visual(
        Box((0.16, 0.54, 0.30)),
        origin=Origin(xyz=(1.00, 0.0, -0.70)),
        material=glass_blue,
        name="windscreen",
    )
    gondola.visual(
        Cylinder(radius=0.055, length=0.10),
        origin=Origin(xyz=(0.58, 0.0, -1.11)),
        material=dark_metal,
        name="sensor_mast",
    )
    gondola.visual(
        Sphere(radius=0.22),
        origin=Origin(xyz=(0.58, 0.0, -1.27)),
        material=dark_metal,
        name="sensor_dome",
    )
    gondola.visual(
        Cylinder(radius=0.07, length=0.30),
        origin=Origin(xyz=(0.79, 0.0, -1.27), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_metal,
        name="camera_barrel",
    )
    model.articulation(
        "hull_to_gondola",
        ArticulationType.FIXED,
        parent=hull,
        child=gondola,
        origin=Origin(xyz=(1.10, 0.0, -2.14)),
    )

    def add_engine(
        engine_name: str,
        prop_name: str,
        joint_name: str,
        attach_xyz: tuple[float, float, float],
        side_sign: float,
    ) -> None:
        engine = model.part(engine_name)
        engine.visual(
            Sphere(radius=0.0447),
            origin=Origin(),
            material=structure_gray,
            name="mount_boss",
        )
        engine.visual(
            Box((0.16, 0.30, 0.12)),
            origin=Origin(xyz=(0.0, 0.145 * side_sign, -0.06)),
            material=structure_gray,
            name="mount_arm",
        )
        engine.visual(
            Box((0.18, 0.42, 0.14)),
            origin=Origin(xyz=(0.0, 0.34 * side_sign, -0.07)),
            material=structure_gray,
            name="mount_bracket",
        )
        _add_member(
            engine,
            (0.02, 0.18 * side_sign, -0.02),
            (0.12, 0.64 * side_sign, -0.08),
            radius=0.042,
            material=structure_gray,
            name="upper_pylon",
        )
        _add_member(
            engine,
            (-0.06, 0.14 * side_sign, -0.06),
            (-0.12, 0.64 * side_sign, -0.18),
            radius=0.040,
            material=structure_gray,
            name="lower_pylon",
        )
        engine.visual(
            Cylinder(radius=0.20, length=1.10),
            origin=Origin(
                xyz=(0.02, 0.84 * side_sign, -0.12),
                rpy=(0.0, math.pi / 2.0, 0.0),
            ),
            material=structure_gray,
            name="nacelle_body",
        )
        engine.visual(
            Sphere(radius=0.11),
            origin=Origin(xyz=(0.56, 0.84 * side_sign, -0.12)),
            material=structure_gray,
            name="cowling",
        )
        engine.visual(
            Sphere(radius=0.14),
            origin=Origin(xyz=(-0.53, 0.84 * side_sign, -0.12)),
            material=dark_metal,
            name="rear_cap",
        )
        engine.visual(
            Cylinder(radius=0.045, length=0.18),
            origin=Origin(
                xyz=(-0.67, 0.84 * side_sign, -0.12),
                rpy=(0.0, math.pi / 2.0, 0.0),
            ),
            material=dark_metal,
            name="exhaust",
        )
        model.articulation(
            f"hull_to_{engine_name}",
            ArticulationType.FIXED,
            parent=hull,
            child=engine,
            origin=Origin(xyz=attach_xyz),
        )

        propeller = _build_propeller(model, prop_name, safety_orange, dark_metal)
        model.articulation(
            joint_name,
            ArticulationType.CONTINUOUS,
            parent=engine,
            child=propeller,
            origin=Origin(xyz=(0.76, 0.84 * side_sign, -0.12)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=40.0, velocity=55.0),
        )

    add_engine("port_engine", "port_propeller", "port_prop_spin", (-0.80, 2.10, 0.0), 1.0)
    add_engine(
        "starboard_engine",
        "starboard_propeller",
        "starboard_prop_spin",
        (-0.80, -2.10, 0.0),
        -1.0,
    )

    gear_frame = model.part("gear_frame")
    gear_frame.visual(
        Box((0.86, 0.28, 0.08)),
        origin=Origin(xyz=(0.0, 0.0, -0.04)),
        material=structure_gray,
        name="gear_mount",
    )
    for x_sign in (-1.0, 1.0):
        for y_sign in (-1.0, 1.0):
            _add_member(
                gear_frame,
                (0.24 * x_sign, 0.12 * y_sign, -0.08),
                (0.02 * x_sign, 0.52 * y_sign, -0.42),
                radius=0.030,
                material=structure_gray,
            )
    gear_frame.visual(
        Cylinder(radius=0.032, length=1.16),
        origin=Origin(xyz=(0.0, 0.0, -0.42), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="axle",
    )
    model.articulation(
        "gondola_to_gear_frame",
        ArticulationType.FIXED,
        parent=gondola,
        child=gear_frame,
        origin=Origin(xyz=(-0.30, 0.0, -1.10)),
    )

    port_wheel = _build_wheel(model, "port_wheel", rubber, dark_metal)
    starboard_wheel = _build_wheel(model, "starboard_wheel", rubber, dark_metal)
    model.articulation(
        "port_wheel_spin",
        ArticulationType.CONTINUOUS,
        parent=gear_frame,
        child=port_wheel,
        origin=Origin(xyz=(0.0, 0.62, -0.42)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=20.0),
    )
    model.articulation(
        "starboard_wheel_spin",
        ArticulationType.CONTINUOUS,
        parent=gear_frame,
        child=starboard_wheel,
        origin=Origin(xyz=(0.0, -0.62, -0.42)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=20.0),
    )

    tail_frame = model.part("tail_frame")
    tail_frame.visual(
        Cylinder(radius=0.13, length=0.62),
        origin=Origin(xyz=(-0.31, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=structure_gray,
        name="tail_stinger",
    )
    tail_frame.visual(
        Box((0.48, 0.58, 0.14)),
        origin=Origin(xyz=(-0.34, 0.0, 0.0)),
        material=structure_gray,
        name="tail_center",
    )
    tail_frame.visual(
        Box((0.68, 0.10, 1.10)),
        origin=Origin(xyz=(-0.56, 0.0, 0.64)),
        material=light_gray,
        name="fin",
    )
    tail_frame.visual(
        Box((0.42, 0.08, 0.48)),
        origin=Origin(xyz=(-0.38, 0.0, -0.28)),
        material=light_gray,
        name="ventral_fin",
    )
    tail_frame.visual(
        Box((0.70, 0.58, 0.08)),
        origin=Origin(xyz=(-0.56, 0.39, 0.0)),
        material=light_gray,
        name="port_stabilizer",
    )
    tail_frame.visual(
        Box((0.70, 0.58, 0.08)),
        origin=Origin(xyz=(-0.56, -0.39, 0.0)),
        material=light_gray,
        name="starboard_stabilizer",
    )
    model.articulation(
        "hull_to_tail_frame",
        ArticulationType.FIXED,
        parent=hull,
        child=tail_frame,
        origin=Origin(xyz=(-8.90, 0.0, 0.0)),
    )

    rudder = model.part("rudder")
    rudder.visual(
        Box((0.44, 0.05, 0.72)),
        origin=Origin(xyz=(-0.22, 0.0, 0.0)),
        material=light_gray,
        name="rudder_surface",
    )
    model.articulation(
        "rudder_hinge",
        ArticulationType.REVOLUTE,
        parent=tail_frame,
        child=rudder,
        origin=Origin(xyz=(-0.90, 0.0, 0.60)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=15.0,
            velocity=1.4,
            lower=-0.45,
            upper=0.45,
        ),
    )

    port_elevator = model.part("port_elevator")
    port_elevator.visual(
        Box((0.38, 0.38, 0.05)),
        origin=Origin(xyz=(-0.19, 0.0, 0.0)),
        material=light_gray,
        name="elevator_surface",
    )
    model.articulation(
        "port_elevator_hinge",
        ArticulationType.REVOLUTE,
        parent=tail_frame,
        child=port_elevator,
        origin=Origin(xyz=(-0.91, 0.39, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=1.4,
            lower=-0.35,
            upper=0.35,
        ),
    )

    starboard_elevator = model.part("starboard_elevator")
    starboard_elevator.visual(
        Box((0.38, 0.38, 0.05)),
        origin=Origin(xyz=(-0.19, 0.0, 0.0)),
        material=light_gray,
        name="elevator_surface",
    )
    model.articulation(
        "starboard_elevator_hinge",
        ArticulationType.REVOLUTE,
        parent=tail_frame,
        child=starboard_elevator,
        origin=Origin(xyz=(-0.91, -0.39, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=1.4,
            lower=-0.35,
            upper=0.35,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
