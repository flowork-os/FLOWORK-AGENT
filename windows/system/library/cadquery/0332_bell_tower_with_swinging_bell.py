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

# ===== model =====
import math
def _bearing_shell(inner_radius: float, outer_radius: float, length: float):
    _ = inner_radius
    return Cylinder(radius=outer_radius, length=length)
def _bell_shell():
    outer_profile = [
        (0.12, 0.00),
        (0.16, -0.03),
        (0.22, -0.12),
        (0.34, -0.30),
        (0.48, -0.66),
        (0.58, -0.98),
        (0.64, -1.18),
        (0.67, -1.30),
    ]
    inner_profile = [
        (0.08, -0.03),
        (0.13, -0.10),
        (0.22, -0.34),
        (0.34, -0.72),
        (0.47, -1.04),
        (0.57, -1.24),
    ]

    def ring(radius: float, z: float, segments: int) -> list[tuple[float, float, float]]:
        return [
            (
                radius * math.cos((2.0 * math.pi * i) / segments),
                radius * math.sin((2.0 * math.pi * i) / segments),
                z,
            )
            for i in range(segments)
        ]

    def add_ring(geom: MeshGeometry, pts: list[tuple[float, float, float]]) -> list[int]:
        return [geom.add_vertex(x, y, z) for x, y, z in pts]

    def bridge_rings(geom: MeshGeometry, ring_a: list[int], ring_b: list[int], flip: bool = False) -> None:
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

    geom = MeshGeometry()
    segments = 56

    outer_rings = [add_ring(geom, ring(radius, z, segments)) for radius, z in outer_profile]
    inner_rings = [add_ring(geom, ring(radius, z, segments)) for radius, z in inner_profile]

    for idx in range(len(outer_rings) - 1):
        bridge_rings(geom, outer_rings[idx], outer_rings[idx + 1], flip=False)
    for idx in range(len(inner_rings) - 1):
        bridge_rings(geom, inner_rings[idx + 1], inner_rings[idx], flip=False)

    bridge_rings(geom, outer_rings[0], inner_rings[0], flip=False)
    bridge_rings(geom, inner_rings[-1], outer_rings[-1], flip=False)

    return mesh_from_geometry(geom, "bronze_bell_shell")
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="english_parish_church_bell_tower")

    stone = model.material("stone", rgba=(0.68, 0.67, 0.63, 1.0))
    darker_stone = model.material("darker_stone", rgba=(0.60, 0.59, 0.55, 1.0))
    oak = model.material("oak", rgba=(0.45, 0.31, 0.17, 1.0))
    bronze = model.material("bronze", rgba=(0.61, 0.43, 0.19, 1.0))
    iron = model.material("iron", rgba=(0.22, 0.22, 0.24, 1.0))

    tower_width = 6.40
    wall_thickness = 0.75
    inner_clear = tower_width - (2.0 * wall_thickness)
    lower_stage_height = 12.65
    opening_bottom = 13.25
    opening_top = 15.45
    opening_height = opening_top - opening_bottom
    opening_width = 1.70
    upper_stage_top = 16.80
    parapet_height = 0.48
    merlon_height = 0.70
    tower_top = upper_stage_top + parapet_height + merlon_height

    tower = model.part("tower")
    tower.visual(
        Box((7.00, 7.00, 0.90)),
        origin=Origin(xyz=(0.0, 0.0, 0.45)),
        material=darker_stone,
        name="plinth",
    )

    for sign, face_name in ((1.0, "east"), (-1.0, "west")):
        tower.visual(
            Box((wall_thickness, tower_width, lower_stage_height)),
            origin=Origin(
                xyz=(sign * (0.5 * tower_width - 0.5 * wall_thickness), 0.0, 0.5 * lower_stage_height)
            ),
            material=stone,
            name=f"{face_name}_lower_wall",
        )
        tower.visual(
            Box((wall_thickness, tower_width, opening_bottom - lower_stage_height)),
            origin=Origin(
                xyz=(
                    sign * (0.5 * tower_width - 0.5 * wall_thickness),
                    0.0,
                    lower_stage_height + 0.5 * (opening_bottom - lower_stage_height),
                )
            ),
            material=stone,
            name=f"{face_name}_sill_wall",
        )
        tower.visual(
            Box((wall_thickness, 0.5 * (tower_width - opening_width), opening_height)),
            origin=Origin(
                xyz=(
                    sign * (0.5 * tower_width - 0.5 * wall_thickness),
                    0.25 * (tower_width + opening_width),
                    opening_bottom + 0.5 * opening_height,
                )
            ),
            material=stone,
            name=f"{face_name}_north_jamb",
        )
        tower.visual(
            Box((wall_thickness, 0.5 * (tower_width - opening_width), opening_height)),
            origin=Origin(
                xyz=(
                    sign * (0.5 * tower_width - 0.5 * wall_thickness),
                    -0.25 * (tower_width + opening_width),
                    opening_bottom + 0.5 * opening_height,
                )
            ),
            material=stone,
            name=f"{face_name}_south_jamb",
        )
        tower.visual(
            Box((wall_thickness, tower_width, upper_stage_top - opening_top)),
            origin=Origin(
                xyz=(
                    sign * (0.5 * tower_width - 0.5 * wall_thickness),
                    0.0,
                    opening_top + 0.5 * (upper_stage_top - opening_top),
                )
            ),
            material=stone,
            name=f"{face_name}_lintel_wall",
        )
        tower.visual(
            Box((wall_thickness, tower_width, parapet_height)),
            origin=Origin(
                xyz=(
                    sign * (0.5 * tower_width - 0.5 * wall_thickness),
                    0.0,
                    upper_stage_top + 0.5 * parapet_height,
                )
            ),
            material=stone,
            name=f"{face_name}_parapet",
        )

    for sign, face_name in ((1.0, "north"), (-1.0, "south")):
        tower.visual(
            Box((inner_clear, wall_thickness, lower_stage_height)),
            origin=Origin(
                xyz=(0.0, sign * (0.5 * tower_width - 0.5 * wall_thickness), 0.5 * lower_stage_height)
            ),
            material=stone,
            name=f"{face_name}_lower_wall",
        )
        tower.visual(
            Box((inner_clear, wall_thickness, opening_bottom - lower_stage_height)),
            origin=Origin(
                xyz=(
                    0.0,
                    sign * (0.5 * tower_width - 0.5 * wall_thickness),
                    lower_stage_height + 0.5 * (opening_bottom - lower_stage_height),
                )
            ),
            material=stone,
            name=f"{face_name}_sill_wall",
        )
        tower.visual(
            Box((0.5 * (tower_width - opening_width), wall_thickness, opening_height)),
            origin=Origin(
                xyz=(
                    0.25 * (tower_width + opening_width),
                    sign * (0.5 * tower_width - 0.5 * wall_thickness),
                    opening_bottom + 0.5 * opening_height,
                )
            ),
            material=stone,
            name=f"{face_name}_east_jamb",
        )
        tower.visual(
            Box((0.5 * (tower_width - opening_width), wall_thickness, opening_height)),
            origin=Origin(
                xyz=(
                    -0.25 * (tower_width + opening_width),
                    sign * (0.5 * tower_width - 0.5 * wall_thickness),
                    opening_bottom + 0.5 * opening_height,
                )
            ),
            material=stone,
            name=f"{face_name}_west_jamb",
        )
        tower.visual(
            Box((inner_clear, wall_thickness, upper_stage_top - opening_top)),
            origin=Origin(
                xyz=(
                    0.0,
                    sign * (0.5 * tower_width - 0.5 * wall_thickness),
                    opening_top + 0.5 * (upper_stage_top - opening_top),
                )
            ),
            material=stone,
            name=f"{face_name}_lintel_wall",
        )
        tower.visual(
            Box((inner_clear, wall_thickness, parapet_height)),
            origin=Origin(
                xyz=(
                    0.0,
                    sign * (0.5 * tower_width - 0.5 * wall_thickness),
                    upper_stage_top + 0.5 * parapet_height,
                )
            ),
            material=stone,
            name=f"{face_name}_parapet",
        )

    tower.visual(
        Box((inner_clear, inner_clear, 0.25)),
        origin=Origin(xyz=(0.0, 0.0, 12.55)),
        material=darker_stone,
        name="belfry_floor",
    )

    for sign_x, sign_y, corner_name in (
        (1.0, 1.0, "ne"),
        (1.0, -1.0, "se"),
        (-1.0, 1.0, "nw"),
        (-1.0, -1.0, "sw"),
    ):
        tower.visual(
            Box((0.90, 0.90, merlon_height)),
            origin=Origin(
                xyz=(
                    sign_x * (0.5 * tower_width - 0.45),
                    sign_y * (0.5 * tower_width - 0.45),
                    upper_stage_top + parapet_height + 0.5 * merlon_height,
                )
            ),
            material=stone,
            name=f"corner_merlon_{corner_name}",
        )

    for sign in (1.0, -1.0):
        tower.visual(
            Box((0.90, 0.80, merlon_height)),
            origin=Origin(
                xyz=(
                    sign * (0.5 * tower_width - 0.45),
                    0.0,
                    upper_stage_top + parapet_height + 0.5 * merlon_height,
                )
            ),
            material=stone,
            name=f"east_west_center_merlon_{int(sign)}",
        )
        tower.visual(
            Box((0.80, 0.90, merlon_height)),
            origin=Origin(
                xyz=(
                    0.0,
                    sign * (0.5 * tower_width - 0.45),
                    upper_stage_top + parapet_height + 0.5 * merlon_height,
                )
            ),
            material=stone,
            name=f"north_south_center_merlon_{int(sign)}",
        )

    band_depth = 0.92
    for sign, face_name in ((1.0, "east"), (-1.0, "west")):
        tower.visual(
            Box((band_depth, tower_width + 0.16, 0.18)),
            origin=Origin(
                xyz=(sign * (0.5 * tower_width - 0.5 * band_depth), 0.0, 12.62)
            ),
            material=darker_stone,
            name=f"{face_name}_stringcourse",
        )
    for sign, face_name in ((1.0, "north"), (-1.0, "south")):
        tower.visual(
            Box((inner_clear + 0.18, band_depth, 0.18)),
            origin=Origin(
                xyz=(0.0, sign * (0.5 * tower_width - 0.5 * band_depth), 12.62)
            ),
            material=darker_stone,
            name=f"{face_name}_stringcourse",
        )

    tower.inertial = Inertial.from_geometry(
        Box((7.0, 7.0, tower_top)),
        mass=180000.0,
        origin=Origin(xyz=(0.0, 0.0, 0.5 * tower_top)),
    )

    frame = model.part("belfry_frame")
    sill_z = -1.75
    axle_y = 1.18
    post_height = 2.55

    frame.visual(
        Box((inner_clear, 0.24, 0.24)),
        origin=Origin(xyz=(0.0, 0.96, sill_z)),
        material=oak,
        name="north_sill",
    )
    frame.visual(
        Box((inner_clear, 0.24, 0.24)),
        origin=Origin(xyz=(0.0, -0.96, sill_z)),
        material=oak,
        name="south_sill",
    )
    frame.visual(
        Box((0.24, 2.16, 0.24)),
        origin=Origin(xyz=(0.98, 0.0, sill_z)),
        material=oak,
        name="east_tie",
    )
    frame.visual(
        Box((0.24, 2.16, 0.24)),
        origin=Origin(xyz=(-0.98, 0.0, sill_z)),
        material=oak,
        name="west_tie",
    )

    for px, py, post_name in (
        (0.98, 0.96, "ne"),
        (0.98, -0.96, "se"),
        (-0.98, 0.96, "nw"),
        (-0.98, -0.96, "sw"),
    ):
        frame.visual(
            Box((0.18, 0.18, post_height)),
            origin=Origin(xyz=(px, py, sill_z + 0.12 + 0.5 * post_height)),
            material=oak,
            name=f"post_{post_name}",
        )

    frame.visual(
        Box((2.14, 0.26, 0.22)),
        origin=Origin(xyz=(0.0, axle_y, 0.20)),
        material=oak,
        name="north_head_beam_upper",
    )
    frame.visual(
        Box((2.14, 0.26, 0.22)),
        origin=Origin(xyz=(0.0, axle_y, -0.20)),
        material=oak,
        name="north_head_beam_lower",
    )
    frame.visual(
        Box((2.14, 0.26, 0.22)),
        origin=Origin(xyz=(0.0, -axle_y, 0.20)),
        material=oak,
        name="south_head_beam_upper",
    )
    frame.visual(
        Box((2.14, 0.26, 0.22)),
        origin=Origin(xyz=(0.0, -axle_y, -0.20)),
        material=oak,
        name="south_head_beam_lower",
    )
    frame.visual(
        _bearing_shell(0.058, 0.12, 0.16),
        origin=Origin(xyz=(0.0, axle_y, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=iron,
        name="left_bearing",
    )
    frame.visual(
        _bearing_shell(0.058, 0.12, 0.16),
        origin=Origin(xyz=(0.0, -axle_y, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=iron,
        name="right_bearing",
    )
    frame.inertial = Inertial.from_geometry(
        Box((inner_clear, 2.6, 2.9)),
        mass=3200.0,
        origin=Origin(xyz=(0.0, 0.0, -0.45)),
    )

    bell = model.part("bell_assembly")
    bell.visual(
        Cylinder(radius=0.058, length=3.04),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=iron,
        name="axle_shaft",
    )
    bell.visual(
        Box((0.34, 1.74, 0.32)),
        origin=Origin(xyz=(0.0, 0.0, -0.03)),
        material=oak,
        name="headstock",
    )
    bell.visual(
        _bell_shell(),
        origin=Origin(xyz=(0.0, 0.0, -0.23)),
        material=bronze,
        name="bell_shell",
    )
    for sx, sy, strap_name in (
        (0.11, 0.10, "ne"),
        (0.11, -0.10, "se"),
        (-0.11, 0.10, "nw"),
        (-0.11, -0.10, "sw"),
    ):
        bell.visual(
            Box((0.05, 0.12, 0.18)),
            origin=Origin(xyz=(sx, sy, -0.20)),
            material=iron,
            name=f"crown_strap_{strap_name}",
        )
    bell.visual(
        mesh_from_geometry(
            TorusGeometry(radius=0.47, tube=0.035, radial_segments=18, tubular_segments=56),
            "ringing_wheel_rim",
        ),
        origin=Origin(xyz=(0.0, 1.45, -0.02), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=oak,
        name="ringing_wheel",
    )
    bell.visual(
        Cylinder(radius=0.08, length=0.20),
        origin=Origin(xyz=(0.0, 1.45, -0.02), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=oak,
        name="wheel_hub",
    )
    for index, angle in enumerate((0.0, math.pi / 3.0, 2.0 * math.pi / 3.0)):
        bell.visual(
            Box((0.05, 0.05, 0.90)),
            origin=Origin(xyz=(0.0, 1.45, -0.02), rpy=(0.0, angle, 0.0)),
            material=oak,
            name=f"wheel_spoke_{index}",
        )
    bell.inertial = Inertial.from_geometry(
        Box((1.40, 3.10, 1.75)),
        mass=1550.0,
        origin=Origin(xyz=(0.0, 0.55, -0.55)),
    )

    model.articulation(
        "tower_to_frame",
        ArticulationType.FIXED,
        parent=tower,
        child=frame,
        origin=Origin(xyz=(0.0, 0.0, 15.0)),
    )
    model.articulation(
        "frame_to_bell",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=bell,
        origin=Origin(),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=4000.0,
            velocity=1.6,
            lower=-3.20,
            upper=3.20,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
