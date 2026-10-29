# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, astronomical_telescope_on_tripod, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: astronomical_telescope_on_tripod

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
def _open_tube_shell_geometry(
    outer_radius: float,
    inner_radius: float,
    length: float,
    *,
    segments: int = 56,
) -> MeshGeometry:
    geom = MeshGeometry()
    half_length = length * 0.5

    outer_back: list[int] = []
    outer_front: list[int] = []
    inner_back: list[int] = []
    inner_front: list[int] = []

    for index in range(segments):
        angle = (2.0 * math.pi * index) / segments
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        outer_back.append(geom.add_vertex(outer_radius * cos_a, outer_radius * sin_a, -half_length))
        outer_front.append(geom.add_vertex(outer_radius * cos_a, outer_radius * sin_a, half_length))
        inner_back.append(geom.add_vertex(inner_radius * cos_a, inner_radius * sin_a, -half_length))
        inner_front.append(geom.add_vertex(inner_radius * cos_a, inner_radius * sin_a, half_length))

    for index in range(segments):
        nxt = (index + 1) % segments

        geom.add_face(outer_back[index], outer_back[nxt], outer_front[nxt])
        geom.add_face(outer_back[index], outer_front[nxt], outer_front[index])

        geom.add_face(inner_back[index], inner_front[nxt], inner_back[nxt])
        geom.add_face(inner_back[index], inner_front[index], inner_front[nxt])

        geom.add_face(outer_back[index], inner_back[nxt], outer_back[nxt])
        geom.add_face(outer_back[index], inner_back[index], inner_back[nxt])

        geom.add_face(outer_front[index], outer_front[nxt], inner_front[nxt])
        geom.add_face(outer_front[index], inner_front[nxt], inner_front[index])

    return geom
