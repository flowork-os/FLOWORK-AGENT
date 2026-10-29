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
def _arched_top_box(width: float, depth: float, base_z: float, shoulder_z: float, crown_z: float) -> MeshGeometry:
    """Closed extruded mesh for the rounded top box of the cabinet."""
    half_w = width / 2.0
    half_d = depth / 2.0

    profile: list[tuple[float, float]] = [(-half_w, base_z), (half_w, base_z), (half_w, shoulder_z)]
    for i in range(1, 16):
        theta = (i / 15.0) * math.pi
        # Half-ellipse crown from right shoulder to left shoulder.
        profile.append((half_w * math.cos(theta), shoulder_z + (crown_z - shoulder_z) * math.sin(theta)))
    profile.append((-half_w, base_z))

    geom = MeshGeometry()
    front: list[int] = []
    back: list[int] = []
    for x, z in profile:
        front.append(geom.add_vertex(x, -half_d, z))
    for x, z in profile:
        back.append(geom.add_vertex(x, half_d, z))

    n = len(profile)
    for i in range(n):
        j = (i + 1) % n
        geom.add_face(front[i], front[j], back[j])
        geom.add_face(front[i], back[j], back[i])

    # Cap the front and back with a fan around the profile center.
    center_z = (base_z + crown_z) / 2.0
    front_c = geom.add_vertex(0.0, -half_d, center_z)
    back_c = geom.add_vertex(0.0, half_d, center_z)
    for i in range(n):
        j = (i + 1) % n
        geom.add_face(front_c, front[i], front[j])
        geom.add_face(back_c, back[j], back[i])

    return geom
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="tall_reel_slot_machine")

    cabinet_red = model.material("deep_casino_red", rgba=(0.55, 0.03, 0.04, 1.0))
    black = model.material("gloss_black", rgba=(0.005, 0.005, 0.006, 1.0))
    dark = model.material("smoked_glass", rgba=(0.05, 0.09, 0.13, 0.45))
    chrome = model.material("brushed_chrome", rgba=(0.78, 0.72, 0.60, 1.0))
    warm_gold = model.material("warm_gold", rgba=(0.95, 0.66, 0.18, 1.0))
    reel_paper = model.material("aged_reel_paper", rgba=(0.96, 0.91, 0.78, 1.0))
    rubber = model.material("dark_rubber", rgba=(0.02, 0.018, 0.016, 1.0))
    service_blue = model.material("recessed_blue_door", rgba=(0.06, 0.12, 0.19, 1.0))

    cabinet = model.part("cabinet")

    # Full-height carcass panels. The front is intentionally built as rails and
    # surrounds so the reel window and service door read as real openings rather
    # than flat decals.
    cabinet.visual(Box((0.72, 0.56, 0.075)), origin=Origin(xyz=(0.0, 0.0, 0.0375)), material=black, name="floor_plinth")
    cabinet.visual(Box((0.05, 0.56, 1.48)), origin=Origin(xyz=(-0.335, 0.0, 0.79)), material=cabinet_red, name="side_panel_0")
    cabinet.visual(Box((0.05, 0.56, 1.48)), origin=Origin(xyz=(0.335, 0.0, 0.79)), material=cabinet_red, name="side_panel_1")
    cabinet.visual(Box((0.72, 0.05, 1.48)), origin=Origin(xyz=(0.0, 0.255, 0.79)), material=cabinet_red, name="rear_panel")
    cabinet.visual(Box((0.72, 0.56, 0.055)), origin=Origin(xyz=(0.0, 0.0, 1.345)), material=cabinet_red, name="top_tie")

    top_mesh = mesh_from_geometry(_arched_top_box(0.72, 0.56, 1.35, 1.62, 1.80), "curved_top_box")
    cabinet.visual(top_mesh, material=cabinet_red, name="curved_top_box")
    cabinet.visual(Box((0.50, 0.012, 0.16)), origin=Origin(xyz=(0.0, -0.286, 1.535)), material=warm_gold, name="top_marquee")
    cabinet.visual(Box((0.56, 0.014, 0.025)), origin=Origin(xyz=(0.0, -0.287, 1.43)), material=chrome, name="marquee_trim")

    # Reel window surround with a real open center.
    cabinet.visual(Box((0.055, 0.032, 0.46)), origin=Origin(xyz=(-0.3125, -0.296, 1.11)), material=chrome, name="reel_frame_left")
    cabinet.visual(Box((0.055, 0.032, 0.46)), origin=Origin(xyz=(0.3125, -0.296, 1.11)), material=chrome, name="reel_frame_right")
    cabinet.visual(Box((0.68, 0.032, 0.045)), origin=Origin(xyz=(0.0, -0.296, 1.3325)), material=chrome, name="reel_frame_top")
    cabinet.visual(Box((0.68, 0.032, 0.045)), origin=Origin(xyz=(0.0, -0.296, 0.8875)), material=chrome, name="reel_frame_bottom")
    cabinet.visual(Box((0.585, 0.006, 0.365)), origin=Origin(xyz=(0.0, -0.313, 1.11)), material=dark, name="reel_glass")

    # Lower service-door surround. The door itself is a child part recessed
    # behind this front plane.
    cabinet.visual(Box((0.065, 0.032, 0.64)), origin=Origin(xyz=(-0.3025, -0.296, 0.43)), material=chrome, name="door_jamb_0")
    cabinet.visual(Box((0.065, 0.032, 0.64)), origin=Origin(xyz=(0.3025, -0.296, 0.43)), material=chrome, name="door_jamb_1")
    cabinet.visual(Box((0.68, 0.032, 0.055)), origin=Origin(xyz=(0.0, -0.296, 0.105)), material=chrome, name="door_sill")
    cabinet.visual(Box((0.68, 0.032, 0.055)), origin=Origin(xyz=(0.0, -0.296, 0.735)), material=chrome, name="door_header")
    cabinet.visual(Box((0.011, 0.024, 0.54)), origin=Origin(xyz=(-0.2645, -0.291, 0.42)), material=chrome, name="hinge_leaf")

    # Projecting front shelf with a real ledge, front skirt, and under-braces.
    cabinet.visual(Box((0.68, 0.26, 0.055)), origin=Origin(xyz=(0.0, -0.41, 0.7625)), material=black, name="button_shelf")
    cabinet.visual(Box((0.68, 0.035, 0.105)), origin=Origin(xyz=(0.0, -0.535, 0.7125)), material=black, name="shelf_front_lip")
    cabinet.visual(Box((0.035, 0.19, 0.10)), origin=Origin(xyz=(-0.305, -0.39, 0.695)), material=rubber, name="shelf_brace_0")
    cabinet.visual(Box((0.035, 0.19, 0.10)), origin=Origin(xyz=(0.305, -0.39, 0.695)), material=rubber, name="shelf_brace_1")

    # Button sockets mounted in the ledge.
    button_positions = [-0.24, -0.12, 0.0, 0.12, 0.24]
    button_colors = [
        Material("button_red", rgba=(0.88, 0.03, 0.02, 1.0)),
        Material("button_yellow", rgba=(1.0, 0.78, 0.05, 1.0)),
        Material("button_green", rgba=(0.02, 0.62, 0.16, 1.0)),
        Material("button_blue", rgba=(0.04, 0.20, 0.86, 1.0)),
        Material("button_orange", rgba=(1.0, 0.34, 0.04, 1.0)),
    ]
    socket_top_z = 0.795
    for idx, x in enumerate(button_positions):
        cabinet.visual(
            Cylinder(radius=0.050, length=0.010),
            origin=Origin(xyz=(x, -0.42, socket_top_z - 0.005)),
            material=chrome,
            name=f"button_socket_{idx}",
        )
        button = model.part(f"button_{idx}")
        button.visual(
            Cylinder(radius=0.038, length=0.028),
            origin=Origin(xyz=(0.0, 0.0, 0.014)),
            material=button_colors[idx],
            name="cap",
        )
        button.visual(
            Cylinder(radius=0.028, length=0.004),
            origin=Origin(xyz=(0.0, 0.0, 0.030)),
            material=Material(f"button_highlight_{idx}", rgba=(1.0, 1.0, 1.0, 0.35)),
            name="top_highlight",
        )
        model.articulation(
            f"button_{idx}_slide",
            ArticulationType.PRISMATIC,
            parent=cabinet,
            child=button,
            origin=Origin(xyz=(x, -0.42, socket_top_z)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(effort=8.0, velocity=0.08, lower=0.0, upper=0.014),
        )

    # Three independently spinning mechanical reels visible through the window.
    reel_symbol_materials = [
        model.material("symbol_red", rgba=(0.85, 0.02, 0.02, 1.0)),
        model.material("symbol_green", rgba=(0.02, 0.55, 0.12, 1.0)),
        model.material("symbol_blue", rgba=(0.02, 0.14, 0.75, 1.0)),
        model.material("symbol_gold", rgba=(0.94, 0.65, 0.05, 1.0)),
    ]
    for idx, x in enumerate((-0.18, 0.0, 0.18)):
        cabinet.visual(
            Box((0.018, 0.50, 0.045)),
            origin=Origin(xyz=(x - 0.075, 0.015, 1.0755)),
            material=chrome,
            name=f"reel_bearing_{idx}_0",
        )
        cabinet.visual(
            Box((0.018, 0.50, 0.045)),
            origin=Origin(xyz=(x + 0.075, 0.015, 1.0755)),
            material=chrome,
            name=f"reel_bearing_{idx}_1",
        )
        reel = model.part(f"reel_{idx}")
        reel.visual(
            Cylinder(radius=0.125, length=0.118),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=reel_paper,
            name="drum",
        )
        reel.visual(
            Cylinder(radius=0.012, length=0.170),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=chrome,
            name="axle",
        )
        for s_idx, z in enumerate((-0.075, 0.0, 0.075)):
            reel.visual(
                Box((0.090, 0.004, 0.040)),
                origin=Origin(xyz=(0.0, -math.sqrt(0.125 * 0.125 - z * z) - 0.002, z)),
                material=reel_symbol_materials[(idx + s_idx) % len(reel_symbol_materials)],
                name=f"symbol_{s_idx}",
            )
        model.articulation(
            f"reel_{idx}_spin",
            ArticulationType.CONTINUOUS,
            parent=cabinet,
            child=reel,
            origin=Origin(xyz=(x, -0.155, 1.11)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=2.0, velocity=20.0),
        )

    # Recessed lower service door, carried on a vertical side hinge.
    door = model.part("service_door")
    door.visual(
        Box((0.49, 0.022, 0.52)),
        origin=Origin(xyz=(0.245, 0.011, 0.0)),
        material=service_blue,
        name="door_panel",
    )
    door.visual(
        Cylinder(radius=0.014, length=0.54),
        origin=Origin(xyz=(0.0, 0.011, 0.0)),
        material=chrome,
        name="hinge_barrel",
    )
    door.visual(
        Box((0.055, 0.018, 0.18)),
        origin=Origin(xyz=(0.38, -0.007, 0.06)),
        material=chrome,
        name="pull_handle",
    )
    door.visual(
        Box((0.20, 0.004, 0.040)),
        origin=Origin(xyz=(0.245, -0.001, 0.17)),
        material=black,
        name="service_label",
    )
    model.articulation(
        "door_hinge",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=door,
        origin=Origin(xyz=(-0.245, -0.302, 0.42)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.2, lower=0.0, upper=1.65),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
