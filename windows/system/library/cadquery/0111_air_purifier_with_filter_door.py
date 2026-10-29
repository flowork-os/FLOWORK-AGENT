# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_purifier_with_filter_door, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_purifier_with_filter_door

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
ASSETS = AssetContext.from_script(__file__)
BODY_RADIUS = 0.090
BODY_SHELL_THICKNESS = 0.0045
PLINTH_RADIUS = 0.096
PLINTH_HEIGHT = 0.018
DRUM_HEIGHT = 0.142
DRUM_TOP = PLINTH_HEIGHT + DRUM_HEIGHT
PANEL_OPENING_WIDTH = 0.090
PANEL_OPENING_HEIGHT = 0.110
PANEL_OPENING_BOTTOM = 0.030
PANEL_CENTER_Z = PANEL_OPENING_BOTTOM + (PANEL_OPENING_HEIGHT * 0.5)
HINGE_BARREL_RADIUS = 0.005
HINGE_X = -(PANEL_OPENING_WIDTH * 0.5) - HINGE_BARREL_RADIUS
HINGE_Y = 0.096
def _save_mesh(geometry, filename: str):
    ASSETS.mesh_dir.mkdir(parents=True, exist_ok=True)
    return mesh_from_geometry(geometry, ASSETS.mesh_path(filename))
def _ring_shell(*, outer_radius: float, inner_radius: float, height: float):
    outer = CylinderGeometry(radius=outer_radius, height=height, radial_segments=64)
    inner = CylinderGeometry(radius=inner_radius, height=height + 0.006, radial_segments=64)
    return boolean_difference(outer, inner)