def _tube_shell_mesh(
    name: str,
    outer_radius: float,
    inner_radius: float,
    length: float,
    *,
    segments: int = 56,
):
    return mesh_from_geometry(
        _open_tube_shell_geometry(
            outer_radius,
            inner_radius,
            length,
            segments=segments,
        ),
        name,
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="video_astronomy_telescope")

    tripod_dark = model.material("tripod_dark", rgba=(0.16, 0.17, 0.18, 1.0))
    aluminum = model.material("aluminum", rgba=(0.68, 0.70, 0.73, 1.0))
    mount_dark = model.material("mount_dark", rgba=(0.11, 0.12, 0.13, 1.0))
    tube_white = model.material("tube_white", rgba=(0.92, 0.93, 0.94, 1.0))
    optics_gray = model.material("optics_gray", rgba=(0.56, 0.59, 0.63, 1.0))
    camera_black = model.material("camera_black", rgba=(0.07, 0.08, 0.09, 1.0))

    tripod = model.part("tripod")
    tripod.visual(
        Cylinder(radius=0.135, length=0.022),
        origin=Origin(xyz=(0.0, 0.0, -0.011)),
        material=tripod_dark,
        name="head_plate",
    )
    tripod.visual(
        Cylinder(radius=0.072, length=0.048),
        origin=Origin(xyz=(0.0, 0.0, -0.035)),
        material=tripod_dark,
        name="azimuth_pier",
    )
    tripod.visual(
        Cylinder(radius=0.048, length=0.12),
        origin=Origin(xyz=(0.0, 0.0, -0.095)),
        material=tripod_dark,
        name="center_hub",
    )

    leg_length = 0.95
    leg_radius = 0.019
    top_radius = 0.108
    foot_radius = 0.52
    top_z = -0.026
    foot_z = -0.94
    for index, angle in enumerate((0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0), start=1):
        top = (top_radius * math.cos(angle), top_radius * math.sin(angle), top_z)
        foot = (foot_radius * math.cos(angle), foot_radius * math.sin(angle), foot_z)
        ux = top[0] - foot[0]
        uy = top[1] - foot[1]
        uz = top[2] - foot[2]
        yaw = math.atan2(uy, ux)
        pitch = math.atan2(math.hypot(ux, uy), uz)

        tripod.visual(
            Cylinder(radius=leg_radius, length=leg_length),
            origin=Origin(
                xyz=(
                    0.5 * (top[0] + foot[0]),
                    0.5 * (top[1] + foot[1]),
                    0.5 * (top[2] + foot[2]),
                ),
                rpy=(0.0, pitch, yaw),
            ),
            material=aluminum,
            name=f"leg_{index}_tube",
        )
        tripod.visual(
            Box((0.065, 0.038, 0.03)),
            origin=Origin(
                xyz=(
                    (top_radius + 0.014) * math.cos(angle),
                    (top_radius + 0.014) * math.sin(angle),
                    -0.031,
                ),
                rpy=(0.0, 0.0, angle),
            ),
            material=tripod_dark,
            name=f"leg_clamp_{index}",
        )

    mount_arm = model.part("mount_arm")
    mount_arm.visual(
        Cylinder(radius=0.105, length=0.05),
        origin=Origin(xyz=(0.0, 0.0, 0.025)),
        material=mount_dark,
        name="azimuth_turntable",
    )
    mount_arm.visual(
        Box((0.16, 0.20, 0.16)),
        origin=Origin(xyz=(0.05, 0.0, 0.10)),
        material=mount_dark,
        name="drive_body",
    )
    mount_arm.visual(
        Box((0.08, 0.13, 0.36)),
        origin=Origin(xyz=(0.08, 0.0, 0.26)),
        material=mount_dark,
        name="single_arm",
    )
    mount_arm.visual(
        Cylinder(radius=0.036, length=0.24),
        origin=Origin(xyz=(0.04, 0.0, 0.18), rpy=(0.0, 0.32, 0.0)),
        material=mount_dark,
        name="arm_brace",
    )
    mount_arm.visual(
        Cylinder(radius=0.055, length=0.12),
        origin=Origin(xyz=(0.085, 0.0, 0.43), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=mount_dark,
        name="altitude_hub",
    )
    mount_arm.visual(
        Box((0.07, 0.24, 0.05)),
        origin=Origin(xyz=(0.035, 0.0, 0.43)),
        material=mount_dark,
        name="saddle_block",
    )

    optical_tube = model.part("optical_tube")
    optical_tube.visual(
        _tube_shell_mesh("ota_shell", 0.115, 0.105, 0.68),
        origin=Origin(xyz=(-0.154, 0.0, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=tube_white,
        name="ota_shell",
    )
    optical_tube.visual(
        Box((0.026, 0.40, 0.018)),
        origin=Origin(xyz=(-0.013, 0.0, 0.0)),
        material=mount_dark,
        name="ota_dovetail",
    )
    optical_tube.visual(
        _tube_shell_mesh("front_ring_band", 0.127, 0.118, 0.028),
        origin=Origin(xyz=(-0.154, -0.14, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=mount_dark,
        name="front_ring_band",
    )
    optical_tube.visual(
        _tube_shell_mesh("rear_ring_band", 0.127, 0.118, 0.028),
        origin=Origin(xyz=(-0.154, 0.14, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=mount_dark,
        name="rear_ring_band",
    )
    optical_tube.visual(
        Box((0.078, 0.08, 0.03)),
        origin=Origin(xyz=(-0.039, -0.14, 0.0)),
        material=mount_dark,
        name="front_ring_block",
    )
    optical_tube.visual(
        Box((0.078, 0.08, 0.03)),
        origin=Origin(xyz=(-0.039, 0.14, 0.0)),
        material=mount_dark,
        name="rear_ring_block",
    )
    optical_tube.visual(
        _tube_shell_mesh("primary_cell", 0.112, 0.100, 0.055),
        origin=Origin(xyz=(-0.154, 0.31, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=mount_dark,
        name="primary_cell",
    )
    optical_tube.visual(
        Cylinder(radius=0.102, length=0.018),
        origin=Origin(xyz=(-0.154, 0.302, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=optics_gray,
        name="primary_mirror",
    )
    optical_tube.visual(
        Box((0.216, 0.004, 0.006)),
        origin=Origin(xyz=(-0.154, -0.19, 0.0)),
        material=mount_dark,
        name="secondary_spider_x",
    )
    optical_tube.visual(
        Box((0.006, 0.004, 0.216)),
        origin=Origin(xyz=(-0.154, -0.19, 0.0)),
        material=mount_dark,
        name="secondary_spider_z",
    )
    optical_tube.visual(
        Cylinder(radius=0.015, length=0.04),
        origin=Origin(xyz=(-0.154, -0.19, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=mount_dark,
        name="secondary_holder",
    )
    optical_tube.visual(
        Box((0.068, 0.052, 0.03)),
        origin=Origin(xyz=(-0.154, -0.09, 0.111)),
        material=mount_dark,
        name="focuser_base",
    )
    optical_tube.visual(
        Cylinder(radius=0.027, length=0.092),
        origin=Origin(xyz=(-0.154, -0.09, 0.172)),
        material=mount_dark,
        name="focuser_drawtube",
    )
    optical_tube.visual(
        Cylinder(radius=0.034, length=0.112),
        origin=Origin(xyz=(-0.154, -0.09, 0.252)),
        material=camera_black,
        name="camera_body",
    )
    optical_tube.visual(
        Box((0.078, 0.062, 0.032)),
        origin=Origin(xyz=(-0.154, -0.09, 0.318)),
        material=camera_black,
        name="camera_heat_sink",
    )

    model.articulation(
        "tripod_to_mount",
        ArticulationType.CONTINUOUS,
        parent=tripod,
        child=mount_arm,
        origin=Origin(),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=30.0, velocity=1.2),
    )
    model.articulation(
        "mount_to_optical_tube",
        ArticulationType.REVOLUTE,
        parent=mount_arm,
        child=optical_tube,
        origin=Origin(xyz=(0.0, 0.0, 0.43)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=20.0,
            velocity=0.8,
            lower=-0.45,
            upper=1.40,
        ),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
