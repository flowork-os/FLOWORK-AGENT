# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, blender, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: blender

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

# ===== brackets_hinges_bezels (13 syms) =====
def _identity4():
    return (
        (1.0, 0.0, 0.0, 0.0),
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )

def _rpy_matrix(roll, pitch, yaw):
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    return (
        (cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
        (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
        (-sp, cp * sr, cp * cr),
    )

def _origin_to_mat4(origin):
    if origin is None:
        return _identity4()
    ox, oy, oz = origin.xyz
    rr, rp, ry = origin.rpy
    r = _rpy_matrix(float(rr), float(rp), float(ry))
    return (
        (r[0][0], r[0][1], r[0][2], float(ox)),
        (r[1][0], r[1][1], r[1][2], float(oy)),
        (r[2][0], r[2][1], r[2][2], float(oz)),
        (0.0, 0.0, 0.0, 1.0),
    )

def _mat4_vec3(mat, vec):
    x, y, z = vec
    return (
        mat[0][0] * x + mat[0][1] * y + mat[0][2] * z + mat[0][3],
        mat[1][0] * x + mat[1][1] * y + mat[1][2] * z + mat[1][3],
        mat[2][0] * x + mat[2][1] * y + mat[2][2] * z + mat[2][3],
    )

def _transform_aabb(aabb, tf):
    (min_x, min_y, min_z), (max_x, max_y, max_z) = aabb
    corners = [(x, y, z) for x in (min_x, max_x) for y in (min_y, max_y) for z in (min_z, max_z)]
    tx0 = ty0 = tz0 = float("inf")
    tx1 = ty1 = tz1 = float("-inf")
    for c in corners:
        x, y, z = _mat4_vec3(tf, c)
        tx0, ty0, tz0 = min(tx0, x), min(ty0, y), min(tz0, z)
        tx1, ty1, tz1 = max(tx1, x), max(ty1, y), max(tz1, z)
    return (tx0, ty0, tz0), (tx1, ty1, tz1)

def _aabb_union(items):
    if not items:
        raise ValidationError("Cannot union empty AABB list")
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    for mn, mx in items:
        for i in range(3):
            mins[i] = min(mins[i], mn[i])
            maxs[i] = max(maxs[i], mx[i])
    return (mins[0], mins[1], mins[2]), (maxs[0], maxs[1], maxs[2])

def _geometry_local_aabb(geometry):
    if isinstance(geometry, Box):
        sx, sy, sz = geometry.size
        return ((-sx / 2.0, -sy / 2.0, -sz / 2.0), (sx / 2.0, sy / 2.0, sz / 2.0))
    if isinstance(geometry, Cylinder):
        r = float(geometry.radius)
        length = float(geometry.length)
        return ((-r, -r, -length / 2.0), (r, r, length / 2.0))
    if isinstance(geometry, Sphere):
        r = float(geometry.radius)
        return ((-r, -r, -r), (r, r, r))
    shape = _to_shape(geometry)
    bb = shape.BoundingBox()
    return ((bb.xmin, bb.ymin, bb.zmin), (bb.xmax, bb.ymax, bb.zmax))

def _iter_subject_items(subject, *, prefer_collisions):
    if isinstance(subject, Part):
        collisions = list(getattr(subject, "collisions", []) or [])
        if prefer_collisions and collisions:
            items = collisions
        elif subject.visuals:
            items = list(subject.visuals)
        else:
            items = collisions
        return [
            (item.geometry, _origin_to_mat4(getattr(item, "origin", None)))
            for item in items
            if getattr(item, "geometry", None) is not None
        ]
    if isinstance(subject, Visual):
        return [(subject.geometry, _origin_to_mat4(subject.origin))]
    return [(subject, _identity4())]

def link_local_aabbs(link, *, asset_root=None, prefer_collisions=True):
    items = _iter_subject_items(link, prefer_collisions=prefer_collisions)
    return [_transform_aabb(_geometry_local_aabb(g), tf) for g, tf in items]

_FACE_TABLE = {
    "+x": (0, +1.0, (0.0, math.pi / 2.0, 0.0)),
    "-x": (0, -1.0, (0.0, -math.pi / 2.0, 0.0)),
    "+y": (1, +1.0, (-math.pi / 2.0, 0.0, 0.0)),
    "-y": (1, -1.0, (math.pi / 2.0, 0.0, 0.0)),
    "+z": (2, +1.0, (0.0, 0.0, 0.0)),
    "-z": (2, -1.0, (math.pi, 0.0, 0.0)),
}

_FACE_TANGENT_AXES = {
    "+x": (1, 2), "-x": (1, 2),
    "+y": (0, 2), "-y": (0, 2),
    "+z": (0, 1), "-z": (0, 1),
}

def _as_pair(values, *, name):
    try:
        if len(values) != 2:
            raise ValidationError(f"{name} must have 2 elements")
        return (float(values[0]), float(values[1]))
    except TypeError as exc:
        raise ValidationError(f"{name} must have 2 elements") from exc

def place_on_face(
    parent_link,
    face,
    *,
    face_pos=(0.0, 0.0),
    proud=0.0,
    asset_root=None,
    prefer_collisions=True,
):
    """Compute an Origin that places a child on a face of the parent's AABB."""
    face_key = face.strip().lower()
    if face_key not in _FACE_TABLE:
        raise ValidationError(
            f"Invalid face {face!r}; expected one of: {', '.join(sorted(_FACE_TABLE))}"
        )
    axis_idx, sign, rpy = _FACE_TABLE[face_key]
    tang_a, tang_b = _FACE_TANGENT_AXES[face_key]
    face_pos_pair = _as_pair(face_pos, name="face_pos")

    aabbs = link_local_aabbs(parent_link, prefer_collisions=prefer_collisions)
    if not aabbs:
        raise ValidationError(f"Parent link {parent_link.name!r} has no geometry to compute AABB")
    (mn, mx) = _aabb_union(aabbs)

    surface = float(mx[axis_idx]) if sign > 0 else float(mn[axis_idx])
    normal_coord = surface + sign * float(proud)

    xyz = [0.0, 0.0, 0.0]
    xyz[axis_idx] = normal_coord
    xyz[tang_a] = face_pos_pair[0]
    xyz[tang_b] = face_pos_pair[1]
    return Origin(xyz=(xyz[0], xyz[1], xyz[2]), rpy=rpy)

# ===== model =====
import cadquery as cq
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="blender")

    # 1. Base
    base = model.part("base")

    base_cq = cq.Workplane("XY").rect(0.16, 0.16).extrude(0.18).edges("|Z").fillet(0.03)
    
    # Base collar for jar
    collar = cq.Workplane("XY").workplane(offset=0.18).circle(0.06).extrude(0.02)
    base_cq = base_cq.union(collar)
    
    # Hole in collar
    collar_hole = cq.Workplane("XY").workplane(offset=0.18).circle(0.05).extrude(0.02)
    base_cq = base_cq.cut(collar_hole)

    base.visual(
        mesh_from_cadquery(base_cq, "base_mesh"),
        origin=Origin(xyz=(0, 0, 0)),
        name="motor_base",
        color=(0.15, 0.15, 0.15),
    )

    # Feet
    for dx in [-0.06, 0.06]:
        for dy in [-0.06, 0.06]:
            base.visual(
                Cylinder(radius=0.015, length=0.01),
                origin=Origin(xyz=(dx, dy, -0.005)),
                name=f"foot_{dx}_{dy}",
                color=(0.05, 0.05, 0.05),
            )

    # 2. Controls
    dial = model.part("dial")
    dial_cq = cq.Workplane("XY").circle(0.025).extrude(0.015).edges(">Z").fillet(0.005)
    indicator = cq.Workplane("XY").rect(0.005, 0.04).extrude(0.016)
    dial_cq = dial_cq.union(indicator)

    dial.visual(
        mesh_from_cadquery(dial_cq, "dial_mesh"),
        origin=Origin(),
        name="dial_knob",
        color=(0.8, 0.8, 0.8),
    )

    dial_origin = place_on_face(
        base,
        "-y",
        face_pos=(0, 0.12),
        proud=-0.001
    )

    model.articulation(
        "base_to_dial",
        ArticulationType.REVOLUTE,
        parent=base,
        child=dial,
        origin=dial_origin,
        axis=(0, 0, 1),
        motion_limits=MotionLimits(lower=-2.0, upper=2.0),
    )

    for i, dx in enumerate([-0.03, 0, 0.03]):
        btn = model.part(f"button_{i}")
        btn.visual(
            Box((0.02, 0.01, 0.01)),
            origin=Origin(),
            name=f"btn_vis_{i}",
            color=(0.8, 0.8, 0.8),
        )
        btn_origin = place_on_face(
            base,
            "-y",
            face_pos=(dx, 0.06),
            proud=0.004
        )
        model.articulation(
            f"base_to_button_{i}",
            ArticulationType.PRISMATIC,
            parent=base,
            child=btn,
            origin=btn_origin,
            axis=(0, 0, -1),
            motion_limits=MotionLimits(lower=0, upper=0.005),
        )

    # 3. Jar
    jar = model.part("jar")

    jar_body = cq.Workplane("XY").circle(0.055).extrude(0.24, taper=-2)
    jar_body = jar_body.faces(">Z").shell(-0.004)

    handle_outer = cq.Workplane("XZ").center(0.07, 0.12).rect(0.06, 0.16).extrude(0.015, both=True).edges().fillet(0.005)
    handle_inner = cq.Workplane("XZ").center(0.08, 0.12).rect(0.03, 0.12).extrude(0.02, both=True)
    handle_cq = handle_outer.cut(handle_inner)

    jar_cq = jar_body.union(handle_cq)

    jar_base = cq.Workplane("XY").workplane(offset=-0.02).circle(0.048).extrude(0.02)
    jar_cq = jar_cq.union(jar_base)

    jar.visual(
        mesh_from_cadquery(jar_cq, "jar_mesh"),
        origin=Origin(xyz=(0, 0, 0)),
        name="pitcher",
        color=(0.8, 0.9, 1.0, 0.4),
    )

    model.articulation(
        "base_to_jar",
        ArticulationType.PRISMATIC,
        parent=base,
        child=jar,
        origin=Origin(xyz=(0, 0, 0.20)),
        axis=(0, 0, 1),
        motion_limits=MotionLimits(lower=0, upper=0.30),
    )

    # 4. Blade
    blade = model.part("blade")
    blade_cq = cq.Workplane("XY").rect(0.07, 0.015).extrude(0.002)
    blade_cq = blade_cq.union(cq.Workplane("XY").rect(0.015, 0.07).extrude(0.002))
    blade_stem = cq.Workplane("XY").workplane(offset=-0.02).circle(0.006).extrude(0.022)
    blade_cq = blade_cq.union(blade_stem)

    blade.visual(
        mesh_from_cadquery(blade_cq, "blade_mesh"),
        origin=Origin(xyz=(0, 0, 0)),
        name="blade_metal",
        color=(0.7, 0.7, 0.7),
    )

    model.articulation(
        "jar_to_blade",
        ArticulationType.CONTINUOUS,
        parent=jar,
        child=blade,
        origin=Origin(xyz=(0, 0, 0.005)),
        axis=(0, 0, 1),
        motion_limits=MotionLimits(effort=1.0, velocity=10.0),
    )

    # 5. Lid
    lid = model.part("lid")

    lid_cq = cq.Workplane("XY").circle(0.065).extrude(0.01)
    lid_plug = (
        cq.Workplane("XY")
        .workplane(offset=-0.015)
        .circle(0.05)
        .extrude(0.015)
    )
    lid_cq = lid_cq.union(lid_plug)

    cap = cq.Workplane("XY").workplane(offset=0.01).circle(0.03).extrude(0.01)
    lid_cq = lid_cq.union(cap)

    lid.visual(
        mesh_from_cadquery(lid_cq, "lid_mesh"),
        origin=Origin(xyz=(0, 0, 0)),
        name="lid_cap",
        color=(0.1, 0.1, 0.1),
    )

    model.articulation(
        "jar_to_lid",
        ArticulationType.PRISMATIC,
        parent=jar,
        child=lid,
        origin=Origin(xyz=(0, 0, 0.24)),
        axis=(0, 0, 1),
        motion_limits=MotionLimits(lower=0, upper=0.15),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
