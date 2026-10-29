# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, box_fan_with_control_knob, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: box_fan_with_control_knob

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
BODY_WIDTH = 0.44
BODY_DEPTH = 0.34
BODY_HEIGHT = 0.84
WALL_THICKNESS = 0.016
def _add_caster(
    model: ArticulatedObject,
    housing,
    *,
    name: str,
    origin_xyz: tuple[float, float, float],
    dark_material,
    metal_material,
) -> None:
    caster = model.part(name)
    caster.visual(
        Cylinder(radius=0.008, length=0.030),
        origin=Origin(xyz=(0.0, 0.0, -0.015)),
        material=metal_material,
        name="caster_stem",
    )
    caster.visual(
        Cylinder(radius=0.015, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, -0.035)),
        material=metal_material,
        name="caster_swivel",
    )
    caster.visual(
        Box((0.034, 0.018, 0.010)),
        origin=Origin(xyz=(0.0, 0.0, -0.044)),
        material=metal_material,
        name="caster_bridge",
    )
    caster.visual(
        Box((0.006, 0.018, 0.030)),
        origin=Origin(xyz=(-0.012, 0.0, -0.059)),
        material=metal_material,
        name="caster_left_fork",
    )
    caster.visual(
        Box((0.006, 0.018, 0.030)),
        origin=Origin(xyz=(0.012, 0.0, -0.059)),
        material=metal_material,
        name="caster_right_fork",
    )
    caster.visual(
        Cylinder(radius=0.022, length=0.022),
        origin=Origin(xyz=(0.0, 0.0, -0.069), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_material,
        name="caster_wheel",
    )
    caster.inertial = Inertial.from_geometry(
        Box((0.034, 0.022, 0.095)),
        mass=0.18,
        origin=Origin(xyz=(0.0, 0.0, -0.047)),
    )
    model.articulation(
        f"housing_to_{name}",
        ArticulationType.FIXED,
        parent=housing,
        child=caster,
        origin=Origin(xyz=origin_xyz),
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="portable_evaporative_cooler")

    body_white = model.material("body_white", rgba=(0.89, 0.91, 0.90, 1.0))
    trim_dark = model.material("trim_dark", rgba=(0.19, 0.21, 0.23, 1.0))
    grille_dark = model.material("grille_dark", rgba=(0.15, 0.16, 0.17, 1.0))
    wheel_rubber = model.material("wheel_rubber", rgba=(0.08, 0.08, 0.09, 1.0))
    caster_metal = model.material("caster_metal", rgba=(0.54, 0.56, 0.58, 1.0))
    panel_grey = model.material("panel_grey", rgba=(0.75, 0.77, 0.78, 1.0))
    accent_blue = model.material("accent_blue", rgba=(0.31, 0.58, 0.72, 1.0))

    housing = model.part("housing")
    housing.visual(
        Box((0.28, 0.14, 0.050)),
        origin=Origin(xyz=(0.0, -0.030, BODY_HEIGHT + 0.025)),
        material=panel_grey,
        name="control_console",
    )
    housing.visual(
        Box((BODY_WIDTH - 0.010, BODY_DEPTH - 0.010, 0.024)),
        origin=Origin(xyz=(0.0, 0.0, 0.012)),
        material=body_white,
        name="base_pan",
    )
    housing.visual(
        Box((WALL_THICKNESS, BODY_DEPTH, BODY_HEIGHT - 0.010)),
        origin=Origin(xyz=(-(BODY_WIDTH / 2.0) + (WALL_THICKNESS / 2.0), 0.0, (BODY_HEIGHT - 0.010) / 2.0)),
        material=body_white,
        name="left_wall",
    )
    housing.visual(
        Box((WALL_THICKNESS, BODY_DEPTH, BODY_HEIGHT - 0.010)),
        origin=Origin(xyz=((BODY_WIDTH / 2.0) - (WALL_THICKNESS / 2.0), 0.0, (BODY_HEIGHT - 0.010) / 2.0)),
        material=body_white,
        name="right_wall",
    )
    housing.visual(
        Box((BODY_WIDTH - 2.0 * WALL_THICKNESS + 0.004, BODY_DEPTH - 0.040, WALL_THICKNESS)),
        origin=Origin(xyz=(0.0, 0.010, BODY_HEIGHT - 0.008)),
        material=body_white,
        name="top_cap",
    )
    housing.visual(
        Box((0.076, WALL_THICKNESS, 0.720)),
        origin=Origin(xyz=(-0.182, (BODY_DEPTH / 2.0) - (WALL_THICKNESS / 2.0), 0.366)),
        material=body_white,
        name="front_left_stile",
    )
    housing.visual(
        Box((0.076, WALL_THICKNESS, 0.720)),
        origin=Origin(xyz=(0.182, (BODY_DEPTH / 2.0) - (WALL_THICKNESS / 2.0), 0.366)),
        material=body_white,
        name="front_right_stile",
    )
    housing.visual(
        Box((0.292, WALL_THICKNESS, 0.402)),
        origin=Origin(xyz=(0.0, (BODY_DEPTH / 2.0) - (WALL_THICKNESS / 2.0), 0.201)),
        material=body_white,
        name="front_lower_panel",
    )
    housing.visual(
        Box((0.292, WALL_THICKNESS, 0.138)),
        origin=Origin(xyz=(0.0, (BODY_DEPTH / 2.0) - (WALL_THICKNESS / 2.0), 0.771)),
        material=body_white,
        name="front_upper_panel",
    )
    housing.visual(
        Box((BODY_WIDTH - 2.0 * WALL_THICKNESS + 0.004, WALL_THICKNESS, 0.140)),
        origin=Origin(xyz=(0.0, -(BODY_DEPTH / 2.0) + (WALL_THICKNESS / 2.0), 0.070)),
        material=body_white,
        name="rear_lower_panel",
    )
    housing.visual(
        Box((BODY_WIDTH - 2.0 * WALL_THICKNESS + 0.004, WALL_THICKNESS, 0.360)),
        origin=Origin(xyz=(0.0, -(BODY_DEPTH / 2.0) + (WALL_THICKNESS / 2.0), 0.660)),
        material=body_white,
        name="rear_upper_panel",
    )
    housing.visual(
        Box((0.094, WALL_THICKNESS, 0.344)),
        origin=Origin(xyz=(-0.157, -(BODY_DEPTH / 2.0) + (WALL_THICKNESS / 2.0), 0.312)),
        material=body_white,
        name="rear_left_jamb",
    )
    housing.visual(
        Box((0.094, WALL_THICKNESS, 0.344)),
        origin=Origin(xyz=(0.157, -(BODY_DEPTH / 2.0) + (WALL_THICKNESS / 2.0), 0.312)),
        material=body_white,
        name="rear_right_jamb",
    )
    housing.visual(
        Cylinder(radius=0.042, length=0.060),
        origin=Origin(xyz=(0.0, 0.065, 0.560), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=trim_dark,
        name="fan_motor_pod",
    )
    housing.visual(
        Box((0.050, 0.060, 0.090)),
        origin=Origin(xyz=(0.0, 0.125, 0.395)),
        material=trim_dark,
        name="fan_motor_column",
    )
    housing.visual(
        Box((0.028, 0.020, 0.160)),
        origin=Origin(xyz=(0.0, 0.085, 0.510)),
        material=trim_dark,
        name="fan_motor_neck",
    )
    housing.visual(
        Box((0.110, 0.012, 0.018)),
        origin=Origin(xyz=(0.0, 0.035, 0.830)),
        material=accent_blue,
        name="panel_badge",
    )
    housing.inertial = Inertial.from_geometry(
        Box((BODY_WIDTH, BODY_DEPTH, BODY_HEIGHT + 0.060)),
        mass=18.0,
        origin=Origin(xyz=(0.0, 0.0, 0.450)),
    )

    front_grille = model.part("front_grille")
    grille_ring = mesh_from_geometry(
        TorusGeometry(radius=0.115, tube=0.006).rotate_x(math.pi / 2.0),
        "cooler_front_grille_ring",
    )
    front_grille.visual(
        Box((0.284, 0.008, 0.018)),
        origin=Origin(xyz=(0.0, 0.004, 0.141)),
        material=grille_dark,
        name="grille_top_frame",
    )
    front_grille.visual(
        Box((0.284, 0.008, 0.018)),
        origin=Origin(xyz=(0.0, 0.004, -0.141)),
        material=grille_dark,
        name="grille_bottom_frame",
    )
    front_grille.visual(
        Box((0.018, 0.008, 0.300)),
        origin=Origin(xyz=(-0.133, 0.004, 0.0)),
        material=grille_dark,
        name="grille_left_frame",
    )
    front_grille.visual(
        Box((0.018, 0.008, 0.300)),
        origin=Origin(xyz=(0.133, 0.004, 0.0)),
        material=grille_dark,
        name="grille_right_frame",
    )
    front_grille.visual(
        grille_ring,
        origin=Origin(xyz=(0.0, 0.004, 0.0)),
        material=grille_dark,
        name="grille_ring",
    )
    front_grille.visual(
        Box((0.034, 0.008, 0.018)),
        origin=Origin(xyz=(0.0, 0.004, 0.123)),
        material=grille_dark,
        name="grille_top_brace",
    )
    front_grille.visual(
        Box((0.034, 0.008, 0.018)),
        origin=Origin(xyz=(0.0, 0.004, -0.123)),
        material=grille_dark,
        name="grille_bottom_brace",
    )
    front_grille.visual(
        Box((0.018, 0.008, 0.034)),
        origin=Origin(xyz=(-0.123, 0.004, 0.0)),
        material=grille_dark,
        name="grille_left_brace",
    )
    front_grille.visual(
        Box((0.018, 0.008, 0.034)),
        origin=Origin(xyz=(0.123, 0.004, 0.0)),
        material=grille_dark,
        name="grille_right_brace",
    )
    front_grille.visual(
        Cylinder(radius=0.005, length=0.226),
        origin=Origin(xyz=(0.0, 0.004, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=grille_dark,
        name="grille_horizontal_bar",
    )
    front_grille.visual(
        Cylinder(radius=0.005, length=0.226),
        origin=Origin(xyz=(0.0, 0.004, 0.0)),
        material=grille_dark,
        name="grille_vertical_bar",
    )
    front_grille.visual(
        Cylinder(radius=0.018, length=0.012),
        origin=Origin(xyz=(0.0, 0.004, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=grille_dark,
        name="grille_center_hub",
    )
    front_grille.inertial = Inertial.from_geometry(
        Box((0.284, 0.012, 0.300)),
        mass=0.55,
        origin=Origin(xyz=(0.0, 0.004, 0.0)),
    )
    model.articulation(
        "housing_to_front_grille",
        ArticulationType.FIXED,
        parent=housing,
        child=front_grille,
        origin=Origin(xyz=(0.0, 0.170, 0.560)),
    )

    rear_fill_door = model.part("rear_fill_door")
    rear_fill_door.visual(
        Box((0.214, 0.008, 0.332)),
        origin=Origin(xyz=(0.107, 0.0, 0.0)),
        material=panel_grey,
        name="door_panel",
    )
    rear_fill_door.visual(
        Box((0.014, 0.012, 0.120)),
        origin=Origin(xyz=(0.190, -0.008, 0.0)),
        material=trim_dark,
        name="door_pull",
    )
    rear_fill_door.inertial = Inertial.from_geometry(
        Box((0.214, 0.014, 0.332)),
        mass=0.65,
        origin=Origin(xyz=(0.107, -0.002, 0.0)),
    )
    model.articulation(
        "housing_to_rear_fill_door",
        ArticulationType.REVOLUTE,
        parent=housing,
        child=rear_fill_door,
        origin=Origin(xyz=(-0.110, -0.166, 0.312)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=4.0,
            velocity=1.8,
            lower=0.0,
            upper=math.radians(105.0),
        ),
    )

    fan_rotor = model.part("fan_rotor")
    fan_rotor.visual(
        Cylinder(radius=0.010, length=0.055),
        origin=Origin(xyz=(0.0, 0.0275, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=trim_dark,
        name="fan_shaft",
    )
    fan_rotor.visual(
        Cylinder(radius=0.030, length=0.020),
        origin=Origin(xyz=(0.0, 0.060, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=trim_dark,
        name="fan_hub",
    )
    for index, angle in enumerate((0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0)):
        fan_rotor.visual(
            Box((0.098, 0.008, 0.032)),
            origin=Origin(
                xyz=(0.050 * math.cos(angle), 0.060, 0.050 * math.sin(angle)),
                rpy=(0.22, -angle, 0.0),
            ),
            material=trim_dark,
            name=f"fan_blade_{index}",
        )
    fan_rotor.inertial = Inertial.from_geometry(
        Cylinder(radius=0.125, length=0.070),
        mass=0.45,
        origin=Origin(xyz=(0.0, 0.060, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
    )
    model.articulation(
        "housing_to_fan_rotor",
        ArticulationType.CONTINUOUS,
        parent=housing,
        child=fan_rotor,
        origin=Origin(xyz=(0.0, 0.095, 0.560)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=6.0,
            velocity=18.0,
        ),
    )

    flow_control_knob = model.part("flow_control_knob")
    flow_control_knob.visual(
        Cylinder(radius=0.018, length=0.022),
        origin=Origin(xyz=(0.0, 0.0, 0.011)),
        material=trim_dark,
        name="knob_body",
    )
    flow_control_knob.visual(
        Box((0.006, 0.016, 0.004)),
        origin=Origin(xyz=(0.013, 0.0, 0.022)),
        material=accent_blue,
        name="knob_indicator",
    )
    flow_control_knob.inertial = Inertial.from_geometry(
        Cylinder(radius=0.018, length=0.024),
        mass=0.05,
        origin=Origin(xyz=(0.0, 0.0, 0.012)),
    )
    model.articulation(
        "housing_to_flow_control_knob",
        ArticulationType.CONTINUOUS,
        parent=housing,
        child=flow_control_knob,
        origin=Origin(xyz=(0.086, -0.040, BODY_HEIGHT + 0.050)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=0.4,
            velocity=6.0,
        ),
    )

    _add_caster(
        model,
        housing,
        name="front_left_caster",
        origin_xyz=(-0.155, 0.110, 0.0),
        dark_material=wheel_rubber,
        metal_material=caster_metal,
    )
    _add_caster(
        model,
        housing,
        name="front_right_caster",
        origin_xyz=(0.155, 0.110, 0.0),
        dark_material=wheel_rubber,
        metal_material=caster_metal,
    )
    _add_caster(
        model,
        housing,
        name="rear_left_caster",
        origin_xyz=(-0.155, -0.110, 0.0),
        dark_material=wheel_rubber,
        metal_material=caster_metal,
    )
    _add_caster(
        model,
        housing,
        name="rear_right_caster",
        origin_xyz=(0.155, -0.110, 0.0),
        dark_material=wheel_rubber,
        metal_material=caster_metal,
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
