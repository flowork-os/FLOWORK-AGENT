# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, arcade_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: arcade_machine

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

# ===== model =====
import math
def _add_quad(geom: MeshGeometry, a: int, b: int, c: int, d: int) -> None:
    geom.add_face(a, b, c)
    geom.add_face(a, c, d)
def _prism_from_profile(
    profile_yz: list[tuple[float, float]],
    *,
    x_min: float,
    x_max: float,
) -> MeshGeometry:
    geom = MeshGeometry()
    left_ids: list[int] = []
    right_ids: list[int] = []

    for y, z in profile_yz:
        left_ids.append(geom.add_vertex(x_min, y, z))
        right_ids.append(geom.add_vertex(x_max, y, z))

    count = len(profile_yz)
    for index in range(count):
        next_index = (index + 1) % count
        _add_quad(
            geom,
            left_ids[index],
            left_ids[next_index],
            right_ids[next_index],
            right_ids[index],
        )

    for index in range(1, count - 1):
        geom.add_face(left_ids[0], left_ids[index + 1], left_ids[index])
        geom.add_face(right_ids[0], right_ids[index], right_ids[index + 1])

    return geom
def _segment_pose(
    start_yz: tuple[float, float],
    end_yz: tuple[float, float],
) -> tuple[float, float, float, float]:
    start_y, start_z = start_yz
    end_y, end_z = end_yz
    delta_y = end_y - start_y
    delta_z = end_z - start_z
    return (
        (start_y + end_y) * 0.5,
        (start_z + end_z) * 0.5,
        math.hypot(delta_y, delta_z),
        math.atan2(delta_z, delta_y),
    )
