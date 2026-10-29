# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bicycle_dropper_seatpost_assembly, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bicycle_dropper_seatpost_assembly

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

class _NoOp:
    """Universal no-op sentinel that is callable AND Path-like, so asset/IO
    expressions in model scripts (e.g. ASSETS.mesh_dir.mkdir(); dir / 'x.obj')
    are harmless in self-contained mode."""
    def __call__(self, *a, **k):
        return self

    def __getattr__(self, _n):
        return self

    def __truediv__(self, _o):
        return self

    def __rtruediv__(self, _o):
        return self

    def __fspath__(self):
        return "/tmp/_articraft_noop"

    def mkdir(self, *a, **k):
        return None

_NOOP = _NoOp()

class _NoopMeta(type):
    def __getattr__(cls, _name):
        def _noop(*a, **k):
            return cls()
        return _noop

class AssetContext(metaclass=_NoopMeta):
    def __init__(self, *a, **k):
        pass

    def __getattr__(self, _n):
        return _NOOP

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

def boolean_difference(a, b, *more):
    s = _to_shape(a).cut(_to_shape(b))
    for m in more:
        s = s.cut(_to_shape(m))
    return MeshGeometry()._set(s)

# ===== primitives (2 syms) =====
class BoxGeometry(MeshGeometry):
    def __init__(self, size):
        super().__init__()
        x, y, z = (float(size[0]), float(size[1]), float(size[2]))
        solid = cq.Solid.makeBox(x, y, z, cq.Vector(-x / 2.0, -y / 2.0, -z / 2.0))
        self._set(solid)

class CylinderGeometry(MeshGeometry):
    def __init__(self, radius, height, *, radial_segments=24, closed=True):
        super().__init__()
        radius = float(radius)
        height = float(height)
        solid = cq.Solid.makeCylinder(
            radius, height, cq.Vector(0, 0, -height / 2.0), cq.Vector(0, 0, 1)
        )
        self._set(solid)

# ===== model =====
import math
ASSETS = AssetContext.from_script(__file__)
def _save_mesh(name: str, geometry):
    return mesh_from_geometry(geometry, ASSETS.mesh_path(name))
def _ring_shell(
    *,
    outer_radius: float,
    inner_radius: float,
    height: float,
    z_center: float = 0.0,
    radial_segments: int = 64,
):
    outer = CylinderGeometry(radius=outer_radius, height=height, radial_segments=radial_segments)
    inner = CylinderGeometry(
        radius=inner_radius,
        height=height + 0.002,
        radial_segments=radial_segments,
    )
    return boolean_difference(outer, inner).translate(0.0, 0.0, z_center)
def _build_collar_core():
    collar = _ring_shell(
        outer_radius=0.0238,
        inner_radius=0.0189,
        height=0.028,
        z_center=0.014,
        radial_segments=72,
    )
    port_cut = BoxGeometry((0.018, 0.012, 0.010)).translate(-0.021, 0.0, 0.012)
    return boolean_difference(collar, port_cut)
