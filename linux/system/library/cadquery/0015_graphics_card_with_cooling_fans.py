# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, graphics_card_with_cooling_fans, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: graphics_card_with_cooling_fans

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

# ===== primitives (1 syms) =====
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
CARD_LENGTH = 0.286
CARD_HEIGHT = 0.108
PCB_THICKNESS = 0.002
FIN_BASE_THICKNESS = 0.004
HEATSINK_TOP_Z = 0.022
SHROUD_BOTTOM_Z = HEATSINK_TOP_Z
SHROUD_TOP_Z = 0.038
BACKPLATE_THICKNESS = 0.0016
FAN_CENTERS = (-0.092, 0.0, 0.092)
FAN_RIM_OUTER = 0.039
FAN_RIM_INNER = 0.0355
SHROUD_BEZEL_OUTER = 0.045
SHROUD_BEZEL_INNER = 0.0408
FAN_Z_JOINT = 0.0
def _save_mesh(geometry, filename: str):
    return mesh_from_geometry(geometry, ASSETS.mesh_path(filename))
def _ring_band_mesh(
    *,
    outer_radius: float,
    inner_radius: float,
    height: float,
    radial_segments: int = 56,
):
    outer = CylinderGeometry(radius=outer_radius, height=height, radial_segments=radial_segments)
    inner = CylinderGeometry(
        radius=inner_radius,
        height=height + 0.002,
        radial_segments=radial_segments,
    )
    return boolean_difference(outer, inner)
def _add_fin_stack(part, material) -> None:
    part.visual(
        Box((0.266, 0.102, FIN_BASE_THICKNESS)),
        origin=Origin(xyz=(0.004, 0.000, 0.004)),
        material=material,
        name="fin_base",
    )
    part.visual(
        Box((0.256, 0.096, 0.002)),
        origin=Origin(xyz=(0.008, 0.000, HEATSINK_TOP_Z - 0.001)),
        material=material,
        name="top_spreader",
    )
    fin_count = 15
    for index in range(fin_count):
        y = -0.044 + index * (0.088 / (fin_count - 1))
        part.visual(
            Box((0.250, 0.0018, HEATSINK_TOP_Z - 0.006)),
            origin=Origin(xyz=(0.008, y, 0.014)),
            material=material,
            name=f"fin_{index}",
        )
    part.visual(
        Box((0.020, 0.100, 0.016)),
        origin=Origin(xyz=(-0.118, 0.000, 0.014)),
        material=material,
        name="left_cold_plate",
    )
    part.visual(
        Box((0.020, 0.100, 0.016)),
        origin=Origin(xyz=(0.126, 0.000, 0.014)),
        material=material,
        name="right_cold_plate",
    )
def _add_core_details(part, pcb_material, metal_material, gold_material) -> None:
    part.visual(
        Box((CARD_LENGTH, CARD_HEIGHT, PCB_THICKNESS)),
        origin=Origin(xyz=(0.004, 0.000, PCB_THICKNESS * 0.5)),
        material=pcb_material,
        name="pcb",
    )
    part.visual(
        Box((0.092, 0.008, 0.0012)),
        origin=Origin(xyz=(-0.018, -0.050, 0.0014)),
        material=gold_material,
        name="pcie_fingers",
    )
    part.visual(
        Box((0.018, 0.012, 0.010)),
        origin=Origin(xyz=(0.084, 0.060, 0.007)),
        material=metal_material,
        name="power_socket_left",
    )
    part.visual(
        Box((0.018, 0.012, 0.010)),
        origin=Origin(xyz=(0.108, 0.060, 0.007)),
        material=metal_material,
        name="power_socket_right",
    )
    part.visual(
        Box((0.118, 0.006, 0.008)),
        origin=Origin(xyz=(0.070, 0.052, 0.006)),
        material=metal_material,
        name="top_edge_bar",
    )
    part.visual(
        Box((0.074, 0.010, 0.008)),
        origin=Origin(xyz=(0.102, -0.044, 0.006)),
        material=metal_material,
        name="rear_stiffener",
    )