def _offset_along_local_z(y: float, z: float, angle: float, offset: float) -> tuple[float, float]:
    return (y - math.sin(angle) * offset, z + math.cos(angle) * offset)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bartop_arcade_machine")

    body_black = model.material("body_black", rgba=(0.10, 0.10, 0.11, 1.0))
    trim_black = model.material("trim_black", rgba=(0.04, 0.04, 0.05, 1.0))
    control_black = model.material("control_black", rgba=(0.09, 0.09, 0.10, 1.0))
    screen_glass = model.material("screen_glass", rgba=(0.09, 0.16, 0.20, 0.92))
    marquee_glow = model.material("marquee_glow", rgba=(0.76, 0.18, 0.84, 0.82))
    knob_black = model.material("knob_black", rgba=(0.12, 0.12, 0.13, 1.0))
    knob_indicator = model.material("knob_indicator", rgba=(0.82, 0.82, 0.83, 1.0))
    coin_metal = model.material("coin_metal", rgba=(0.62, 0.64, 0.67, 1.0))
    coin_dark = model.material("coin_dark", rgba=(0.16, 0.17, 0.18, 1.0))
    button_red = model.material("button_red", rgba=(0.72, 0.14, 0.16, 1.0))
    button_yellow = model.material("button_yellow", rgba=(0.84, 0.68, 0.12, 1.0))
    button_blue = model.material("button_blue", rgba=(0.12, 0.40, 0.74, 1.0))

    cabinet_width = 0.42
    side_thickness = 0.012
    inner_width = cabinet_width - 2.0 * side_thickness

    profile_yz = [
        (-0.160, 0.000),
        (0.120, 0.000),
        (0.120, 0.340),
        (0.040, 0.450),
        (-0.020, 0.450),
        (-0.050, 0.320),
        (-0.072, 0.142),
        (-0.154, 0.095),
    ]

    marquee_segment = ((-0.020, 0.450), (-0.050, 0.320))
    bezel_segment = ((-0.050, 0.320), (-0.072, 0.142))
    deck_segment = ((-0.154, 0.095), (-0.072, 0.142))
    back_segment = ((0.120, 0.340), (0.040, 0.450))

    marquee_y, marquee_z, marquee_len, marquee_angle = _segment_pose(*marquee_segment)
    bezel_y, bezel_z, bezel_len, bezel_angle = _segment_pose(*bezel_segment)
    deck_y, deck_z, deck_len, deck_angle = _segment_pose(*deck_segment)
    back_y, back_z, back_len, back_angle = _segment_pose(*back_segment)

    left_side_mesh = mesh_from_geometry(
        _prism_from_profile(
            profile_yz,
            x_min=-cabinet_width * 0.5,
            x_max=-cabinet_width * 0.5 + side_thickness,
        ),
        "arcade_left_side_panel",
    )
    right_side_mesh = mesh_from_geometry(
        _prism_from_profile(
            profile_yz,
            x_min=cabinet_width * 0.5 - side_thickness,
            x_max=cabinet_width * 0.5,
        ),
        "arcade_right_side_panel",
    )

    cabinet = model.part("cabinet")
    cabinet.visual(left_side_mesh, material=body_black, name="left_side")
    cabinet.visual(right_side_mesh, material=body_black, name="right_side")
    cabinet.visual(
        Box((inner_width, 0.280, side_thickness)),
        origin=Origin(xyz=(0.000, -0.020, side_thickness * 0.5)),
        material=body_black,
        name="bottom_panel",
    )
    cabinet.visual(
        Box((inner_width, side_thickness, 0.340)),
        origin=Origin(xyz=(0.000, 0.114, 0.170)),
        material=body_black,
        name="rear_panel_lower",
    )
    cabinet.visual(
        Box((inner_width, back_len, side_thickness)),
        origin=Origin(xyz=(0.000, back_y, back_z), rpy=(back_angle, 0.0, 0.0)),
        material=body_black,
        name="rear_panel_upper",
    )
    cabinet.visual(
        Box((inner_width, 0.060, side_thickness)),
        origin=Origin(xyz=(0.000, 0.010, 0.444)),
        material=body_black,
        name="top_panel",
    )
    cabinet.visual(
        Box((inner_width, marquee_len, side_thickness)),
        origin=Origin(xyz=(0.000, marquee_y, marquee_z), rpy=(marquee_angle, 0.0, 0.0)),
        material=body_black,
        name="marquee_panel_backer",
    )
    cabinet.visual(
        Box((inner_width * 0.96, marquee_len - 0.010, 0.004)),
        origin=Origin(
            xyz=(0.000, marquee_y - math.sin(marquee_angle) * 0.004, marquee_z + math.cos(marquee_angle) * 0.004),
            rpy=(marquee_angle, 0.0, 0.0),
        ),
        material=marquee_glow,
        name="marquee_face",
    )
    cabinet.visual(
        Box((inner_width, deck_len, side_thickness)),
        origin=Origin(xyz=(0.000, deck_y, deck_z), rpy=(deck_angle, 0.0, 0.0)),
        material=control_black,
        name="control_deck",
    )
    cabinet.visual(
        Box((inner_width, 0.095, side_thickness)),
        origin=Origin(xyz=(0.000, -0.157, 0.048), rpy=(1.06, 0.0, 0.0)),
        material=body_black,
        name="front_kick_panel",
    )

    bezel_width = 0.255
    bezel_height = 0.138
    bezel_bar = 0.016
    cabinet.visual(
        Box((inner_width, bezel_bar, 0.010)),
        origin=Origin(
            xyz=(0.000, bezel_y + 0.5 * bezel_height * math.cos(bezel_angle), bezel_z + 0.5 * bezel_height * math.sin(bezel_angle)),
            rpy=(bezel_angle, 0.0, 0.0),
        ),
        material=trim_black,
        name="bezel_top_bar",
    )
    cabinet.visual(
        Box((inner_width, bezel_bar, 0.010)),
        origin=Origin(
            xyz=(0.000, bezel_y - 0.5 * bezel_height * math.cos(bezel_angle), bezel_z - 0.5 * bezel_height * math.sin(bezel_angle)),
            rpy=(bezel_angle, 0.0, 0.0),
        ),
        material=trim_black,
        name="bezel_bottom_bar",
    )
    cabinet.visual(
        Box((bezel_bar, bezel_height, 0.010)),
        origin=Origin(xyz=(-0.5 * bezel_width, bezel_y, bezel_z), rpy=(bezel_angle, 0.0, 0.0)),
        material=trim_black,
        name="bezel_left_bar",
    )
    cabinet.visual(
        Box((bezel_bar, bezel_height, 0.010)),
        origin=Origin(xyz=(0.5 * bezel_width, bezel_y, bezel_z), rpy=(bezel_angle, 0.0, 0.0)),
        material=trim_black,
        name="bezel_right_bar",
    )
    cabinet.visual(
        Cylinder(radius=0.012, length=0.006),
        origin=Origin(xyz=(0.090, 0.004, 0.447)),
        material=trim_black,
        name="knob_mount",
    )
    cabinet.inertial = Inertial.from_geometry(
        Box((cabinet_width, 0.280, 0.450)),
        mass=7.5,
        origin=Origin(xyz=(0.000, -0.020, 0.225)),
    )

    screen = model.part("screen")
    screen.visual(
        Box((0.228, 0.128, 0.008)),
        origin=Origin(xyz=(0.000, 0.000, -0.009)),
        material=screen_glass,
        name="screen_panel",
    )
    screen.inertial = Inertial.from_geometry(
        Box((0.228, 0.128, 0.008)),
        mass=0.28,
        origin=Origin(xyz=(0.000, 0.000, -0.009)),
    )
    model.articulation(
        "cabinet_to_screen",
        ArticulationType.FIXED,
        parent=cabinet,
        child=screen,
        origin=Origin(xyz=(0.000, bezel_y, bezel_z), rpy=(bezel_angle, 0.0, 0.0)),
    )

    knob = model.part("control_knob")
    knob.visual(
        Cylinder(radius=0.023, length=0.004),
        origin=Origin(xyz=(0.000, 0.000, 0.002)),
        material=knob_black,
        name="knob_skirt",
    )
    knob.visual(
        Cylinder(radius=0.019, length=0.016),
        origin=Origin(xyz=(0.000, 0.000, 0.012)),
        material=knob_black,
        name="knob_body",
    )
    knob.visual(
        Cylinder(radius=0.010, length=0.004),
        origin=Origin(xyz=(0.000, 0.000, 0.022)),
        material=knob_black,
        name="knob_cap",
    )
    knob.visual(
        Box((0.003, 0.018, 0.002)),
        origin=Origin(xyz=(0.000, 0.010, 0.023)),
        material=knob_indicator,
        name="knob_pointer",
    )
    knob.inertial = Inertial.from_geometry(
        Cylinder(radius=0.023, length=0.026),
        mass=0.07,
        origin=Origin(xyz=(0.000, 0.000, 0.013)),
    )
    model.articulation(
        "cabinet_to_control_knob",
        ArticulationType.CONTINUOUS,
        parent=cabinet,
        child=knob,
        origin=Origin(xyz=(0.090, 0.004, 0.450)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.3, velocity=12.0),
    )

    button_surface_y, button_surface_z = _offset_along_local_z(deck_y, deck_z, deck_angle, side_thickness * 0.5)
    button_guide_y, button_guide_z = _offset_along_local_z(deck_y, deck_z, deck_angle, side_thickness * 0.5 + 0.002)
    button_specs = (
        ("red_button", "red", -0.060, button_red),
        ("yellow_button", "yellow", -0.018, button_yellow),
        ("blue_button", "blue", 0.024, button_blue),
    )
    for part_name, color_name, x_pos, material in button_specs:
        cabinet.visual(
            Cylinder(radius=0.016, length=0.004),
            origin=Origin(xyz=(x_pos, button_guide_y, button_guide_z), rpy=(deck_angle, 0.0, 0.0)),
            material=trim_black,
            name=f"{color_name}_button_guide",
        )

        button = model.part(part_name)
        button.visual(
            Cylinder(radius=0.013, length=0.006),
            origin=Origin(xyz=(0.0, 0.0, 0.007)),
            material=material,
            name="button_cap",
        )
        button.inertial = Inertial.from_geometry(
            Cylinder(radius=0.013, length=0.006),
            mass=0.03,
            origin=Origin(xyz=(0.0, 0.0, 0.007)),
        )
        model.articulation(
            f"cabinet_to_{part_name}",
            ArticulationType.PRISMATIC,
            parent=cabinet,
            child=button,
            origin=Origin(xyz=(x_pos, button_surface_y, button_surface_z), rpy=(deck_angle, 0.0, 0.0)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=0.4,
                velocity=0.10,
                lower=0.0,
                upper=0.003,
            ),
        )

    acceptor = model.part("coin_acceptor")
    acceptor.visual(
        Box((0.006, 0.052, 0.100)),
        origin=Origin(xyz=(0.003, 0.000, 0.050)),
        material=coin_metal,
        name="acceptor_base",
    )
    acceptor.visual(
        Box((0.008, 0.040, 0.010)),
        origin=Origin(xyz=(0.010, 0.000, 0.071)),
        material=coin_dark,
        name="coin_slot",
    )
    acceptor.visual(
        Box((0.005, 0.034, 0.020)),
        origin=Origin(xyz=(0.0085, 0.000, 0.018)),
        material=coin_dark,
        name="return_bezel",
    )
    acceptor.visual(
        Box((0.004, 0.052, 0.010)),
        origin=Origin(xyz=(0.008, 0.000, 0.095)),
        material=coin_metal,
        name="top_lip",
    )
    acceptor.inertial = Inertial.from_geometry(
        Box((0.014, 0.052, 0.100)),
        mass=0.14,
        origin=Origin(xyz=(0.007, 0.000, 0.050)),
    )
    model.articulation(
        "cabinet_to_coin_acceptor",
        ArticulationType.FIXED,
        parent=cabinet,
        child=acceptor,
        origin=Origin(xyz=(cabinet_width * 0.5, -0.114, 0.082)),
    )

    coin_flap = model.part("coin_return_flap")
    coin_flap.visual(
        Box((0.003, 0.028, 0.018)),
        origin=Origin(xyz=(0.0015, 0.000, -0.009)),
        material=coin_metal,
        name="coin_flap",
    )
    coin_flap.inertial = Inertial.from_geometry(
        Box((0.003, 0.028, 0.018)),
        mass=0.02,
        origin=Origin(xyz=(0.0015, 0.000, -0.009)),
    )
    model.articulation(
        "coin_acceptor_to_return_flap",
        ArticulationType.REVOLUTE,
        parent=acceptor,
        child=coin_flap,
        origin=Origin(xyz=(0.006, 0.000, 0.026)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.08,
            velocity=3.0,
            lower=0.0,
            upper=1.1,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