def _add_knurl_rows(part, material, *, x_offset: float = 0.0) -> None:
    ridge_radius = 0.0230
    ridge_size = (0.0036, 0.0042, 0.007)
    row_centers = (0.009, 0.019)
    count = 20
    for row_index, z_center in enumerate(row_centers):
        angle_offset = (math.pi / count) if row_index else 0.0
        for index in range(count):
            angle = angle_offset + (2.0 * math.pi * index / count)
            part.visual(
                Box(ridge_size),
                origin=Origin(
                    xyz=(
                        x_offset + ridge_radius * math.cos(angle),
                        ridge_radius * math.sin(angle),
                        z_center,
                    ),
                    rpy=(0.0, 0.0, angle),
                ),
                material=material,
                name=f"knurl_{row_index}_{index:02d}",
            )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="mechanical_dropper_seatpost", assets=ASSETS)

    black_anodized = model.material("black_anodized", rgba=(0.09, 0.10, 0.11, 1.0))
    satin_black = model.material("satin_black", rgba=(0.15, 0.16, 0.18, 1.0))
    alloy = model.material("alloy", rgba=(0.72, 0.74, 0.77, 1.0))
    hardware = model.material("hardware", rgba=(0.26, 0.28, 0.31, 1.0))
    port_dark = model.material("port_dark", rgba=(0.04, 0.04, 0.05, 1.0))

    main_tube_mesh = _save_mesh(
        "dropper_main_tube.obj",
        _ring_shell(
            outer_radius=0.0158,
            inner_radius=0.0137,
            height=0.348,
            z_center=0.174,
            radial_segments=72,
        ),
    )
    upper_head_mesh = _save_mesh(
        "dropper_upper_head.obj",
        _ring_shell(
            outer_radius=0.0192,
            inner_radius=0.0142,
            height=0.072,
            z_center=0.384,
            radial_segments=72,
        ),
    )
    guide_bushing_mesh = _save_mesh(
        "dropper_guide_bushing.obj",
        _ring_shell(
            outer_radius=0.0142,
            inner_radius=0.0127,
            height=0.014,
            z_center=0.413,
            radial_segments=72,
        ),
    )
    seal_ring_mesh = _save_mesh(
        "dropper_seal_ring.obj",
        _ring_shell(
            outer_radius=0.0182,
            inner_radius=0.0129,
            height=0.010,
            z_center=0.425,
            radial_segments=72,
        ),
    )
    collar_core_mesh = _save_mesh("dropper_collar_core.obj", _build_collar_core())

    lower_body = model.part("lower_body")
    lower_body.visual(main_tube_mesh, material=black_anodized, name="main_tube")
    lower_body.visual(upper_head_mesh, material=satin_black, name="upper_head")
    lower_body.visual(guide_bushing_mesh, material=alloy, name="guide_bushing")
    lower_body.visual(seal_ring_mesh, material=hardware, name="seal_ring")
    lower_body.inertial = Inertial.from_geometry(
        Cylinder(radius=0.0195, length=0.430),
        mass=0.62,
        origin=Origin(xyz=(0.0, 0.0, 0.215)),
    )

    collar = model.part("collar")
    collar.visual(collar_core_mesh, origin=Origin(xyz=(0.019, 0.0, 0.0)), material=alloy, name="collar_ring")
    _add_knurl_rows(collar, alloy, x_offset=0.019)
    collar.inertial = Inertial.from_geometry(
        Cylinder(radius=0.024, length=0.028),
        mass=0.08,
        origin=Origin(xyz=(0.019, 0.0, 0.014)),
    )

    actuation_port = model.part("actuation_port")
    actuation_port.visual(
        Cylinder(radius=0.005, length=0.010),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=port_dark,
        name="port_sleeve",
    )
    actuation_port.visual(
        Box((0.005, 0.010, 0.008)),
        origin=Origin(xyz=(0.001, 0.0, 0.0)),
        material=hardware,
        name="port_stop",
    )
    actuation_port.inertial = Inertial.from_geometry(
        Box((0.014, 0.012, 0.012)),
        mass=0.015,
        origin=Origin(),
    )

    inner_tube = model.part("inner_tube")
    inner_tube.visual(
        Cylinder(radius=0.0127, length=0.320),
        origin=Origin(xyz=(0.0, 0.0, 0.020)),
        material=black_anodized,
        name="stanchion",
    )
    inner_tube.visual(
        Cylinder(radius=0.0138, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, 0.185)),
        material=hardware,
        name="top_cap",
    )
    inner_tube.inertial = Inertial.from_geometry(
        Cylinder(radius=0.0138, length=0.330),
        mass=0.34,
        origin=Origin(xyz=(0.0, 0.0, 0.025)),
    )

    saddle_clamp = model.part("saddle_clamp")
    saddle_clamp.visual(
        Box((0.050, 0.018, 0.012)),
        origin=Origin(xyz=(-0.018, 0.0, 0.006)),
        material=satin_black,
        name="bridge_arm",
    )
    saddle_clamp.visual(
        Box((0.044, 0.024, 0.010)),
        origin=Origin(xyz=(-0.052, 0.0, 0.022)),
        material=satin_black,
        name="rear_cradle",
    )
    saddle_clamp.visual(
        Box((0.016, 0.018, 0.012)),
        origin=Origin(xyz=(-0.034, 0.0, 0.014)),
        material=satin_black,
        name="setback_yoke",
    )
    saddle_clamp.visual(
        Box((0.036, 0.018, 0.008)),
        origin=Origin(xyz=(-0.052, 0.0, 0.036)),
        material=alloy,
        name="upper_plate",
    )
    for x_pos, name_prefix in ((-0.064, "rear"), (-0.040, "front")):
        for side, y_pos in (("left", -0.012), ("right", 0.012)):
            saddle_clamp.visual(
                Cylinder(radius=0.003, length=0.020),
                origin=Origin(xyz=(x_pos, y_pos, 0.028)),
                material=hardware,
                name=f"{name_prefix}_bolt_{side}",
            )
    saddle_clamp.inertial = Inertial.from_geometry(
        Box((0.080, 0.032, 0.046)),
        mass=0.12,
        origin=Origin(xyz=(-0.040, 0.0, 0.023)),
    )

    model.articulation(
        "body_to_collar",
        ArticulationType.FIXED,
        parent=lower_body,
        child=collar,
        origin=Origin(xyz=(-0.019, 0.0, 0.392)),
    )
    model.articulation(
        "collar_to_port",
        ArticulationType.FIXED,
        parent=collar,
        child=actuation_port,
        origin=Origin(xyz=(-0.006, 0.0, 0.012)),
    )
    model.articulation(
        "stanchion_travel",
        ArticulationType.PRISMATIC,
        parent=lower_body,
        child=inner_tube,
        origin=Origin(xyz=(0.0, 0.0, 0.420)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=300.0,
            velocity=0.35,
            lower=0.0,
            upper=0.120,
        ),
    )
    model.articulation(
        "stanchion_to_clamp",
        ArticulationType.FIXED,
        parent=inner_tube,
        child=saddle_clamp,
        origin=Origin(xyz=(0.0, 0.0, 0.190)),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