def _add_shroud_structure(part, body_material, accent_material, bezel_mesh) -> None:
    frame_center_z = 0.030
    frame_height = SHROUD_TOP_Z - SHROUD_BOTTOM_Z

    part.visual(
        Box((0.282, 0.012, frame_height)),
        origin=Origin(xyz=(0.000, 0.051, frame_center_z)),
        material=body_material,
        name="top_rail",
    )
    part.visual(
        Box((0.282, 0.012, frame_height)),
        origin=Origin(xyz=(0.000, -0.051, frame_center_z)),
        material=body_material,
        name="bottom_rail",
    )
    part.visual(
        Box((0.008, 0.114, frame_height)),
        origin=Origin(xyz=(-0.141, 0.000, frame_center_z)),
        material=body_material,
        name="left_endcap",
    )
    part.visual(
        Box((0.014, 0.114, frame_height)),
        origin=Origin(xyz=(0.144, 0.000, frame_center_z)),
        material=body_material,
        name="right_endcap",
    )
    part.visual(
        Box((0.008, 0.066, frame_height)),
        origin=Origin(xyz=(-0.046, 0.000, frame_center_z)),
        material=body_material,
        name="bridge_left",
    )
    part.visual(
        Box((0.008, 0.066, frame_height)),
        origin=Origin(xyz=(0.046, 0.000, frame_center_z)),
        material=body_material,
        name="bridge_right",
    )

    for label, x_pos in zip(("left", "center", "right"), FAN_CENTERS):
        part.visual(
            bezel_mesh,
            origin=Origin(xyz=(x_pos, 0.000, 0.030)),
            material=body_material,
            name=f"bezel_{label}",
        )
        part.visual(
            Cylinder(radius=0.010, length=0.006),
            origin=Origin(xyz=(x_pos, 0.000, 0.025)),
            material=accent_material,
            name=f"bearing_{label}",
        )
        part.visual(
            Box((0.006, 0.034, 0.004)),
            origin=Origin(xyz=(x_pos, 0.027, 0.025)),
            material=accent_material,
            name=f"bearing_top_strut_{label}",
        )
        part.visual(
            Box((0.006, 0.034, 0.004)),
            origin=Origin(xyz=(x_pos, -0.027, 0.025)),
            material=accent_material,
            name=f"bearing_bottom_strut_{label}",
        )

    part.visual(
        Box((0.074, 0.008, 0.006)),
        origin=Origin(xyz=(-0.088, 0.028, 0.038)),
        material=accent_material,
        name="accent_upper_left",
    )
    part.visual(
        Box((0.074, 0.008, 0.006)),
        origin=Origin(xyz=(0.088, 0.028, 0.038)),
        material=accent_material,
        name="accent_upper_right",
    )
    part.visual(
        Box((0.074, 0.008, 0.006)),
        origin=Origin(xyz=(-0.088, -0.028, 0.038)),
        material=accent_material,
        name="accent_lower_left",
    )
    part.visual(
        Box((0.074, 0.008, 0.006)),
        origin=Origin(xyz=(0.088, -0.028, 0.038)),
        material=accent_material,
        name="accent_lower_right",
    )
    part.visual(
        Box((0.004, 0.010, 0.004)),
        origin=Origin(xyz=(FAN_CENTERS[1] + 0.0445, 0.000, 0.034)),
        material=accent_material,
        name="center_ref_x",
    )
    part.visual(
        Box((0.010, 0.004, 0.004)),
        origin=Origin(xyz=(FAN_CENTERS[1], 0.0445, 0.034)),
        material=accent_material,
        name="center_ref_y",
    )
def _add_backplate_details(part, plate_material, accent_material) -> None:
    part.visual(
        Box((0.294, 0.110, BACKPLATE_THICKNESS)),
        origin=Origin(xyz=(0.003, 0.000, -BACKPLATE_THICKNESS * 0.5)),
        material=plate_material,
        name="plate",
    )
    for index, y in enumerate((-0.030, 0.000, 0.030)):
        part.visual(
            Box((0.240, 0.006, 0.003)),
            origin=Origin(xyz=(0.018, y, -0.0022)),
            material=accent_material,
            name=f"rib_{index}",
        )
    part.visual(
        Box((0.050, 0.024, 0.0032)),
        origin=Origin(xyz=(-0.106, 0.000, -0.0023)),
        material=accent_material,
        name="vrm_plate",
    )
    part.visual(
        Box((0.070, 0.014, 0.0025)),
        origin=Origin(xyz=(0.120, 0.038, -0.00205)),
        material=accent_material,
        name="logo_bar",
    )
