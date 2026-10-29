# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, casino_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: casino_machine

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
BUTTON_GUIDE_HALF_OPENING = 0.0225
BUTTON_GUIDE_WALL_THICKNESS = 0.006
BUTTON_GUIDE_HEIGHT = 0.080
BUTTON_GUIDE_OUTER_HALF = BUTTON_GUIDE_HALF_OPENING + BUTTON_GUIDE_WALL_THICKNESS
BUTTON_STEM_RADIUS = 0.019
BUTTON_GUIDE_CENTER_Z = 0.950
def _prism_from_yz_profile(
    width: float,
    yz_profile: list[tuple[float, float]],
    mesh_name: str,
):
    sections = []
    for x in (-0.5 * width, 0.5 * width):
        sections.append([(x, y, z) for y, z in yz_profile])
    return mesh_from_geometry(section_loft(sections), mesh_name)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="casino_cabinet")

    charcoal = model.material("charcoal", rgba=(0.12, 0.13, 0.15, 1.0))
    satin_black = model.material("satin_black", rgba=(0.06, 0.07, 0.08, 1.0))
    trim = model.material("trim", rgba=(0.32, 0.34, 0.38, 1.0))
    smoked_glass = model.material("smoked_glass", rgba=(0.18, 0.30, 0.34, 0.35))
    display_glow = model.material("display_glow", rgba=(0.10, 0.22, 0.34, 0.55))
    chrome = model.material("chrome", rgba=(0.72, 0.74, 0.78, 1.0))
    reel_white = model.material("reel_white", rgba=(0.92, 0.92, 0.90, 1.0))
    reel_band = model.material("reel_band", rgba=(0.82, 0.10, 0.14, 1.0))
    button_red = model.material("button_red", rgba=(0.86, 0.16, 0.18, 1.0))

    cabinet = model.part("cabinet")
    cabinet.visual(
        Box((0.84, 0.68, 0.10)),
        origin=Origin(xyz=(0.0, -0.01, 0.05)),
        material=charcoal,
        name="base_plinth",
    )
    cabinet.visual(
        Box((0.04, 0.62, 1.68)),
        origin=Origin(xyz=(-0.40, -0.01, 0.94)),
        material=charcoal,
        name="left_side_wall",
    )
    cabinet.visual(
        Box((0.04, 0.62, 1.68)),
        origin=Origin(xyz=(0.40, -0.01, 0.94)),
        material=charcoal,
        name="right_side_wall",
    )
    cabinet.visual(
        Box((0.76, 0.46, 0.03)),
        origin=Origin(xyz=(0.0, -0.05, 0.115)),
        material=satin_black,
        name="interior_floor",
    )
    cabinet.visual(
        Box((0.76, 0.04, 0.82)),
        origin=Origin(xyz=(0.0, -0.285, 1.45)),
        material=charcoal,
        name="rear_upper_wall",
    )
    cabinet.visual(
        Box((0.76, 0.03, 0.15)),
        origin=Origin(xyz=(0.0, -0.285, 0.21)),
        material=charcoal,
        name="rear_opening_sill",
    )
    cabinet.visual(
        Box((0.76, 0.03, 0.18)),
        origin=Origin(xyz=(0.0, -0.285, 1.00)),
        material=charcoal,
        name="rear_opening_lintel",
    )
    cabinet.visual(
        Box((0.08, 0.03, 0.62)),
        origin=Origin(xyz=(-0.34, -0.285, 0.60)),
        material=charcoal,
        name="back_left_jamb",
    )
    cabinet.visual(
        Box((0.08, 0.03, 0.62)),
        origin=Origin(xyz=(0.34, -0.285, 0.60)),
        material=charcoal,
        name="back_right_jamb",
    )
    cabinet.visual(
        Box((0.76, 0.04, 0.42)),
        origin=Origin(xyz=(0.0, 0.015, 1.12)),
        material=satin_black,
        name="reel_backboard",
    )
    cabinet.visual(
        Box((0.76, 0.03, 0.52)),
        origin=Origin(xyz=(0.0, -0.18, 1.56)),
        material=satin_black,
        name="display_backboard",
    )
    cabinet.visual(
        Box((0.76, 0.05, 0.22)),
        origin=Origin(xyz=(0.0, 0.18, 0.67)),
        material=charcoal,
        name="front_lower_fascia",
    )
    cabinet.visual(
        Box((0.05, 0.08, 0.46)),
        origin=Origin(xyz=(-0.355, 0.20, 1.12)),
        material=trim,
        name="reel_bezel_left",
    )
    cabinet.visual(
        Box((0.05, 0.08, 0.46)),
        origin=Origin(xyz=(0.355, 0.20, 1.12)),
        material=trim,
        name="reel_bezel_right",
    )
    cabinet.visual(
        Box((0.66, 0.08, 0.06)),
        origin=Origin(xyz=(0.0, 0.20, 1.32)),
        material=trim,
        name="reel_bezel_top",
    )
    cabinet.visual(
        Box((0.66, 0.08, 0.06)),
        origin=Origin(xyz=(0.0, 0.20, 0.92)),
        material=trim,
        name="reel_bezel_bottom",
    )
    cabinet.visual(
        Box((0.06, 0.08, 0.54)),
        origin=Origin(xyz=(-0.37, 0.10, 1.56)),
        material=trim,
        name="screen_bezel_left",
    )
    cabinet.visual(
        Box((0.06, 0.08, 0.54)),
        origin=Origin(xyz=(0.37, 0.10, 1.56)),
        material=trim,
        name="screen_bezel_right",
    )
    cabinet.visual(
        Box((0.68, 0.08, 0.06)),
        origin=Origin(xyz=(0.0, 0.10, 1.82)),
        material=trim,
        name="screen_bezel_top",
    )
    cabinet.visual(
        Box((0.68, 0.08, 0.06)),
        origin=Origin(xyz=(0.0, 0.10, 1.34)),
        material=trim,
        name="screen_bezel_bottom",
    )
    cabinet.visual(
        _prism_from_yz_profile(
            0.50,
            [
                (-0.12, -0.06),
                (0.09, -0.06),
                (0.16, 0.01),
                (0.10, 0.09),
                (-0.10, 0.11),
                (-0.14, 0.03),
            ],
            "control_deck_left_shell",
        ),
        origin=Origin(xyz=(-0.14, 0.18, 0.90)),
        material=charcoal,
        name="control_deck_left",
    )
    cabinet.visual(
        _prism_from_yz_profile(
            0.138,
            [
                (-0.12, -0.06),
                (0.09, -0.06),
                (0.16, 0.01),
                (0.10, 0.09),
                (-0.10, 0.11),
                (-0.14, 0.03),
            ],
            "control_deck_right_shell",
        ),
        origin=Origin(xyz=(0.331, 0.18, 0.90)),
        material=charcoal,
        name="control_deck_right",
    )
    cabinet.visual(
        Box((BUTTON_GUIDE_WALL_THICKNESS, 2.0 * BUTTON_GUIDE_OUTER_HALF, BUTTON_GUIDE_HEIGHT)),
        origin=Origin(
            xyz=(
                0.18 - BUTTON_GUIDE_HALF_OPENING - 0.5 * BUTTON_GUIDE_WALL_THICKNESS,
                0.27,
                BUTTON_GUIDE_CENTER_Z,
            )
        ),
        material=chrome,
        name="button_sleeve_left",
    )
    cabinet.visual(
        Box((BUTTON_GUIDE_WALL_THICKNESS, 2.0 * BUTTON_GUIDE_OUTER_HALF, BUTTON_GUIDE_HEIGHT)),
        origin=Origin(
            xyz=(
                0.18 + BUTTON_GUIDE_HALF_OPENING + 0.5 * BUTTON_GUIDE_WALL_THICKNESS,
                0.27,
                BUTTON_GUIDE_CENTER_Z,
            )
        ),
        material=chrome,
        name="button_sleeve_right",
    )
    cabinet.visual(
        Box((2.0 * BUTTON_GUIDE_OUTER_HALF, BUTTON_GUIDE_WALL_THICKNESS, BUTTON_GUIDE_HEIGHT)),
        origin=Origin(
            xyz=(
                0.18,
                0.27 - BUTTON_GUIDE_HALF_OPENING - 0.5 * BUTTON_GUIDE_WALL_THICKNESS,
                BUTTON_GUIDE_CENTER_Z,
            )
        ),
        material=chrome,
        name="button_sleeve_rear",
    )
    cabinet.visual(
        Box((2.0 * BUTTON_GUIDE_OUTER_HALF, BUTTON_GUIDE_WALL_THICKNESS, BUTTON_GUIDE_HEIGHT)),
        origin=Origin(
            xyz=(
                0.18,
                0.27 + BUTTON_GUIDE_HALF_OPENING + 0.5 * BUTTON_GUIDE_WALL_THICKNESS,
                BUTTON_GUIDE_CENTER_Z,
            )
        ),
        material=chrome,
        name="button_sleeve_front",
    )
    cabinet.visual(
        Box((0.064, 0.072, 0.050)),
        origin=Origin(xyz=(0.240, 0.270, 0.950)),
        material=satin_black,
        name="button_support_bridge",
    )
    cabinet.inertial = Inertial.from_geometry(
        Box((0.84, 0.68, 1.86)),
        mass=120.0,
        origin=Origin(xyz=(0.0, -0.01, 0.93)),
    )

    reel_window = model.part("reel_window")
    reel_window.visual(
        Box((0.70, 0.01, 0.20)),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=smoked_glass,
        name="window_glass",
    )
    reel_window.inertial = Inertial.from_geometry(
        Box((0.70, 0.01, 0.20)),
        mass=2.0,
    )
    model.articulation(
        "cabinet_to_reel_window",
        ArticulationType.FIXED,
        parent=cabinet,
        child=reel_window,
        origin=Origin(xyz=(0.0, 0.245, 1.12)),
    )

    upper_display = model.part("upper_display")
    upper_display.visual(
        Box((0.66, 0.01, 0.40)),
        material=display_glow,
        name="display_panel",
    )
    upper_display.inertial = Inertial.from_geometry(
        Box((0.66, 0.01, 0.40)),
        mass=2.2,
    )
    model.articulation(
        "cabinet_to_upper_display",
        ArticulationType.FIXED,
        parent=cabinet,
        child=upper_display,
        origin=Origin(xyz=(0.0, 0.145, 1.56)),
    )

    reel_x_positions = (-0.28, -0.14, 0.0, 0.14, 0.28)
    for index, x_pos in enumerate(reel_x_positions, start=1):
        cabinet.visual(
            Box((0.010, 0.106, 0.045)),
            origin=Origin(xyz=(x_pos - 0.068, 0.078, 1.12)),
            material=trim,
            name=f"reel_{index}_left_bearing",
        )
        cabinet.visual(
            Box((0.010, 0.106, 0.045)),
            origin=Origin(xyz=(x_pos + 0.068, 0.078, 1.12)),
            material=trim,
            name=f"reel_{index}_right_bearing",
        )
        reel = model.part(f"reel_{index}")
        reel.visual(
            Cylinder(radius=0.092, length=0.104),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=reel_white,
            name="reel_drum",
        )
        reel.visual(
            Cylinder(radius=0.014, length=0.126),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=chrome,
            name="shaft",
        )
        reel.visual(
            Cylinder(radius=0.095, length=0.010),
            origin=Origin(xyz=(-0.047, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=reel_band,
            name="left_flange",
        )
        reel.visual(
            Cylinder(radius=0.095, length=0.010),
            origin=Origin(xyz=(0.047, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=reel_band,
            name="right_flange",
        )
        reel.inertial = Inertial.from_geometry(
            Cylinder(radius=0.095, length=0.126),
            mass=1.2,
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        )
        model.articulation(
            f"cabinet_to_reel_{index}",
            ArticulationType.CONTINUOUS,
            parent=cabinet,
            child=reel,
            origin=Origin(xyz=(x_pos, 0.140, 1.12)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=6.0, velocity=18.0),
        )

    spin_button = model.part("spin_button")
    spin_button.visual(
        Cylinder(radius=0.055, length=0.020),
        origin=Origin(xyz=(0.0, 0.0, 0.022)),
        material=button_red,
        name="button_cap",
    )
    spin_button.visual(
        Cylinder(radius=BUTTON_GUIDE_HALF_OPENING, length=0.020),
        origin=Origin(xyz=(0.0, 0.0, 0.010)),
        material=chrome,
        name="button_collar",
    )
    spin_button.visual(
        Cylinder(radius=BUTTON_STEM_RADIUS, length=0.095),
        origin=Origin(xyz=(0.0, 0.0, -0.0375)),
        material=chrome,
        name="button_stem",
    )
    spin_button.inertial = Inertial.from_geometry(
        Cylinder(radius=0.055, length=0.115),
        mass=0.35,
        origin=Origin(xyz=(0.0, 0.0, -0.005)),
    )
    model.articulation(
        "cabinet_to_spin_button",
        ArticulationType.PRISMATIC,
        parent=cabinet,
        child=spin_button,
        origin=Origin(xyz=(0.18, 0.27, 0.98)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=30.0,
            velocity=0.15,
            lower=0.0,
            upper=0.012,
        ),
    )

    maintenance_panel = model.part("maintenance_panel")
    maintenance_panel.visual(
        Box((0.598, 0.018, 0.618)),
        origin=Origin(xyz=(-0.299, 0.0, 0.0)),
        material=satin_black,
        name="panel_leaf",
    )
    maintenance_panel.visual(
        Box((0.040, 0.028, 0.110)),
        origin=Origin(xyz=(-0.530, -0.023, 0.0)),
        material=trim,
        name="panel_handle",
    )
    maintenance_panel.inertial = Inertial.from_geometry(
        Box((0.62, 0.03, 0.62)),
        mass=8.0,
        origin=Origin(xyz=(-0.31, 0.0, 0.0)),
    )
    model.articulation(
        "cabinet_to_maintenance_panel",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=maintenance_panel,
        origin=Origin(xyz=(0.30, -0.309, 0.60)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=1.2,
            lower=0.0,
            upper=1.25,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
