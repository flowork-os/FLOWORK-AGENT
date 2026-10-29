# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bicycle_crankset_and_pedal_assembly, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bicycle_crankset_and_pedal_assembly

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

class MotionProperties:
    def __init__(self, damping=None, friction=None):
        self.damping = damping
        self.friction = friction

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
def _annular_disc_y(
    inner_radius: float,
    outer_radius: float,
    thickness: float,
    *,
    segments: int = 72,
    center_y: float = 0.0,
    tooth_count: int | None = None,
    tooth_height: float = 0.0,
) -> MeshGeometry:
    """Annular cylinder in the XZ plane, extruded along Y."""
    geom = MeshGeometry()
    half = thickness / 2.0
    outer_front: list[int] = []
    outer_back: list[int] = []
    inner_front: list[int] = []
    inner_back: list[int] = []

    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        tooth = 0.0
        if tooth_count and tooth_height > 0.0:
            # A small alternating crest makes the ring read as a chainring
            # without pretending that a chain is present.
            phase = (i * tooth_count) % segments
            tooth = tooth_height if phase < segments / (tooth_count * 2.0) else 0.0
        ro = outer_radius + tooth
        x_o, z_o = ro * math.cos(theta), ro * math.sin(theta)
        x_i, z_i = inner_radius * math.cos(theta), inner_radius * math.sin(theta)
        outer_front.append(geom.add_vertex(x_o, center_y + half, z_o))
        outer_back.append(geom.add_vertex(x_o, center_y - half, z_o))
        inner_front.append(geom.add_vertex(x_i, center_y + half, z_i))
        inner_back.append(geom.add_vertex(x_i, center_y - half, z_i))

    for i in range(segments):
        j = (i + 1) % segments
        # Front annulus face.
        geom.add_face(outer_front[i], outer_front[j], inner_front[j])
        geom.add_face(outer_front[i], inner_front[j], inner_front[i])
        # Back annulus face.
        geom.add_face(outer_back[j], outer_back[i], inner_back[i])
        geom.add_face(outer_back[j], inner_back[i], inner_back[j])
        # Outer cylindrical wall.
        geom.add_face(outer_front[j], outer_front[i], outer_back[i])
        geom.add_face(outer_front[j], outer_back[i], outer_back[j])
        # Inner bore wall.
        geom.add_face(inner_front[i], inner_front[j], inner_back[j])
        geom.add_face(inner_front[i], inner_back[j], inner_back[i])

    return geom
def _bar_between_xz(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    width: float,
    thickness_y: float,
    center_y: float,
) -> MeshGeometry:
    """Rectangular machined strut between two XZ points, extruded along Y."""
    x0, z0 = start
    x1, z1 = end
    dx, dz = x1 - x0, z1 - z0
    length = math.hypot(dx, dz)
    if length <= 0.0:
        raise ValueError("bar endpoints must differ")
    nx, nz = -dz / length, dx / length
    half_w = width / 2.0
    half_t = thickness_y / 2.0

    section = [
        (x0 + nx * half_w, z0 + nz * half_w),
        (x1 + nx * half_w, z1 + nz * half_w),
        (x1 - nx * half_w, z1 - nz * half_w),
        (x0 - nx * half_w, z0 - nz * half_w),
    ]

    geom = MeshGeometry()
    front = [geom.add_vertex(x, center_y + half_t, z) for x, z in section]
    back = [geom.add_vertex(x, center_y - half_t, z) for x, z in section]
    geom.add_face(front[0], front[1], front[2])
    geom.add_face(front[0], front[2], front[3])
    geom.add_face(back[2], back[1], back[0])
    geom.add_face(back[3], back[2], back[0])
    for i in range(4):
        j = (i + 1) % 4
        geom.add_face(front[i], front[j], back[j])
        geom.add_face(front[i], back[j], back[i])
    return geom
def _cylinder_between(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    radius: float,
    *,
    segments: int = 24,
) -> MeshGeometry:
    """Capped cylinder mesh between two arbitrary points."""
    sx, sy, sz = start
    ex, ey, ez = end
    ax, ay, az = ex - sx, ey - sy, ez - sz
    length = math.sqrt(ax * ax + ay * ay + az * az)
    if length <= 0.0:
        raise ValueError("cylinder endpoints must differ")
    wx, wy, wz = ax / length, ay / length, az / length

    # Choose a stable perpendicular basis around the tube axis.
    if abs(wz) < 0.9:
        ux, uy, uz = -wy, wx, 0.0
    else:
        ux, uy, uz = 0.0, -wz, wy
    u_len = math.sqrt(ux * ux + uy * uy + uz * uz)
    ux, uy, uz = ux / u_len, uy / u_len, uz / u_len
    vx = wy * uz - wz * uy
    vy = wz * ux - wx * uz
    vz = wx * uy - wy * ux

    geom = MeshGeometry()
    ring0: list[int] = []
    ring1: list[int] = []
    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        cx = math.cos(theta) * ux + math.sin(theta) * vx
        cy = math.cos(theta) * uy + math.sin(theta) * vy
        cz = math.cos(theta) * uz + math.sin(theta) * vz
        ring0.append(geom.add_vertex(sx + radius * cx, sy + radius * cy, sz + radius * cz))
        ring1.append(geom.add_vertex(ex + radius * cx, ey + radius * cy, ez + radius * cz))
    c0 = geom.add_vertex(sx, sy, sz)
    c1 = geom.add_vertex(ex, ey, ez)
    for i in range(segments):
        j = (i + 1) % segments
        geom.add_face(ring0[i], ring0[j], ring1[j])
        geom.add_face(ring0[i], ring1[j], ring1[i])
        geom.add_face(c0, ring0[i], ring0[j])
        geom.add_face(c1, ring1[j], ring1[i])
    return geom