def _add_bracket_details(part, bracket_material, dark_material) -> None:
    plate_x = -0.149
    part.visual(
        Box((0.002, 0.112, 0.004)),
        origin=Origin(xyz=(plate_x, 0.000, 0.018)),
        material=bracket_material,
        name="front_edge",
    )
    part.visual(
        Box((0.002, 0.112, 0.004)),
        origin=Origin(xyz=(plate_x, 0.000, 0.002)),
        material=bracket_material,
        name="rear_edge",
    )
    part.visual(
        Box((0.002, 0.010, 0.020)),
        origin=Origin(xyz=(plate_x, 0.051, 0.010)),
        material=bracket_material,
        name="top_cross",
    )
    part.visual(
        Box((0.002, 0.010, 0.020)),
        origin=Origin(xyz=(plate_x, 0.000, 0.010)),
        material=bracket_material,
        name="middle_cross",
    )
    part.visual(
        Box((0.002, 0.010, 0.020)),
        origin=Origin(xyz=(plate_x, -0.051, 0.010)),
        material=bracket_material,
        name="bottom_cross",
    )
    part.visual(
        Box((0.010, 0.020, 0.002)),
        origin=Origin(xyz=(-0.144, -0.040, 0.003)),
        material=bracket_material,
        name="mount_tongue",
    )
    part.visual(
        Box((0.002, 0.018, 0.012)),
        origin=Origin(xyz=(plate_x, 0.062, 0.020)),
        material=bracket_material,
        name="screw_ear",
    )
    part.visual(
        Box((0.002, 0.038, 0.014)),
        origin=Origin(xyz=(plate_x, 0.026, 0.010)),
        material=dark_material,
        name="upper_port_liner",
    )
    part.visual(
        Box((0.002, 0.038, 0.014)),
        origin=Origin(xyz=(plate_x, -0.026, 0.010)),
        material=dark_material,
        name="lower_port_liner",
    )