def _build_drum_shell_mesh():
    shell = _ring_shell(
        outer_radius=BODY_RADIUS,
        inner_radius=BODY_RADIUS - BODY_SHELL_THICKNESS,
        height=DRUM_HEIGHT,
    ).translate(0.0, 0.0, PLINTH_HEIGHT + (DRUM_HEIGHT * 0.5))
    cutout = BoxGeometry(
        (
            PANEL_OPENING_WIDTH + 0.010,
            BODY_RADIUS * 1.28,
            PANEL_OPENING_HEIGHT + 0.012,
        )
    ).translate(0.0, BODY_RADIUS * 0.58, PANEL_CENTER_Z)
    return boolean_difference(shell, cutout)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="desktop_air_purifier", assets=ASSETS)

    shell_white = model.material("shell_white", rgba=(0.93, 0.94, 0.92, 1.0))
    charcoal = model.material("charcoal", rgba=(0.17, 0.18, 0.19, 1.0))
    dark_trim = model.material("dark_trim", rgba=(0.23, 0.24, 0.25, 1.0))
    filter_grey = model.material("filter_grey", rgba=(0.74, 0.78, 0.80, 1.0))
    filter_frame = model.material("filter_frame", rgba=(0.28, 0.29, 0.30, 1.0))
    soft_black = model.material("soft_black", rgba=(0.12, 0.13, 0.14, 1.0))

    housing = model.part("housing")
    housing.visual(
        Cylinder(radius=PLINTH_RADIUS, length=PLINTH_HEIGHT),
        origin=Origin(xyz=(0.0, 0.0, PLINTH_HEIGHT * 0.5)),
        material=charcoal,
        name="plinth",
    )
    housing.visual(
        _save_mesh(_build_drum_shell_mesh(), "purifier_drum_shell.obj"),
        material=shell_white,
        name="drum_shell",
    )
    housing.visual(
        Box((PANEL_OPENING_WIDTH + 0.020, 0.016, 0.014)),
        origin=Origin(xyz=(0.0, 0.082, PANEL_OPENING_BOTTOM - 0.007)),
        material=shell_white,
        name="bottom_bezel",
    )
    housing.visual(
        Box((PANEL_OPENING_WIDTH + 0.020, 0.016, 0.014)),
        origin=Origin(xyz=(0.0, 0.082, PANEL_OPENING_BOTTOM + PANEL_OPENING_HEIGHT + 0.007)),
        material=shell_white,
        name="top_bezel",
    )
    housing.visual(
        Box((0.014, 0.016, PANEL_OPENING_HEIGHT + 0.020)),
        origin=Origin(xyz=(-(PANEL_OPENING_WIDTH * 0.5) - 0.007, 0.082, PANEL_CENTER_Z)),
        material=shell_white,
        name="left_bezel",
    )
    housing.visual(
        Box((0.014, 0.016, PANEL_OPENING_HEIGHT + 0.020)),
        origin=Origin(xyz=((PANEL_OPENING_WIDTH * 0.5) + 0.007, 0.082, PANEL_CENTER_Z)),
        material=shell_white,
        name="right_bezel",
    )
    housing.visual(
        Box((0.010, 0.002, PANEL_OPENING_HEIGHT - 0.014)),
        origin=Origin(
            xyz=((PANEL_OPENING_WIDTH * 0.5) + 0.003, HINGE_Y - 0.007, PANEL_CENTER_Z)
        ),
        material=dark_trim,
        name="latch_seat",
    )
    housing.inertial = Inertial.from_geometry(
        Cylinder(radius=PLINTH_RADIUS, length=DRUM_TOP),
        mass=2.2,
        origin=Origin(xyz=(0.0, 0.0, DRUM_TOP * 0.5)),
    )

    exhaust_cap = model.part("exhaust_cap")
    exhaust_cap.visual(
        Cylinder(radius=0.089, length=0.004),
        origin=Origin(xyz=(0.0, 0.0, 0.002)),
        material=dark_trim,
        name="cap_flange",
    )
    exhaust_cap.visual(
        Cylinder(radius=0.066, length=0.018),
        origin=Origin(xyz=(0.0, 0.0, 0.013)),
        material=dark_trim,
        name="cap_shell",
    )
    exhaust_cap.visual(
        Box((0.044, 0.006, 0.004)),
        origin=Origin(xyz=(0.0, 0.0, 0.020)),
        material=soft_black,
        name="grille_bar_x",
    )
    exhaust_cap.visual(
        Box((0.006, 0.044, 0.004)),
        origin=Origin(xyz=(0.0, 0.0, 0.020)),
        material=soft_black,
        name="grille_bar_y",
    )
    exhaust_cap.visual(
        Cylinder(radius=0.010, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, 0.017)),
        material=soft_black,
        name="grille_hub",
    )
    exhaust_cap.inertial = Inertial.from_geometry(
        Cylinder(radius=0.082, length=0.030),
        mass=0.28,
        origin=Origin(xyz=(0.0, 0.0, 0.015)),
    )

    access_panel = model.part("access_panel")
    access_panel.visual(
        Box((PANEL_OPENING_WIDTH, 0.004, PANEL_OPENING_HEIGHT)),
        origin=Origin(xyz=(HINGE_BARREL_RADIUS + (PANEL_OPENING_WIDTH * 0.5), -0.003, 0.0)),
        material=shell_white,
        name="door_skin",
    )
    access_panel.visual(
        Box((0.058, 0.005, 0.098)),
        origin=Origin(xyz=(0.056, 0.001, 0.0)),
        material=filter_frame,
        name="filter_frame",
    )
    access_panel.visual(
        Box((0.050, 0.004, 0.086)),
        origin=Origin(xyz=(0.056, 0.0015, 0.0)),
        material=filter_grey,
        name="filter_media",
    )
    for index in range(4):
        access_panel.visual(
            Box((0.0045, 0.0055, 0.086)),
            origin=Origin(xyz=(0.039 + (index * 0.011), 0.001, 0.0)),
            material=filter_frame,
            name=f"filter_pleat_{index}",
        )
    access_panel.visual(
        Box((0.007, 0.007, 0.026)),
        origin=Origin(xyz=(0.088, 0.0045, 0.0)),
        material=dark_trim,
        name="pull_tab",
    )
    access_panel.visual(
        Box((0.010, 0.005, 0.040)),
        origin=Origin(xyz=(0.091, -0.0055, 0.0)),
        material=dark_trim,
        name="latch_tongue",
    )
    access_panel.inertial = Inertial.from_geometry(
        Box((0.100, 0.040, 0.120)),
        mass=0.34,
        origin=Origin(xyz=(0.052, -0.012, 0.0)),
    )

    model.articulation(
        "housing_to_exhaust_cap",
        ArticulationType.FIXED,
        parent=housing,
        child=exhaust_cap,
        origin=Origin(xyz=(0.0, 0.0, DRUM_TOP)),
    )
    model.articulation(
        "housing_to_access_panel",
        ArticulationType.REVOLUTE,
        parent=housing,
        child=access_panel,
        origin=Origin(xyz=(HINGE_X, HINGE_Y, PANEL_CENTER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=4.0, velocity=2.5, lower=0.0, upper=1.15),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
