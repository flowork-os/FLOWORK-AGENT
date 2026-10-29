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
BODY_RADIUS = 0.09
BODY_HEIGHT = 0.29
BODY_INNER_RADIUS = 0.078
def _save_mesh(geometry: MeshGeometry, filename: str):
    return mesh_from_geometry(geometry, ASSETS.mesh_path(filename))
def _build_body_shell_mesh() -> MeshGeometry:
    outer = CylinderGeometry(radius=BODY_RADIUS, height=BODY_HEIGHT, radial_segments=72)
    inner = CylinderGeometry(
        radius=BODY_INNER_RADIUS,
        height=BODY_HEIGHT - 0.040,
        radial_segments=72,
    )
    shell = boolean_difference(outer, inner)

    front_opening = BoxGeometry((0.058, 0.118, 0.186)).translate(0.061, 0.0, 0.0)
    shell = boolean_difference(shell, front_opening)

    outlet_recess = CylinderGeometry(radius=0.070, height=0.020, radial_segments=64).translate(
        0.0,
        0.0,
        (BODY_HEIGHT * 0.5) - 0.010,
    )
    shell = boolean_difference(shell, outlet_recess)
    return shell.translate(0.0, 0.0, BODY_HEIGHT * 0.5)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="desktop_air_purifier", assets=ASSETS)

    shell_mat = model.material("shell_gray", rgba=(0.20, 0.22, 0.24, 1.0))
    door_mat = model.material("door_gray", rgba=(0.24, 0.25, 0.27, 1.0))
    dark_mat = model.material("dark_trim", rgba=(0.09, 0.10, 0.11, 1.0))
    filter_mat = model.material("filter_media", rgba=(0.33, 0.36, 0.38, 1.0))
    steel_mat = model.material("hardware", rgba=(0.54, 0.56, 0.58, 1.0))
    satin_mat = model.material("satin_trim", rgba=(0.31, 0.33, 0.35, 1.0))

    opening_w = 0.102
    opening_h = 0.158
    lip_t = 0.008
    lip_x = 0.078
    lip_side_w = 0.010
    lip_rail_h = 0.012

    bay_side_w = 0.010
    bay_rail_h = 0.012
    bay_frame_x = 0.065
    bay_back_x = 0.053

    door_w = 0.114
    door_h = 0.172
    door_t = 0.0045
    hinge_x = BODY_RADIUS + 0.0025
    hinge_y = door_w * 0.5
    hinge_z = 0.145
    hinge_pin_r = 0.0016

    body = model.part("body")
    body.visual(
        _save_mesh(_build_body_shell_mesh(), "purifier_shell.obj"),
        material=shell_mat,
        name="shell",
    )
    body.visual(
        Cylinder(radius=0.095, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.006)),
        material=satin_mat,
        name="base_ring",
    )

    seat_side_offset = (door_w * 0.5) - 0.005
    seat_rail_offset = (door_h * 0.5) - 0.005
    seat_x = hinge_x - door_t - 0.001
    body.visual(
        Box((0.002, 0.010, door_h - 0.004)),
        origin=Origin(xyz=(seat_x, -seat_side_offset, hinge_z)),
        material=door_mat,
        name="seat_left",
    )
    body.visual(
        Box((0.002, 0.010, door_h - 0.004)),
        origin=Origin(xyz=(seat_x, seat_side_offset, hinge_z)),
        material=door_mat,
        name="seat_right",
    )
    body.visual(
        Box((0.002, door_w - 0.020, 0.010)),
        origin=Origin(xyz=(seat_x, 0.0, hinge_z + seat_rail_offset)),
        material=door_mat,
        name="seat_top",
    )
    body.visual(
        Box((0.002, door_w - 0.020, 0.010)),
        origin=Origin(xyz=(seat_x, 0.0, hinge_z - seat_rail_offset)),
        material=door_mat,
        name="seat_bottom",
    )

    side_offset = (opening_w * 0.5) + (lip_side_w * 0.5)
    rail_offset = (opening_h * 0.5) + (lip_rail_h * 0.5)
    body.visual(
        Box((lip_t, lip_side_w, opening_h + (lip_rail_h * 2.0))),
        origin=Origin(xyz=(lip_x, -side_offset, hinge_z)),
        material=shell_mat,
        name="lip_left",
    )
    body.visual(
        Box((lip_t, lip_side_w, opening_h + (lip_rail_h * 2.0))),
        origin=Origin(xyz=(lip_x, side_offset, hinge_z)),
        material=satin_mat,
        name="lip_right",
    )
    body.visual(
        Box((lip_t, opening_w, lip_rail_h)),
        origin=Origin(xyz=(lip_x, 0.0, hinge_z + rail_offset)),
        material=satin_mat,
        name="lip_top",
    )
    body.visual(
        Box((lip_t, opening_w, lip_rail_h)),
        origin=Origin(xyz=(lip_x, 0.0, hinge_z - rail_offset)),
        material=satin_mat,
        name="lip_bottom",
    )

    bay_side_offset = (opening_w * 0.5) - (bay_side_w * 0.5)
    bay_rail_offset = (opening_h * 0.5) - (bay_rail_h * 0.5)
    body.visual(
        Box((0.020, bay_side_w, opening_h - 0.004)),
        origin=Origin(xyz=(bay_frame_x, -bay_side_offset, hinge_z)),
        material=shell_mat,
        name="bay_left_frame",
    )
    body.visual(
        Box((0.020, bay_side_w, opening_h - 0.004)),
        origin=Origin(xyz=(bay_frame_x, bay_side_offset, hinge_z)),
        material=shell_mat,
        name="bay_right_frame",
    )
    body.visual(
        Box((0.020, opening_w - 0.020, bay_rail_h)),
        origin=Origin(xyz=(bay_frame_x, 0.0, hinge_z + bay_rail_offset)),
        material=shell_mat,
        name="bay_top_frame",
    )
    body.visual(
        Box((0.020, opening_w - 0.020, bay_rail_h)),
        origin=Origin(xyz=(bay_frame_x, 0.0, hinge_z - bay_rail_offset)),
        material=shell_mat,
        name="bay_bottom_frame",
    )
    body.visual(
        Box((0.006, opening_w - 0.014, opening_h - 0.010)),
        origin=Origin(xyz=(bay_back_x, 0.0, hinge_z)),
        material=dark_mat,
        name="bay_backplate",
    )
    body.visual(
        Box((0.012, 0.086, 0.140)),
        origin=Origin(xyz=(0.057, 0.0, hinge_z)),
        material=filter_mat,
        name="bay_filter",
    )
    for idx, y in enumerate((-0.028, -0.014, 0.0, 0.014, 0.028), start=1):
        body.visual(
            Box((0.014, 0.004, 0.140)),
            origin=Origin(xyz=(0.059, y, hinge_z)),
            material=dark_mat,
            name=f"filter_rib_{idx}",
        )

    for prefix, z in (("upper", hinge_z + 0.064), ("lower", hinge_z - 0.064)):
        body.visual(
            Box((0.011, 0.010, 0.030)),
            origin=Origin(xyz=(0.0855, hinge_y - 0.001, z)),
            material=shell_mat,
            name=f"{prefix}_hinge_mount",
        )
        body.visual(
            Cylinder(radius=hinge_pin_r, length=0.022),
            origin=Origin(xyz=(hinge_x, hinge_y, z)),
            material=steel_mat,
            name=f"{prefix}_hinge_pin",
        )
    body.visual(
        Cylinder(radius=hinge_pin_r, length=0.128),
        origin=Origin(xyz=(hinge_x, hinge_y, hinge_z)),
        material=steel_mat,
        name="hinge_spindle",
    )

    body.visual(
        Cylinder(radius=0.070, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, BODY_HEIGHT - 0.021)),
        material=dark_mat,
        name="outlet_floor",
    )
    for idx, y in enumerate((-0.030, -0.015, 0.0, 0.015, 0.030), start=1):
        body.visual(
            Box((0.112, 0.008, 0.004)),
            origin=Origin(xyz=(0.0, y, BODY_HEIGHT - 0.013)),
            material=shell_mat,
            name="grille_slat_center" if idx == 3 else f"grille_slat_{idx}",
        )
    body.visual(
        Box((0.050, 0.018, 0.003)),
        origin=Origin(xyz=(0.022, 0.0, BODY_HEIGHT - 0.023)),
        material=dark_mat,
        name="control_strip",
    )
    body.visual(
        Box((0.026, 0.005, 0.0015)),
        origin=Origin(xyz=(0.022, 0.0, BODY_HEIGHT - 0.021)),
        material=steel_mat,
        name="control_highlight",
    )
    body.inertial = Inertial.from_geometry(
        Cylinder(radius=BODY_RADIUS, length=BODY_HEIGHT),
        mass=2.9,
        origin=Origin(xyz=(0.0, 0.0, BODY_HEIGHT * 0.5)),
    )

    door = model.part("filter_door")
    door.visual(
        Box((door_t, door_w, door_h)),
        origin=Origin(xyz=(-door_t * 0.5, -door_w * 0.5, 0.0)),
        material=door_mat,
        name="door_panel",
    )
    door.visual(
        Box((0.0018, 0.088, 0.142)),
        origin=Origin(xyz=(-0.0016, -door_w * 0.5, 0.0)),
        material=satin_mat,
        name="door_inner_stiffener",
    )
    door.visual(
        Box((0.003, 0.010, door_h - 0.004)),
        origin=Origin(xyz=(-0.0015, -door_w + 0.005, 0.0)),
        material=door_mat,
        name="free_edge_return",
    )
    for name, z in (("upper_knuckle", 0.064), ("lower_knuckle", -0.064)):
        door.visual(
            Cylinder(radius=0.0038, length=0.022),
            origin=Origin(xyz=(0.0, 0.0, z)),
            material=shell_mat,
            name=name,
        )
    pocket_y = -door_w + 0.008
    door.visual(
        Box((0.0032, 0.015, 0.060)),
        origin=Origin(xyz=(-0.0016, pocket_y, 0.0)),
        material=dark_mat,
        name="pull_pocket",
    )
    door.visual(
        Cylinder(radius=0.0044, length=0.040),
        origin=Origin(xyz=(-0.0003, pocket_y, 0.0)),
        material=steel_mat,
        name="pull_core",
    )
    for idx, z in enumerate((-0.014, -0.007, 0.0, 0.007, 0.014), start=1):
        door.visual(
            Cylinder(radius=0.0049, length=0.003),
            origin=Origin(xyz=(-0.0003, pocket_y, z)),
            material=steel_mat,
            name=f"knurl_band_{idx}",
        )
    door.inertial = Inertial.from_geometry(
        Box((0.018, door_w, door_h)),
        mass=0.45,
        origin=Origin(xyz=(-0.009, -door_w * 0.5, 0.0)),
    )

    model.articulation(
        "filter_door_hinge",
        ArticulationType.REVOLUTE,
        parent=body,
        child=door,
        origin=Origin(xyz=(hinge_x, hinge_y, hinge_z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=6.0, velocity=2.2, lower=0.0, upper=1.22),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