def _build_fan_part(model, name: str, fan_material, hub_material, rim_mesh, *, add_tab: bool):
    fan = model.part(name)
    fan.visual(
        rim_mesh,
        origin=Origin(xyz=(0.000, 0.000, 0.034)),
        material=fan_material,
        name="rim",
    )
    fan.visual(
        Cylinder(radius=0.013, length=0.008),
        origin=Origin(xyz=(0.000, 0.000, 0.033)),
        material=hub_material,
        name="hub",
    )
    fan.visual(
        Cylinder(radius=0.006, length=0.004),
        origin=Origin(xyz=(0.000, 0.000, 0.030)),
        material=hub_material,
        name="axle",
    )
    fan.visual(
        Cylinder(radius=0.0095, length=0.0025),
        origin=Origin(xyz=(0.000, 0.000, 0.03725)),
        material=fan_material,
        name="cap",
    )

    blade_count = 9
    for index in range(blade_count):
        angle = index * math.tau / blade_count
        fan.visual(
            Box((0.028, 0.008, 0.0026)),
            origin=Origin(
                xyz=(0.024 * math.cos(angle), 0.024 * math.sin(angle), 0.033),
                rpy=(0.22, 0.00, angle + 0.55),
            ),
            material=fan_material,
            name=f"blade_{index}",
        )

    if add_tab:
        fan.visual(
            Box((0.004, 0.006, 0.002)),
            origin=Origin(xyz=(0.0365, 0.000, 0.034)),
            material=hub_material,
            name="timing_tab",
        )

    fan.inertial = Inertial.from_geometry(
        Cylinder(radius=0.040, length=0.012),
        mass=0.08,
        origin=Origin(xyz=(0.000, 0.000, 0.033)),
    )
    return fan
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="graphics_card", assets=ASSETS)

    shroud_black = model.material("shroud_black", rgba=(0.12, 0.13, 0.14, 1.0))
    shroud_trim = model.material("shroud_trim", rgba=(0.20, 0.22, 0.24, 1.0))
    pcb_black = model.material("pcb_black", rgba=(0.07, 0.09, 0.07, 1.0))
    fin_aluminum = model.material("fin_aluminum", rgba=(0.55, 0.58, 0.62, 1.0))
    bracket_metal = model.material("bracket_metal", rgba=(0.66, 0.68, 0.71, 1.0))
    backplate_metal = model.material("backplate_metal", rgba=(0.30, 0.33, 0.36, 1.0))
    fan_black = model.material("fan_black", rgba=(0.10, 0.10, 0.11, 1.0))
    gold = model.material("gold", rgba=(0.82, 0.69, 0.25, 1.0))

    bezel_mesh = _save_mesh(
        _ring_band_mesh(
            outer_radius=SHROUD_BEZEL_OUTER,
            inner_radius=SHROUD_BEZEL_INNER,
            height=SHROUD_TOP_Z - SHROUD_BOTTOM_Z,
        ),
        "gpu_shroud_bezel.obj",
    )
    rim_mesh = _save_mesh(
        _ring_band_mesh(
            outer_radius=FAN_RIM_OUTER,
            inner_radius=FAN_RIM_INNER,
            height=0.006,
        ),
        "gpu_fan_rim.obj",
    )

    core = model.part("core")
    _add_core_details(core, pcb_black, shroud_trim, gold)
    _add_fin_stack(core, fin_aluminum)
    core.inertial = Inertial.from_geometry(
        Box((0.300, 0.118, 0.024)),
        mass=1.45,
        origin=Origin(xyz=(0.005, 0.000, 0.012)),
    )

    shroud = model.part("shroud")
    _add_shroud_structure(shroud, shroud_black, shroud_trim, bezel_mesh)
    shroud.inertial = Inertial.from_geometry(
        Box((0.292, 0.116, SHROUD_TOP_Z - SHROUD_BOTTOM_Z)),
        mass=0.42,
        origin=Origin(xyz=(0.002, 0.000, 0.030)),
    )

    backplate = model.part("backplate")
    _add_backplate_details(backplate, backplate_metal, shroud_trim)
    backplate.inertial = Inertial.from_geometry(
        Box((0.296, 0.112, 0.004)),
        mass=0.28,
        origin=Origin(xyz=(0.003, 0.000, -0.002)),
    )

    bracket = model.part("bracket")
    _add_bracket_details(bracket, bracket_metal, shroud_trim)
    bracket.inertial = Inertial.from_geometry(
        Box((0.012, 0.118, 0.026)),
        mass=0.08,
        origin=Origin(xyz=(-0.145, 0.000, 0.013)),
    )

    fan_left = _build_fan_part(
        model,
        "fan_left",
        fan_black,
        shroud_trim,
        rim_mesh,
        add_tab=False,
    )
    fan_center = _build_fan_part(
        model,
        "fan_center",
        fan_black,
        shroud_trim,
        rim_mesh,
        add_tab=True,
    )
    fan_right = _build_fan_part(
        model,
        "fan_right",
        fan_black,
        shroud_trim,
        rim_mesh,
        add_tab=False,
    )

    model.articulation(
        "core_to_shroud",
        ArticulationType.FIXED,
        parent=core,
        child=shroud,
        origin=Origin(),
    )
    model.articulation(
        "core_to_backplate",
        ArticulationType.FIXED,
        parent=core,
        child=backplate,
        origin=Origin(),
    )
    model.articulation(
        "core_to_bracket",
        ArticulationType.FIXED,
        parent=core,
        child=bracket,
        origin=Origin(),
    )

    for label, part, x_pos in (
        ("left", fan_left, FAN_CENTERS[0]),
        ("center", fan_center, FAN_CENTERS[1]),
        ("right", fan_right, FAN_CENTERS[2]),
    ):
        model.articulation(
            f"shroud_to_fan_{label}",
            ArticulationType.CONTINUOUS,
            parent=shroud,
            child=part,
            origin=Origin(xyz=(x_pos, 0.000, FAN_Z_JOINT)),
            axis=(0.0, 0.0, 1.0),
            motion_limits=MotionLimits(effort=0.3, velocity=50.0),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
