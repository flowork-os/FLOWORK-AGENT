# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, casino_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: casino_machine

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
def _prism_from_yz_profile(
    profile: list[tuple[float, float]], width: float, *, x_center: float = 0.0
) -> MeshGeometry:
    """Build a closed prism by extruding a side-profile along cabinet width."""

    geom = MeshGeometry()
    x0 = x_center - width / 2.0
    x1 = x_center + width / 2.0
    for x in (x0, x1):
        for y, z in profile:
            geom.add_vertex(x, y, z)

    n = len(profile)
    # End caps, fan triangulated.  Face winding is not semantically important here,
    # but keeping both caps opposite makes the generated mesh well behaved.
    for i in range(1, n - 1):
        geom.add_face(0, i, i + 1)
        geom.add_face(n, n + i + 1, n + i)

    # Side walls.
    for i in range(n):
        j = (i + 1) % n
        geom.add_face(i, j, n + j)
        geom.add_face(i, n + j, n + i)
    return geom
def _angled_origin(
    center_y: float,
    center_z: float,
    roll: float,
    *,
    local_y: float = 0.0,
    local_z: float = 0.0,
    x: float = 0.0,
) -> Origin:
    """Offset a visual in the local coordinates of the slanted display face."""

    c = math.cos(roll)
    s = math.sin(roll)
    return Origin(
        xyz=(
            x,
            center_y + c * local_y - s * local_z,
            center_z + s * local_y + c * local_z,
        ),
        rpy=(roll, 0.0, 0.0),
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="slant_top_video_slot_machine")

    red = model.material("deep_red_laminate", rgba=(0.42, 0.025, 0.035, 1.0))
    black = model.material("black_powdercoat", rgba=(0.015, 0.015, 0.018, 1.0))
    charcoal = model.material("charcoal_metal", rgba=(0.08, 0.085, 0.09, 1.0))
    chrome = model.material("brushed_chrome", rgba=(0.72, 0.70, 0.65, 1.0))
    glass = model.material("dark_blue_glass", rgba=(0.015, 0.035, 0.085, 0.92))
    glow = model.material("lit_marquee", rgba=(1.0, 0.83, 0.30, 1.0))
    white = model.material("white_legends", rgba=(0.92, 0.93, 0.88, 1.0))
    gold = model.material("coin_gold", rgba=(0.95, 0.68, 0.20, 1.0))

    cabinet = model.part("cabinet")

    # Casino-floor sized slant-top cabinet: about 0.8 m wide and 1.5 m tall.
    # The side polygon creates a continuous wedge-like body with a reclined
    # display face above the projecting button deck.
    shell_profile = [
        (-0.34, 0.00),
        (0.30, 0.00),
        (0.30, 1.46),
        (0.10, 1.52),
        (-0.12, 1.38),
        (-0.37, 0.92),
        (-0.37, 0.18),
    ]
    cabinet.visual(
        mesh_from_geometry(_prism_from_yz_profile(shell_profile, 0.82), "cabinet_shell"),
        material=red,
        name="cabinet_shell",
    )

    cabinet.visual(
        Box((0.88, 0.72, 0.12)),
        origin=Origin(xyz=(0.0, -0.02, 0.06)),
        material=black,
        name="floor_plinth",
    )

    # Shallow shelf that projects from the cabinet front and is carried by real
    # triangular side gussets, not by floating buttons.
    cabinet.visual(
        Box((0.76, 0.31, 0.065)),
        origin=Origin(xyz=(0.0, -0.52, 0.785)),
        material=charcoal,
        name="button_deck",
    )
    cabinet.visual(
        Cylinder(radius=0.025, length=0.76),
        origin=Origin(xyz=(0.0, -0.675, 0.785), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=chrome,
        name="deck_front_roll",
    )
    bracket_profile = [
        (-0.374, 0.758),
        (-0.646, 0.758),
        (-0.374, 0.58),
    ]
    for x, suffix in [(-0.39, "0"), (0.39, "1")]:
        cabinet.visual(
            mesh_from_geometry(
                _prism_from_yz_profile(bracket_profile, 0.045, x_center=x),
                f"deck_gusset_{suffix}",
            ),
            material=charcoal,
            name=f"deck_gusset_{suffix}",
        )

    # Slanted video face, set into the angled body.  Thin trim pieces are
    # slightly embedded in the same plane to read as a manufactured bezel.
    face_roll = -0.498
    face_y = -0.245
    face_z = 1.15
    screen_w = 0.60
    screen_h = 0.36
    trim = 0.035
    cabinet.visual(
        Box((screen_w, 0.018, screen_h)),
        origin=_angled_origin(face_y, face_z, face_roll),
        material=glass,
        name="video_screen",
    )
    cabinet.visual(
        Box((screen_w + 2 * trim, 0.026, trim)),
        origin=_angled_origin(face_y, face_z, face_roll, local_z=screen_h / 2 + trim / 2),
        material=black,
        name="screen_top_bezel",
    )
    cabinet.visual(
        Box((screen_w + 2 * trim, 0.026, trim)),
        origin=_angled_origin(face_y, face_z, face_roll, local_z=-(screen_h / 2 + trim / 2)),
        material=black,
        name="screen_bottom_bezel",
    )
    for x, side_name in [(-(screen_w / 2 + trim / 2), "screen_side_bezel_0"), ((screen_w / 2 + trim / 2), "screen_side_bezel_1")]:
        cabinet.visual(
            Box((trim, 0.026, screen_h)),
            origin=_angled_origin(face_y, face_z, face_roll, x=x),
            material=black,
            name=side_name,
        )
    cabinet.visual(
        Box((0.50, 0.010, 0.035)),
        origin=_angled_origin(face_y, face_z, face_roll, local_z=-0.09, local_y=-0.012),
        material=glow,
        name="game_graphic",
    )
    cabinet.visual(
        Box((0.68, 0.030, 0.13)),
        origin=_angled_origin(-0.09, 1.41, face_roll, local_y=-0.006),
        material=glow,
        name="top_marquee",
    )

    # Belly door surround, bill/card service details and hinge-side support.
    cabinet.visual(
        Box((0.73, 0.020, 0.055)),
        origin=Origin(xyz=(0.0, -0.382, 0.735)),
        material=chrome,
        name="belly_header_trim",
    )
    cabinet.visual(
        Box((0.030, 0.020, 0.56)),
        origin=Origin(xyz=(-0.345, -0.374, 0.46)),
        material=chrome,
        name="hinge_jamb",
    )
    cabinet.visual(
        Box((0.030, 0.020, 0.56)),
        origin=Origin(xyz=(0.285, -0.382, 0.46)),
        material=chrome,
        name="latch_jamb",
    )
    cabinet.visual(
        Box((0.30, 0.020, 0.075)),
        origin=Origin(xyz=(0.12, -0.386, 0.845)),
        material=black,
        name="bill_acceptor",
    )
    cabinet.visual(
        Box((0.16, 0.024, 0.030)),
        origin=Origin(xyz=(0.12, -0.398, 0.848)),
        material=chrome,
        name="bill_slot",
    )
    cabinet.visual(
        Box((0.12, 0.018, 0.055)),
        origin=Origin(xyz=(-0.20, -0.387, 0.842)),
        material=black,
        name="card_reader",
    )

    # Fixed collars in the deck make the row of play buttons visibly mounted.
    button_xs = [-0.27, -0.162, -0.054, 0.054, 0.162, 0.27]
    button_y = -0.585
    collar_top_z = 0.824
    for idx, x in enumerate(button_xs):
        cabinet.visual(
            Cylinder(radius=0.044, length=0.0065),
            origin=Origin(xyz=(x, button_y, collar_top_z - 0.0065 / 2.0)),
            material=black,
            name=f"button_collar_{idx}",
        )

    # The belly door is a separate hinged part so it can swing open from one side.
    belly_door = model.part("belly_door")
    belly_door.visual(
        Box((0.62, 0.032, 0.52)),
        origin=Origin(xyz=(0.31, -0.008, 0.26)),
        material=charcoal,
        name="door_panel",
    )
    belly_door.visual(
        Box((0.54, 0.006, 0.065)),
        origin=Origin(xyz=(0.33, -0.027, 0.39)),
        material=black,
        name="door_vent",
    )
    belly_door.visual(
        Cylinder(radius=0.024, length=0.020),
        origin=Origin(xyz=(0.50, -0.030, 0.31), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=chrome,
        name="lock_cylinder",
    )
    belly_door.visual(
        Box((0.030, 0.012, 0.004)),
        origin=Origin(xyz=(0.50, -0.042, 0.31)),
        material=black,
        name="lock_slot",
    )
    for z in (0.12, 0.40):
        belly_door.visual(
            Cylinder(radius=0.010, length=0.16),
            origin=Origin(xyz=(0.004, -0.010, z)),
            material=chrome,
            name=f"hinge_barrel_{int(z * 100)}",
        )

    door_hinge = model.articulation(
        "belly_door_hinge",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=belly_door,
        origin=Origin(xyz=(-0.36, -0.40, 0.20)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(effort=35.0, velocity=1.5, lower=0.0, upper=1.35),
    )
    _ = door_hinge

    button_materials = [
        model.material("button_red", rgba=(0.86, 0.05, 0.03, 1.0)),
        model.material("button_blue", rgba=(0.05, 0.22, 0.90, 1.0)),
        model.material("button_green", rgba=(0.04, 0.62, 0.16, 1.0)),
        model.material("button_yellow", rgba=(0.94, 0.82, 0.08, 1.0)),
        model.material("button_purple", rgba=(0.42, 0.12, 0.70, 1.0)),
        model.material("button_white", rgba=(0.92, 0.92, 0.86, 1.0)),
    ]
    for idx, x in enumerate(button_xs):
        button = model.part(f"button_{idx}")
        button.visual(
            Cylinder(radius=0.034, length=0.026),
            origin=Origin(xyz=(0.0, 0.0, 0.013)),
            material=button_materials[idx],
            name="cap",
        )
        button.visual(
            Cylinder(radius=0.018, length=0.003),
            origin=Origin(xyz=(0.0, 0.0, 0.0275)),
            material=white if idx != 3 else gold,
            name="legend_lens",
        )
        model.articulation(
            f"button_{idx}_slide",
            ArticulationType.PRISMATIC,
            parent=cabinet,
            child=button,
            origin=Origin(xyz=(x, button_y, collar_top_z)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(effort=8.0, velocity=0.20, lower=0.0, upper=0.016),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
