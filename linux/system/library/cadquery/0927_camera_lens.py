# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_lens, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_lens

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
def _quad(mesh: MeshGeometry, a: int, b: int, c: int, d: int) -> None:
    mesh.add_face(a, b, c)
    mesh.add_face(a, c, d)
def _profiled_annular_mesh(
    outer_profile: list[tuple[float, float]],
    inner_profile: list[tuple[float, float]],
    *,
    radial_segments: int = 96,
) -> MeshGeometry:
    """Build a hollow rotational shell whose axis is the local +X direction."""
    mesh = MeshGeometry()
    outer: list[list[int]] = []
    inner: list[list[int]] = []

    for x, radius in outer_profile:
        ring = []
        for i in range(radial_segments):
            theta = 2.0 * math.pi * i / radial_segments
            ring.append(mesh.add_vertex(x, radius * math.cos(theta), radius * math.sin(theta)))
        outer.append(ring)

    for x, radius in inner_profile:
        ring = []
        for i in range(radial_segments):
            theta = 2.0 * math.pi * i / radial_segments
            ring.append(mesh.add_vertex(x, radius * math.cos(theta), radius * math.sin(theta)))
        inner.append(ring)

    for rings in (outer, inner):
        for s in range(len(rings) - 1):
            for i in range(radial_segments):
                j = (i + 1) % radial_segments
                if rings is outer:
                    _quad(mesh, rings[s][i], rings[s + 1][i], rings[s + 1][j], rings[s][j])
                else:
                    _quad(mesh, rings[s][j], rings[s + 1][j], rings[s + 1][i], rings[s][i])

    for i in range(radial_segments):
        j = (i + 1) % radial_segments
        _quad(mesh, inner[0][i], outer[0][i], outer[0][j], inner[0][j])
        _quad(mesh, outer[-1][i], inner[-1][i], inner[-1][j], outer[-1][j])

    return mesh
def _ribbed_focus_ring_mesh(
    *,
    length: float,
    inner_radius: float,
    base_radius: float,
    rib_radius: float,
    rib_count: int = 48,
    radial_segments: int = 192,
) -> MeshGeometry:
    """A hollow rubber ring with lengthwise raised grip ribs."""
    mesh = MeshGeometry()
    x_values = (-length / 2.0, -length * 0.38, length * 0.38, length / 2.0)
    outer: list[list[int]] = []
    inner: list[list[int]] = []

    def radius_at(index: int) -> float:
        phase = (index * rib_count / radial_segments) % 1.0
        return rib_radius if phase < 0.38 else base_radius

    for x in x_values:
        outer_ring = []
        inner_ring = []
        for i in range(radial_segments):
            theta = 2.0 * math.pi * i / radial_segments
            c, s = math.cos(theta), math.sin(theta)
            outer_ring.append(mesh.add_vertex(x, radius_at(i) * c, radius_at(i) * s))
            inner_ring.append(mesh.add_vertex(x, inner_radius * c, inner_radius * s))
        outer.append(outer_ring)
        inner.append(inner_ring)

    for s in range(len(x_values) - 1):
        for i in range(radial_segments):
            j = (i + 1) % radial_segments
            _quad(mesh, outer[s][i], outer[s + 1][i], outer[s + 1][j], outer[s][j])
            _quad(mesh, inner[s][j], inner[s + 1][j], inner[s + 1][i], inner[s][i])

    for i in range(radial_segments):
        j = (i + 1) % radial_segments
        _quad(mesh, inner[0][i], outer[0][i], outer[0][j], inner[0][j])
        _quad(mesh, outer[-1][i], inner[-1][i], inner[-1][j], outer[-1][j])

    return mesh
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="macro_lens")

    satin_black = model.material("satin_black", rgba=(0.015, 0.016, 0.017, 1.0))
    rubber = model.material("matte_rubber", rgba=(0.005, 0.005, 0.005, 1.0))
    gunmetal = model.material("gunmetal", rgba=(0.18, 0.18, 0.17, 1.0))
    coated_glass = model.material("coated_glass", rgba=(0.08, 0.18, 0.26, 0.55))
    red_mark = model.material("red_macro_mark", rgba=(0.75, 0.02, 0.015, 1.0))

    body = model.part("body")
    body_shell = _profiled_annular_mesh(
        [
            (-0.060, 0.0370),
            (-0.056, 0.0400),
            (-0.052, 0.0400),
            (-0.048, 0.0365),
            (-0.034, 0.0365),
            (-0.030, 0.0358),
            (0.030, 0.0358),
            (0.034, 0.0365),
            (0.052, 0.0365),
        ],
        [
            (-0.060, 0.0308),
            (-0.056, 0.0308),
            (-0.052, 0.0308),
            (-0.048, 0.0308),
            (-0.034, 0.0308),
            (-0.030, 0.0308),
            (0.030, 0.0308),
            (0.034, 0.0308),
            (0.052, 0.0308),
        ],
    )
    body.visual(mesh_from_geometry(body_shell, "body_shell"), material=satin_black, name="body_shell")

    accent_band = _profiled_annular_mesh(
        [(-0.0470, 0.0366), (-0.0445, 0.0377)],
        [(-0.0470, 0.0360), (-0.0445, 0.0360)],
        radial_segments=96,
    )
    body.visual(mesh_from_geometry(accent_band, "macro_mark"), material=red_mark, name="macro_mark")

    focus_ring = model.part("focus_ring")
    focus_ring.visual(
        mesh_from_geometry(
            _ribbed_focus_ring_mesh(
                length=0.060,
                inner_radius=0.0363,
                base_radius=0.0415,
                rib_radius=0.0440,
            ),
            "ribbed_focus_ring",
        ),
        material=rubber,
        name="ribbed_grip",
    )
    for pad_name, z in (("ring_bearing_pad_top", 0.0359), ("ring_bearing_pad_bottom", -0.0359)):
        focus_ring.visual(
            Box((0.010, 0.006, 0.0012)),
            origin=Origin(xyz=(0.0, 0.0, z)),
            material=rubber,
            name=pad_name,
        )

    extension_barrel = model.part("extension_barrel")
    extension_tube = _profiled_annular_mesh(
        [
            (-0.055, 0.0285),
            (-0.050, 0.0285),
            (0.024, 0.0288),
            (0.028, 0.0305),
            (0.035, 0.0305),
        ],
        [
            (-0.055, 0.0205),
            (-0.050, 0.0205),
            (0.024, 0.0205),
            (0.028, 0.0205),
            (0.035, 0.0205),
        ],
    )
    extension_barrel.visual(
        mesh_from_geometry(extension_tube, "extension_tube"),
        material=gunmetal,
        name="extension_tube",
    )
    for pad_name, z in (("barrel_guide_pad_top", 0.0296), ("barrel_guide_pad_bottom", -0.0296)):
        extension_barrel.visual(
            Box((0.012, 0.005, 0.0032)),
            origin=Origin(xyz=(-0.047, 0.0, z)),
            material=gunmetal,
            name=pad_name,
        )
    extension_barrel.visual(
        Cylinder(radius=0.0210, length=0.004),
        origin=Origin(xyz=(0.033, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=coated_glass,
        name="front_glass",
    )

    model.articulation(
        "body_to_focus_ring",
        ArticulationType.REVOLUTE,
        parent=body,
        child=focus_ring,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.6, velocity=2.0, lower=-2.2, upper=2.2),
    )

    model.articulation(
        "body_to_extension_barrel",
        ArticulationType.PRISMATIC,
        parent=body,
        child=extension_barrel,
        origin=Origin(xyz=(0.046, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=0.08, lower=0.0, upper=0.034),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