def _make_pedal(model: ArticulatedObject, name: str, side: float, material: Material) -> object:
    """Flat pedal body with a real-looking bearing sleeve and open cage."""
    pedal = model.part(name)
    body_y = side * 0.046
    rail_y = 0.076
    rail_x = 0.105

    # Bearing sleeve centered on the pedal spindle axis. The spindle itself is
    # fixed to the crankset part and intentionally passes through this sleeve.
    pedal.visual(
        Cylinder(radius=0.0105, length=0.082),
        origin=Origin(xyz=(0.0, body_y, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=material,
        name="bearing_sleeve",
    )

    for z in (-0.020, 0.020):
        pedal.visual(
            Box((0.012, rail_y, 0.006)),
            origin=Origin(xyz=(-rail_x / 2.0, body_y, z)),
            material=material,
            name=f"side_rail_{'top' if z > 0 else 'bottom'}_0",
        )
        pedal.visual(
            Box((0.012, rail_y, 0.006)),
            origin=Origin(xyz=(rail_x / 2.0, body_y, z)),
            material=material,
            name=f"side_rail_{'top' if z > 0 else 'bottom'}_1",
        )
        pedal.visual(
            Box((rail_x, 0.012, 0.006)),
            origin=Origin(xyz=(0.0, body_y + side * rail_y / 2.0, z)),
            material=material,
            name=f"outer_rail_{'top' if z > 0 else 'bottom'}",
        )
        pedal.visual(
            Box((rail_x, 0.012, 0.006)),
            origin=Origin(xyz=(0.0, body_y - side * rail_y / 2.0, z)),
            material=material,
            name=f"inner_rail_{'top' if z > 0 else 'bottom'}",
        )
        # A shallow bridge kisses the sleeve, tying the cage to the bearing
        # without intersecting the visible spindle.
        pedal.visual(
            Box((0.096, 0.016, 0.008)),
            origin=Origin(xyz=(0.0, body_y, z * 0.70)),
            material=material,
            name=f"center_bridge_{'top' if z > 0 else 'bottom'}",
        )

    # Four corner posts keep the upper and lower cages visibly connected.
    for x in (-rail_x / 2.0, rail_x / 2.0):
        for y in (body_y - side * rail_y / 2.0, body_y + side * rail_y / 2.0):
            pedal.visual(
                Box((0.010, 0.010, 0.042)),
                origin=Origin(xyz=(x, y, 0.0)),
                material=material,
                name=f"corner_post_{len(pedal.visuals)}",
            )

    # Small traction pins on both faces, proud enough to read but still mounted.
    for z in (-0.025, 0.025):
        for x in (-0.035, 0.0, 0.035):
            for y in (body_y - side * 0.033, body_y + side * 0.033):
                pedal.visual(
                    Box((0.007, 0.007, 0.006)),
                    origin=Origin(xyz=(x, y, z)),
                    material=material,
                    name=f"grip_pin_{len(pedal.visuals)}",
                )
    return pedal
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bicycle_crankset_pedals")

    polished = model.material("brushed_aluminum", rgba=(0.78, 0.76, 0.70, 1.0))
    dark_metal = model.material("anodized_graphite", rgba=(0.08, 0.085, 0.09, 1.0))
    black = model.material("black_composite", rgba=(0.015, 0.015, 0.017, 1.0))
    bearing = model.material("dark_bearing_rubber", rgba=(0.01, 0.01, 0.012, 1.0))

    bottom_bracket = model.part("bottom_bracket")
    bottom_bracket.visual(
        mesh_from_geometry(
            _annular_disc_y(0.0185, 0.034, 0.078, segments=80),
            "bottom_bracket_shell",
        ),
        material=polished,
        name="shell",
    )
    for side in (-1.0, 1.0):
        bottom_bracket.visual(
            mesh_from_geometry(
                _annular_disc_y(0.0145, 0.030, 0.008, segments=72, center_y=side * 0.043),
                f"bearing_cup_{side:+.0f}",
            ),
            material=bearing,
            name=f"bearing_cup_{0 if side < 0 else 1}",
        )

    # Short welded frame-tube stubs make the subassembly feel mounted and
    # grounded, while leaving the drivetrain side unobstructed.
    bottom_bracket.visual(
        mesh_from_geometry(_cylinder_between((-0.004, 0.0, 0.023), (-0.030, 0.0, 0.165), 0.018), "seat_tube_stub"),
        material=dark_metal,
        name="seat_tube_stub",
    )
    bottom_bracket.visual(
        mesh_from_geometry(_cylinder_between((0.026, 0.0, 0.015), (0.145, 0.0, 0.095), 0.021), "down_tube_stub"),
        material=dark_metal,
        name="down_tube_stub",
    )
    for side in (-1.0, 1.0):
        bottom_bracket.visual(
            mesh_from_geometry(
                _cylinder_between((-0.022, side * 0.031, -0.012), (-0.124, side * 0.055, -0.038), 0.010),
                f"chainstay_lug_{side:+.0f}",
            ),
            material=dark_metal,
            name=f"chainstay_lug_{0 if side < 0 else 1}",
        )

    crankset = model.part("crankset")
    crankset.visual(
        Cylinder(radius=0.012, length=0.170),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=polished,
        name="spindle",
    )
    for y, side_name in ((-0.050, "drive"), (0.050, "outer")):
        crankset.visual(
            Cylinder(radius=0.026, length=0.016),
            origin=Origin(xyz=(0.0, y, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=polished,
            name=f"{side_name}_hub_cap",
        )

    # Drive-side chainring and five-arm spider.
    crankset.visual(
        mesh_from_geometry(
            _annular_disc_y(0.074, 0.106, 0.0045, segments=144, center_y=-0.065, tooth_count=48, tooth_height=0.004),
            "toothed_chainring",
        ),
        material=dark_metal,
        name="chainring",
    )
    for i in range(5):
        angle = 2.0 * math.pi * i / 5.0 + math.radians(18.0)
        start = (0.031 * math.cos(angle), 0.031 * math.sin(angle))
        end = (0.081 * math.cos(angle), 0.081 * math.sin(angle))
        crankset.visual(
            mesh_from_geometry(
                _bar_between_xz(start, end, width=0.018, thickness_y=0.007, center_y=-0.060),
                f"spider_arm_{i}",
            ),
            material=polished,
            name=f"spider_arm_{i}",
        )
        crankset.visual(
            Cylinder(radius=0.006, length=0.008),
            origin=Origin(xyz=(end[0], -0.066, end[1]), rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=polished,
            name=f"chainring_bolt_{i}",
        )

    # Opposed crank arms: drive-side arm down, non-drive arm up at zero pose.
    crankset.visual(
        mesh_from_geometry(
            _bar_between_xz((0.0, -0.018), (0.0, -0.167), width=0.024, thickness_y=0.014, center_y=-0.055),
            "drive_crank_arm",
        ),
        material=polished,
        name="drive_arm",
    )
    crankset.visual(
        mesh_from_geometry(
            _bar_between_xz((0.0, 0.018), (0.0, 0.167), width=0.024, thickness_y=0.014, center_y=0.055),
            "outer_crank_arm",
        ),
        material=polished,
        name="outer_arm",
    )
    for y, z, name in ((-0.055, -0.170, "drive_pedal_eye"), (0.055, 0.170, "outer_pedal_eye")):
        crankset.visual(
            Cylinder(radius=0.018, length=0.018),
            origin=Origin(xyz=(0.0, y, z), rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=polished,
            name=name,
        )
    for side, y, z, name in ((-1.0, -0.106, -0.170, "pedal_axle_0"), (1.0, 0.106, 0.170, "pedal_axle_1")):
        crankset.visual(
            Cylinder(radius=0.006, length=0.088),
            origin=Origin(xyz=(0.0, y, z), rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=polished,
            name=name,
        )

    pedal_0 = _make_pedal(model, "pedal_0", -1.0, black)
    pedal_1 = _make_pedal(model, "pedal_1", 1.0, black)

    model.articulation(
        "crank_spin",
        ArticulationType.CONTINUOUS,
        parent=bottom_bracket,
        child=crankset,
        origin=Origin(),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=25.0, velocity=20.0),
        motion_properties=MotionProperties(damping=0.03, friction=0.01),
    )
    model.articulation(
        "pedal_0_spin",
        ArticulationType.CONTINUOUS,
        parent=crankset,
        child=pedal_0,
        origin=Origin(xyz=(0.0, -0.072, -0.170)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=2.0, velocity=12.0),
        motion_properties=MotionProperties(damping=0.01, friction=0.003),
    )
    model.articulation(
        "pedal_1_spin",
        ArticulationType.CONTINUOUS,
        parent=crankset,
        child=pedal_1,
        origin=Origin(xyz=(0.0, 0.072, 0.170)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=2.0, velocity=12.0),
        motion_properties=MotionProperties(damping=0.01, friction=0.003),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
