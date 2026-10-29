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

# ===== primitives (1 syms) =====
class ConeGeometry(MeshGeometry):
    def __init__(self, radius, height, *, radial_segments=24, closed=True):
        super().__init__()
        radius = float(radius)
        height = float(height)
        # apex at +height/2 (radius 0), base radius `radius` at -height/2
        solid = cq.Solid.makeCone(
            radius, 0.0, height, cq.Vector(0, 0, -height / 2.0), cq.Vector(0, 0, 1)
        )
        self._set(solid)

# ===== model =====
import math
def _connect_rings(
    geom: MeshGeometry,
    ring_a: list[int],
    ring_b: list[int],
    *,
    flip: bool = False,
) -> None:
    count = len(ring_a)
    for i in range(count):
        a0 = ring_a[i]
        a1 = ring_a[(i + 1) % count]
        b0 = ring_b[i]
        b1 = ring_b[(i + 1) % count]
        if flip:
            geom.add_face(a0, b1, b0)
            geom.add_face(a0, a1, b1)
        else:
            geom.add_face(a0, b0, b1)
            geom.add_face(a0, b1, a1)
def _ring_vertices(
    geom: MeshGeometry, radius: float, z: float, segments: int
) -> list[int]:
    ring: list[int] = []
    for i in range(segments):
        angle = math.tau * i / segments
        ring.append(geom.add_vertex(radius * math.cos(angle), radius * math.sin(angle), z))
    return ring
def _revolve_shell(
    outer_profile: list[tuple[float, float]],
    inner_profile: list[tuple[float, float]],
    *,
    segments: int = 72,
    close_top: bool = True,
    close_bottom: bool = True,
) -> MeshGeometry:
    geom = MeshGeometry()

    outer_rings = [_ring_vertices(geom, radius, z, segments) for radius, z in outer_profile]
    inner_rings = [_ring_vertices(geom, radius, z, segments) for radius, z in inner_profile]

    for ring_a, ring_b in zip(outer_rings[:-1], outer_rings[1:]):
        _connect_rings(geom, ring_a, ring_b)
    for ring_a, ring_b in zip(inner_rings[:-1], inner_rings[1:]):
        _connect_rings(geom, ring_a, ring_b, flip=True)

    if close_top:
        _connect_rings(geom, outer_rings[0], inner_rings[0], flip=True)
    if close_bottom:
        _connect_rings(geom, inner_rings[-1], outer_rings[-1], flip=True)

    return geom
def _annular_band_mesh(
    *,
    outer_bottom: float,
    outer_top: float,
    inner_bottom: float,
    inner_top: float,
    z_bottom: float,
    z_top: float,
    name: str,
    segments: int = 72,
):
    return mesh_from_geometry(
        _revolve_shell(
            [(outer_bottom, z_bottom), (outer_top, z_top)],
            [(inner_bottom, z_bottom), (inner_top, z_top)],
            segments=segments,
            close_top=True,
            close_bottom=True,
        ),
        name,
    )
def _bell_shell_mesh():
    return mesh_from_geometry(
        _revolve_shell(
            [
                (0.12, -0.82),
                (0.20, -0.90),
                (0.36, -1.04),
                (0.52, -1.34),
                (0.62, -1.58),
            ],
            [
                (0.06, -0.84),
                (0.13, -0.92),
                (0.28, -1.08),
                (0.44, -1.36),
                (0.54, -1.54),
            ],
            segments=88,
            close_top=True,
            close_bottom=False,
        ),
        "bronze_bell_shell",
    )
def _polar_point(
    angle: float,
    radial: float,
    tangential: float,
    z: float,
) -> tuple[float, float, float]:
    ca = math.cos(angle)
    sa = math.sin(angle)
    return (
        radial * ca - tangential * sa,
        radial * sa + tangential * ca,
        z,
    )
