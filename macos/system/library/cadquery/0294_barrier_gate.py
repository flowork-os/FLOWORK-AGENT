# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, barrier_gate, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: barrier_gate

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

class Mimic:
    def __init__(self, joint, multiplier=1.0, offset=0.0):
        self.joint = str(joint)
        self.multiplier = float(multiplier)
        self.offset = float(offset)

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
LEAF_WIDTH = 1.87
HINGE_X = 1.90
HINGE_Y = -0.045
LOWER_HINGE_Z = 0.55
UPPER_HINGE_Z = 1.35
PANEL_BOTTOM_Z = 0.24
PANEL_TOP_Z = 1.58
def _bar_between(part, name, p0, p1, thickness, material):
    """Add a rectangular wrought-iron bar between two local XZ points."""
    x0, z0 = p0
    x1, z1 = p1
    dx = x1 - x0
    dz = z1 - z0
    length = math.hypot(dx, dz)
    theta_y = -math.atan2(dz, dx)
    part.visual(
        Box((length, thickness, thickness)),
        origin=Origin(
            xyz=((x0 + x1) * 0.5, 0.0, (z0 + z1) * 0.5),
            rpy=(0.0, theta_y, 0.0),
        ),
        material=material,
        name=name,
    )
def _add_panel_geometry(part, side: int, material, ring_mesh) -> None:
    """Build one rectangular ornamental swing-gate leaf around its hinge axis."""
    bottom = PANEL_BOTTOM_Z - LOWER_HINGE_Z
    top = PANEL_TOP_Z - LOWER_HINGE_Z
    height = top - bottom
    center_z = (top + bottom) * 0.5

    stile_thick = 0.060
    rail_thick = 0.060
    y_thick = 0.055
    hinge_stile_x = side * 0.080
    free_stile_x = side * (LEAF_WIDTH - 0.040)
    rail_start = 0.080
    rail_end = LEAF_WIDTH - 0.040
    rail_center = side * ((rail_start + rail_end) * 0.5)
    rail_length = rail_end - rail_start

    part.visual(
        Box((stile_thick, y_thick, height)),
        origin=Origin(xyz=(hinge_stile_x, 0.0, center_z)),
        material=material,
        name="hinge_stile",
    )
    part.visual(
        Box((stile_thick, y_thick, height)),
        origin=Origin(xyz=(free_stile_x, 0.0, center_z)),
        material=material,
        name="free_stile",
    )
    for name, z in (("bottom_rail", bottom + rail_thick * 0.5), ("top_rail", top - rail_thick * 0.5)):
        part.visual(
            Box((rail_length, y_thick, rail_thick)),
            origin=Origin(xyz=(rail_center, 0.0, z)),
            material=material,
            name=name,
        )
    part.visual(
        Box((rail_length * 0.86, 0.045, 0.045)),
        origin=Origin(xyz=(side * (LEAF_WIDTH * 0.50), 0.0, (bottom + top) * 0.5)),
        material=material,
        name="middle_rail",
    )

    picket_bottom = bottom + 0.060
    picket_top = top - 0.060
    picket_height = picket_top - picket_bottom
    for idx, x_abs in enumerate((0.38, 0.67, 0.96, 1.25, 1.54)):
        x = side * x_abs
        part.visual(
            Cylinder(radius=0.014, length=picket_height),
            origin=Origin(xyz=(x, 0.0, (picket_bottom + picket_top) * 0.5)),
            material=material,
            name=f"picket_{idx}",
        )
        part.visual(
            Sphere(radius=0.032),
            origin=Origin(xyz=(x, 0.0, picket_top + 0.025)),
            material=material,
            name=f"finial_{idx}",
        )

    low = bottom + 0.180
    high = top - 0.180
    _bar_between(
        part,
        "rising_scroll_bar",
        (side * 0.210, low),
        (side * (LEAF_WIDTH - 0.210), high),
        0.028,
        material,
    )
    _bar_between(
        part,
        "falling_scroll_bar",
        (side * 0.210, high),
        (side * (LEAF_WIDTH - 0.210), low),
        0.028,
        material,
    )

    part.visual(
        ring_mesh,
        origin=Origin(
            xyz=(side * (LEAF_WIDTH * 0.50), -0.002, (bottom + top) * 0.5),
            rpy=(math.pi / 2.0, 0.0, 0.0),
        ),
        material=material,
        name="central_ring",
    )

    # Lower leaf of the pintle hinge, bolted to the panel and revolving with it.
    part.visual(
        Cylinder(radius=0.034, length=0.150),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=material,
        name="lower_barrel",
    )
    part.visual(
        Box((0.150, 0.030, 0.055)),
        origin=Origin(xyz=(side * 0.075, -0.0425, 0.0)),
        material=material,
        name="lower_strap",
    )
