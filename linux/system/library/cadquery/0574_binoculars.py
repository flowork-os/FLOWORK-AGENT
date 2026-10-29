# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, binoculars, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: binoculars

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

def rounded_rect_profile(width, height, radius, *, corner_segments=6):
    width = float(width); height = float(height); radius = float(radius)
    if width <= 0 or height <= 0:
        raise ValidationError("width/height must be positive")
    corner_segments = max(1, int(corner_segments))
    max_r = 0.5 * min(width, height)
    if radius < 0 or radius > max_r:
        raise ValidationError("radius must be within [0, %s]" % max_r)
    hw = width * 0.5; hh = height * 0.5
    if radius <= 1e-12:
        return [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    r = radius

    def arc(cx, cy, a0, a1):
        out = []
        for i in range(corner_segments + 1):
            t = i / corner_segments
            a = a0 + (a1 - a0) * t
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return out

    pts = []
    pts.extend(arc(hw - r, -hh + r, -math.pi / 2.0, 0.0))
    pts.extend(arc(hw - r, hh - r, 0.0, math.pi / 2.0)[1:])
    pts.extend(arc(-hw + r, hh - r, math.pi / 2.0, math.pi)[1:])
    pts.extend(arc(-hw + r, -hh + r, math.pi, 3.0 * math.pi / 2.0)[1:])
    return pts

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
def _x_cylinder(
    *,
    radius: float,
    length: float,
    center: tuple[float, float, float],
):
    return Cylinder(radius=radius, length=length), Origin(
        xyz=center,
        rpy=(0.0, math.pi / 2.0, 0.0),
    )
def _rounded_section(
    *,
    x: float,
    center_y: float,
    center_z: float,
    width_y: float,
    height_z: float,
    radius: float,
    corner_segments: int = 6,
) -> list[tuple[float, float, float]]:
    profile = rounded_rect_profile(
        width_y,
        height_z,
        radius,
        corner_segments=corner_segments,
    )
    return [(x, center_y + py, center_z + pz) for py, pz in profile]
def _build_barrel_body_mesh(side_sign: float):
    sections = [
        _rounded_section(
            x=-0.084,
            center_y=side_sign * 0.034,
            center_z=-0.018,
            width_y=0.042,
            height_z=0.046,
            radius=0.011,
        ),
        _rounded_section(
            x=-0.050,
            center_y=side_sign * 0.046,
            center_z=-0.014,
            width_y=0.052,
            height_z=0.056,
            radius=0.013,
        ),
        _rounded_section(
            x=-0.006,
            center_y=side_sign * 0.060,
            center_z=-0.006,
            width_y=0.062,
            height_z=0.072,
            radius=0.017,
        ),
        _rounded_section(
            x=0.040,
            center_y=side_sign * 0.070,
            center_z=-0.022,
            width_y=0.066,
            height_z=0.060,
            radius=0.016,
        ),
        _rounded_section(
            x=0.070,
            center_y=side_sign * 0.074,
            center_z=-0.030,
            width_y=0.060,
            height_z=0.052,
            radius=0.014,
        ),
    ]
    return section_loft(sections)
def _add_barrel_visuals(
    model: ArticulatedObject,
    part,
    *,
    side_sign: float,
    body_mesh_name: str,
    armor_material,
    trim_material,
    glass_material,
    right_side_features: bool,
) -> None:
    body_mesh = mesh_from_geometry(_build_barrel_body_mesh(side_sign), body_mesh_name)
    part.visual(body_mesh, material=armor_material, name="armor_shell")

    objective_geom, objective_origin = _x_cylinder(
        radius=0.033,
        length=0.112,
        center=(0.084, side_sign * 0.074, -0.034),
    )
    part.visual(
        objective_geom,
        origin=objective_origin,
        material=armor_material,
        name="objective_barrel",
    )

    objective_ring_geom, objective_ring_origin = _x_cylinder(
        radius=0.035,
        length=0.014,
        center=(0.137, side_sign * 0.074, -0.034),
    )
    part.visual(
        objective_ring_geom,
        origin=objective_ring_origin,
        material=trim_material,
        name="objective_ring",
    )

    objective_glass_geom, objective_glass_origin = _x_cylinder(
        radius=0.029,
        length=0.003,
        center=(0.141, side_sign * 0.074, -0.034),
    )
    part.visual(
        objective_glass_geom,
        origin=objective_glass_origin,
        material=glass_material,
        name="objective_window",
    )

    eyepiece_geom, eyepiece_origin = _x_cylinder(
        radius=0.020,
        length=0.050,
        center=(-0.094, side_sign * 0.034, -0.018),
    )
    part.visual(
        eyepiece_geom,
        origin=eyepiece_origin,
        material=trim_material,
        name="eyepiece_barrel",
    )

    eyecup_geom, eyecup_origin = _x_cylinder(
        radius=0.024,
        length=0.032,
        center=(-0.132, side_sign * 0.034, -0.018),
    )
    part.visual(
        eyecup_geom,
        origin=eyecup_origin,
        material=armor_material,
        name="eyecup",
    )

    eyepiece_glass_geom, eyepiece_glass_origin = _x_cylinder(
        radius=0.017,
        length=0.003,
        center=(-0.145, side_sign * 0.034, -0.018),
    )
    part.visual(
        eyepiece_glass_geom,
        origin=eyepiece_glass_origin,
        material=glass_material,
        name="eyepiece_window",
    )

    part.visual(
        Box((0.104, 0.010, 0.018)),
        origin=Origin(xyz=(0.000, side_sign * 0.015, -0.003)),
        material=armor_material,
        name="hinge_bridge",
    )
    part.visual(
        Box((0.082, 0.022, 0.024)),
        origin=Origin(xyz=(-0.004, side_sign * 0.026, -0.014)),
        material=armor_material,
        name="bridge_drop",
    )
    part.visual(
        Box((0.068, 0.018, 0.020)),
        origin=Origin(xyz=(-0.014, side_sign * 0.041, -0.020)),
        material=armor_material,
        name="inner_brace",
    )

    if right_side_features:
        for index, center_x in enumerate((-0.032, 0.032)):
            hinge_geom, hinge_origin = _x_cylinder(
                radius=0.0105,
                length=0.024,
                center=(center_x, 0.000, 0.000),
            )
            part.visual(
                hinge_geom,
                origin=hinge_origin,
                material=trim_material,
                name=f"hinge_knuckle_{index}",
            )

        part.visual(
            Box((0.044, 0.020, 0.010)),
            origin=Origin(xyz=(-0.040, 0.014, 0.009)),
            material=armor_material,
            name="focus_support_web",
        )

        for index, center_x in enumerate((-0.055, -0.025)):
            support_geom, support_origin = _x_cylinder(
                radius=0.009,
                length=0.010,
                center=(center_x, 0.000, 0.030),
            )
            part.visual(
                support_geom,
                origin=support_origin,
                material=trim_material,
                name=f"focus_support_knuckle_{index}",
            )
            part.visual(
                Box((0.006, 0.010, 0.014)),
                origin=Origin(xyz=(center_x, 0.004, 0.021)),
                material=trim_material,
                name=f"focus_support_post_{index}",
            )

        part.visual(
            Cylinder(radius=0.018, length=0.006),
            origin=Origin(xyz=(-0.012, 0.058, 0.026)),
            material=trim_material,
            name="compass_socket",
        )
    else:
        hinge_geom, hinge_origin = _x_cylinder(
            radius=0.0105,
            length=0.040,
            center=(0.000, 0.000, 0.000),
        )
        part.visual(
            hinge_geom,
            origin=hinge_origin,
            material=trim_material,
            name="hinge_knuckle_center",
        )

    part.inertial = Inertial.from_geometry(
        Box((0.290, 0.130, 0.090)),
        mass=0.78,
        origin=Origin(xyz=(0.000, side_sign * 0.060, -0.020)),
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="marine_porro_prism_binocular")

    armor_material = model.material("armor_black", rgba=(0.14, 0.15, 0.16, 1.0))
    trim_material = model.material("trim_graphite", rgba=(0.23, 0.24, 0.26, 1.0))
    glass_material = model.material("glass_green", rgba=(0.36, 0.47, 0.44, 0.45))
    metal_material = model.material("metal_dark", rgba=(0.30, 0.31, 0.34, 1.0))
    compass_dial_material = model.material("compass_dial", rgba=(0.84, 0.84, 0.76, 1.0))
    compass_needle_material = model.material("compass_needle", rgba=(0.70, 0.16, 0.14, 1.0))

    right_barrel = model.part("right_barrel")
    _add_barrel_visuals(
        model,
        right_barrel,
        side_sign=1.0,
        body_mesh_name="marine_binocular_right_body",
        armor_material=armor_material,
        trim_material=trim_material,
        glass_material=glass_material,
        right_side_features=True,
    )

    left_barrel = model.part("left_barrel")
    _add_barrel_visuals(
        model,
        left_barrel,
        side_sign=-1.0,
        body_mesh_name="marine_binocular_left_body",
        armor_material=armor_material,
        trim_material=trim_material,
        glass_material=glass_material,
        right_side_features=False,
    )

    model.articulation(
        "center_hinge",
        ArticulationType.REVOLUTE,
        parent=right_barrel,
        child=left_barrel,
        origin=Origin(xyz=(0.000, 0.000, 0.000)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=16.0,
            velocity=1.0,
            lower=-0.22,
            upper=0.22,
        ),
    )

    focus_wheel = model.part("focus_wheel")
    focus_hub_geom, focus_hub_origin = _x_cylinder(
        radius=0.009,
        length=0.020,
        center=(0.000, 0.000, 0.000),
    )
    focus_wheel.visual(
        focus_hub_geom,
        origin=focus_hub_origin,
        material=metal_material,
        name="focus_hub",
    )
    focus_tire_geom, focus_tire_origin = _x_cylinder(
        radius=0.016,
        length=0.016,
        center=(0.000, 0.000, 0.000),
    )
    focus_wheel.visual(
        focus_tire_geom,
        origin=focus_tire_origin,
        material=armor_material,
        name="focus_tire",
    )
    for index, center_x in enumerate((-0.008, 0.008)):
        ridge_geom, ridge_origin = _x_cylinder(
            radius=0.017,
            length=0.002,
            center=(center_x, 0.000, 0.000),
        )
        focus_wheel.visual(
            ridge_geom,
            origin=ridge_origin,
            material=trim_material,
            name=f"focus_ridge_{index}",
        )
    focus_wheel.inertial = Inertial.from_geometry(
        Box((0.022, 0.034, 0.034)),
        mass=0.08,
        origin=Origin(),
    )
    model.articulation(
        "focus_wheel_spin",
        ArticulationType.REVOLUTE,
        parent=right_barrel,
        child=focus_wheel,
        origin=Origin(xyz=(-0.040, 0.000, 0.030)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=1.0,
            velocity=10.0,
            lower=-6.0,
            upper=6.0,
        ),
    )

    compass_housing = model.part("compass_housing")
    compass_housing.visual(
        Cylinder(radius=0.016, length=0.010),
        origin=Origin(xyz=(0.000, 0.000, 0.005)),
        material=trim_material,
        name="compass_base",
    )
    compass_housing.visual(
        Cylinder(radius=0.013, length=0.002),
        origin=Origin(xyz=(0.000, 0.000, 0.010)),
        material=compass_dial_material,
        name="compass_dial",
    )
    compass_housing.visual(
        Box((0.018, 0.0022, 0.0012)),
        origin=Origin(xyz=(0.000, 0.000, 0.011)),
        material=compass_needle_material,
        name="compass_needle",
    )
    compass_housing.visual(
        Sphere(radius=0.015),
        origin=Origin(xyz=(0.000, 0.000, 0.018)),
        material=glass_material,
        name="compass_dome",
    )
    compass_housing.inertial = Inertial.from_geometry(
        Box((0.036, 0.036, 0.034)),
        mass=0.05,
        origin=Origin(xyz=(0.000, 0.000, 0.017)),
    )
    model.articulation(
        "compass_rotation",
        ArticulationType.REVOLUTE,
        parent=right_barrel,
        child=compass_housing,
        origin=Origin(xyz=(-0.012, 0.058, 0.029)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=0.5,
            velocity=2.5,
            lower=-0.9,
            upper=0.9,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