def _add_radial_box(
    part,
    size: tuple[float, float, float],
    *,
    angle: float,
    radial: float,
    tangential: float,
    z: float,
    material,
    name: str | None = None,
) -> None:
    part.visual(
        Box(size),
        origin=Origin(xyz=_polar_point(angle, radial, tangential, z), rpy=(0.0, 0.0, angle)),
        material=material,
        name=name,
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="round_belfry_tower")

    stone = model.material("stone", rgba=(0.66, 0.66, 0.63, 1.0))
    stone_dark = model.material("stone_dark", rgba=(0.54, 0.54, 0.52, 1.0))
    roof_slate = model.material("roof_slate", rgba=(0.22, 0.23, 0.25, 1.0))
    oak = model.material("oak", rgba=(0.46, 0.30, 0.16, 1.0))
    aged_bronze = model.material("aged_bronze", rgba=(0.56, 0.38, 0.18, 1.0))
    dark_iron = model.material("dark_iron", rgba=(0.18, 0.18, 0.19, 1.0))

    lower_shell = _annular_band_mesh(
        outer_bottom=1.95,
        outer_top=1.82,
        inner_bottom=1.42,
        inner_top=1.40,
        z_bottom=0.38,
        z_top=6.55,
        name="tower_lower_shell",
    )
    sill_ring = _annular_band_mesh(
        outer_bottom=1.84,
        outer_top=1.80,
        inner_bottom=1.41,
        inner_top=1.40,
        z_bottom=6.55,
        z_top=6.80,
        name="tower_sill_ring",
    )
    cornice_ring = _annular_band_mesh(
        outer_bottom=1.83,
        outer_top=1.73,
        inner_bottom=1.40,
        inner_top=1.34,
        z_bottom=8.55,
        z_top=8.95,
        name="tower_cornice_ring",
    )
    roof_mesh = mesh_from_geometry(
        ConeGeometry(radius=1.55, height=1.55, radial_segments=72).translate(0.0, 0.0, 9.725),
        "tower_roof",
    )
    bell_shell = _bell_shell_mesh()

    tower = model.part("tower")
    tower.visual(
        Cylinder(radius=2.05, length=0.38),
        origin=Origin(xyz=(0.0, 0.0, 0.19)),
        material=stone_dark,
        name="plinth",
    )
    tower.visual(lower_shell, material=stone, name="shaft")
    tower.visual(sill_ring, material=stone_dark, name="sill_ring")

    window_angles = (0.0, math.pi / 2.0, math.pi, 3.0 * math.pi / 2.0)
    for idx, angle in enumerate(window_angles):
        _add_radial_box(
            tower,
            (0.42, 1.58, 0.16),
            angle=angle,
            radial=1.61,
            tangential=0.0,
            z=6.88,
            material=stone_dark,
            name=f"window_sill_{idx}",
        )
        for side, tangential in (("left", -0.63), ("right", 0.63)):
            _add_radial_box(
                tower,
                (0.42, 0.28, 1.33),
                angle=angle,
                radial=1.61,
                tangential=tangential,
                z=7.465,
                material=stone,
                name=f"{side}_jamb_{idx}",
            )

        arch_radius = 0.50
        arch_angles = (
            math.radians(160),
            math.radians(138),
            math.radians(116),
            math.radians(90),
            math.radians(64),
            math.radians(42),
            math.radians(20),
        )
        for stone_index, arch_angle in enumerate(arch_angles):
            _add_radial_box(
                tower,
                (0.42, 0.18, 0.22),
                angle=angle,
                radial=1.61,
                tangential=arch_radius * math.cos(arch_angle),
                z=8.05 + arch_radius * math.sin(arch_angle),
                material=stone,
                name=f"arch_stone_{idx}_{stone_index}",
            )

    for idx, angle in enumerate((math.pi / 4.0, 3.0 * math.pi / 4.0, 5.0 * math.pi / 4.0, 7.0 * math.pi / 4.0)):
        _add_radial_box(
            tower,
            (0.42, 0.84, 1.81),
            angle=angle,
            radial=1.61,
            tangential=0.0,
            z=7.675,
            material=stone,
            name=f"corner_pier_{idx}",
        )

    tower.visual(cornice_ring, material=stone_dark, name="cornice")
    tower.visual(roof_mesh, material=roof_slate, name="roof")
    tower.visual(
        Cylinder(radius=0.06, length=0.22),
        origin=Origin(xyz=(0.0, 0.0, 10.61)),
        material=roof_slate,
        name="finial",
    )
    tower.visual(
        Box((3.10, 0.20, 0.20)),
        origin=Origin(xyz=(0.0, 0.0, 8.56)),
        material=oak,
        name="tie_beam",
    )
    for idx, angle in enumerate((math.pi / 2.0, 3.0 * math.pi / 2.0)):
        _add_radial_box(
            tower,
            (0.36, 0.46, 0.82),
            angle=angle,
            radial=1.60,
            tangential=0.0,
            z=8.14,
            material=stone_dark,
            name=f"beam_socket_{idx}",
        )
    for side, y_sign in (("left", -1.0), ("right", 1.0)):
        for x_sign, suffix in ((-1.0, "inner"), (1.0, "outer")):
            tower.visual(
                Box((0.16, 0.64, 0.26)),
                origin=Origin(xyz=(x_sign * 0.14, y_sign * 1.18, 8.19)),
                material=oak,
                name=f"{side}_bearing_bracket_{suffix}",
            )
        tower.visual(
            Cylinder(radius=0.06, length=0.14),
            origin=Origin(
                xyz=(0.0, y_sign * 0.90, 8.28),
                rpy=(math.pi / 2.0, 0.0, 0.0),
            ),
            material=dark_iron,
            name=f"{side}_bearing",
        )

    bell = model.part("bell_yoke")
    bell.visual(
        Box((0.18, 1.52, 0.14)),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=oak,
        name="yoke_beam",
    )
    for side, y_sign in (("left", -1.0), ("right", 1.0)):
        bell.visual(
            Cylinder(radius=0.04, length=0.20),
            origin=Origin(
                xyz=(0.0, y_sign * 0.86, 0.0),
                rpy=(math.pi / 2.0, 0.0, 0.0),
            ),
            material=dark_iron,
            name=f"{side}_gudgeon",
        )
    for side, x_sign in (("front", 1.0), ("rear", -1.0)):
        bell.visual(
            Box((0.08, 0.20, 0.63)),
            origin=Origin(xyz=(x_sign * 0.13, 0.0, -0.385)),
            material=oak,
            name=f"{side}_yoke_cheek",
        )
    bell.visual(
        Box((0.18, 0.50, 0.12)),
        origin=Origin(xyz=(0.0, 0.0, -0.76)),
        material=oak,
        name="crown_block",
    )
    bell.visual(
        Cylinder(radius=0.07, length=0.08),
        origin=Origin(xyz=(0.0, 0.0, -0.86)),
        material=aged_bronze,
        name="crown_boss",
    )
    bell.visual(bell_shell, material=aged_bronze, name="bell_shell")
    for side, y_sign, x_web, x_eye in (("left", -1.0, 0.04, 0.012), ("right", 1.0, -0.04, -0.012)):
        bell.visual(
            Box((0.03, 0.04, 0.19)),
            origin=Origin(xyz=(x_web, y_sign * 0.09, -0.905)),
            material=dark_iron,
            name=f"{side}_hanger_web",
        )
        bell.visual(
            Cylinder(radius=0.028, length=0.05),
            origin=Origin(
                xyz=(x_eye, y_sign * 0.09, -1.00),
                rpy=(math.pi / 2.0, 0.0, 0.0),
            ),
            material=dark_iron,
            name=f"{side}_hanger_eye",
        )

    clapper = model.part("clapper")
    clapper.visual(
        Cylinder(radius=0.018, length=0.20),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_iron,
        name="clapper_pin",
    )
    clapper.visual(
        Cylinder(radius=0.016, length=0.20),
        origin=Origin(xyz=(0.0, 0.0, -0.10)),
        material=dark_iron,
        name="clapper_shank",
    )
    clapper.visual(
        Cylinder(radius=0.028, length=0.58),
        origin=Origin(xyz=(0.0, 0.0, -0.49)),
        material=dark_iron,
        name="clapper_rod",
    )
    clapper.visual(
        Cylinder(radius=0.05, length=0.12),
        origin=Origin(xyz=(0.0, 0.0, -0.84)),
        material=dark_iron,
        name="clapper_head",
    )
    clapper.visual(
        Sphere(radius=0.08),
        origin=Origin(xyz=(0.0, 0.0, -0.98)),
        material=dark_iron,
        name="clapper_bulb",
    )

    model.articulation(
        "tower_to_bell",
        ArticulationType.REVOLUTE,
        parent=tower,
        child=bell,
        origin=Origin(xyz=(0.0, 0.0, 8.28)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=220.0,
            velocity=1.0,
            lower=-0.78,
            upper=0.78,
        ),
    )
    model.articulation(
        "bell_to_clapper",
        ArticulationType.REVOLUTE,
        parent=bell,
        child=clapper,
        origin=Origin(xyz=(0.0, 0.0, -1.02)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=40.0,
            velocity=3.0,
            lower=-0.45,
            upper=0.45,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