def _add_upper_leaf(part, side: int, material) -> None:
    """Build the visible upper hinge leaf that mimics the same leaf swing."""
    part.visual(
        Cylinder(radius=0.034, length=0.150),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=material,
        name="upper_barrel",
    )
    # The strap kisses the front face of the panel stile so it reads bolted-on
    # without creating an unintended inter-part volume overlap.
    part.visual(
        Box((0.150, 0.030, 0.055)),
        origin=Origin(xyz=(side * 0.075, -0.0425, 0.0)),
        material=material,
        name="upper_strap",
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="double_leaf_decorative_driveway_gate")

    stone = model.material("cast_stone", rgba=(0.58, 0.54, 0.47, 1.0))
    cap_stone = model.material("stone_cap", rgba=(0.66, 0.62, 0.55, 1.0))
    iron = model.material("black_wrought_iron", rgba=(0.015, 0.014, 0.012, 1.0))
    root_metal = model.material("dark_pintle_steel", rgba=(0.025, 0.023, 0.021, 1.0))

    ring_mesh = mesh_from_geometry(
        TorusGeometry(radius=0.210, tube=0.011, radial_segments=18, tubular_segments=48),
        "ornamental_gate_ring",
    )

    pillars = model.part("pillars")
    pillars.visual(
        Box((4.62, 0.46, 0.120)),
        origin=Origin(xyz=(0.0, 0.0, 0.060)),
        material=stone,
        name="ground_sill",
    )
    for side_name, x in (("left", -2.12), ("right", 2.12)):
        pillars.visual(
            Box((0.340, 0.420, 1.900)),
            origin=Origin(xyz=(x, 0.0, 0.950)),
            material=stone,
            name=f"{side_name}_pillar",
        )
        pillars.visual(
            Box((0.440, 0.500, 0.110)),
            origin=Origin(xyz=(x, 0.0, 1.955)),
            material=cap_stone,
            name=f"{side_name}_cap",
        )

    for side_name, hinge_x, bracket_x in (
        ("left", -HINGE_X, -1.935),
        ("right", HINGE_X, 1.935),
    ):
        for level_name, z in (("lower", LOWER_HINGE_Z), ("upper", UPPER_HINGE_Z)):
            pillars.visual(
                Cylinder(radius=0.020, length=0.190),
                origin=Origin(xyz=(hinge_x, HINGE_Y, z)),
                material=root_metal,
                name=f"{side_name}_{level_name}_pin",
            )
            pillars.visual(
                Box((0.060, 0.075, 0.040)),
                origin=Origin(xyz=(bracket_x, HINGE_Y, z + 0.105)),
                material=root_metal,
                name=f"{side_name}_{level_name}_bracket",
            )

    left_panel = model.part("left_panel")
    _add_panel_geometry(left_panel, +1, iron, ring_mesh)

    right_panel = model.part("right_panel")
    _add_panel_geometry(right_panel, -1, iron, ring_mesh)

    left_upper_leaf = model.part("left_upper_leaf")
    _add_upper_leaf(left_upper_leaf, +1, iron)

    right_upper_leaf = model.part("right_upper_leaf")
    _add_upper_leaf(right_upper_leaf, -1, iron)

    swing_limits = MotionLimits(effort=120.0, velocity=0.7, lower=0.0, upper=math.radians(92.0))
    model.articulation(
        "left_lower_pintle",
        ArticulationType.REVOLUTE,
        parent=pillars,
        child=left_panel,
        origin=Origin(xyz=(-HINGE_X, HINGE_Y, LOWER_HINGE_Z)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=swing_limits,
    )
    model.articulation(
        "left_upper_pintle",
        ArticulationType.REVOLUTE,
        parent=pillars,
        child=left_upper_leaf,
        origin=Origin(xyz=(-HINGE_X, HINGE_Y, UPPER_HINGE_Z)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=swing_limits,
        mimic=Mimic("left_lower_pintle"),
    )
    model.articulation(
        "right_lower_pintle",
        ArticulationType.REVOLUTE,
        parent=pillars,
        child=right_panel,
        origin=Origin(xyz=(HINGE_X, HINGE_Y, LOWER_HINGE_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=swing_limits,
    )
    model.articulation(
        "right_upper_pintle",
        ArticulationType.REVOLUTE,
        parent=pillars,
        child=right_upper_leaf,
        origin=Origin(xyz=(HINGE_X, HINGE_Y, UPPER_HINGE_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=swing_limits,
        mimic=Mimic("right_lower_pintle"),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
