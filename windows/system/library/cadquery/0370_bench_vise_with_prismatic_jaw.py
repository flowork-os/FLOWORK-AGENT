# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bench_vise_with_prismatic_jaw, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bench_vise_with_prismatic_jaw

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

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import pi
def _dovetail_prism_y(length: float, bottom_width: float, top_width: float, height: float) -> MeshGeometry:
    """Trapezoidal prism running along local Y, with its lower face at z=0."""
    y0 = -length / 2.0
    y1 = length / 2.0
    xb = bottom_width / 2.0
    xt = top_width / 2.0
    vertices = [
        (-xb, y0, 0.0),
        (xb, y0, 0.0),
        (xt, y0, height),
        (-xt, y0, height),
        (-xb, y1, 0.0),
        (xb, y1, 0.0),
        (xt, y1, height),
        (-xt, y1, height),
    ]
    faces = [
        (0, 1, 2),
        (0, 2, 3),
        (4, 6, 5),
        (4, 7, 6),
        (0, 4, 5),
        (0, 5, 1),
        (1, 5, 6),
        (1, 6, 2),
        (2, 6, 7),
        (2, 7, 3),
        (3, 7, 4),
        (3, 4, 0),
    ]
    return MeshGeometry(vertices=vertices, faces=faces)
def _dovetail_prism_x(length: float, bottom_width: float, top_width: float, height: float) -> MeshGeometry:
    """Trapezoidal prism running along local X, with its lower face at z=0."""
    x0 = -length / 2.0
    x1 = length / 2.0
    yb = bottom_width / 2.0
    yt = top_width / 2.0
    vertices = [
        (x0, -yb, 0.0),
        (x0, yb, 0.0),
        (x0, yt, height),
        (x0, -yt, height),
        (x1, -yb, 0.0),
        (x1, yb, 0.0),
        (x1, yt, height),
        (x1, -yt, height),
    ]
    faces = [
        (0, 1, 2),
        (0, 2, 3),
        (4, 6, 5),
        (4, 7, 6),
        (0, 4, 5),
        (0, 5, 1),
        (1, 5, 6),
        (1, 6, 2),
        (2, 6, 7),
        (2, 7, 3),
        (3, 7, 4),
        (3, 4, 0),
    ]
    return MeshGeometry(vertices=vertices, faces=faces)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cross_slide_milling_vise")

    model.material("painted_cast_iron", rgba=(0.16, 0.20, 0.22, 1.0))
    model.material("dark_cast_iron", rgba=(0.09, 0.10, 0.11, 1.0))
    model.material("machined_steel", rgba=(0.68, 0.70, 0.70, 1.0))
    model.material("blued_steel", rgba=(0.18, 0.19, 0.20, 1.0))
    model.material("black_handle", rgba=(0.02, 0.02, 0.018, 1.0))

    base = model.part("base")
    base.visual(
        Box((0.62, 0.36, 0.045)),
        origin=Origin(xyz=(0.0, 0.0, 0.0225)),
        material="painted_cast_iron",
        name="base_plate",
    )
    for x_pos, name in [(-0.16, "base_way_0"), (0.16, "base_way_1")]:
        base.visual(
            mesh_from_geometry(_dovetail_prism_y(0.39, 0.060, 0.110, 0.050), name),
            origin=Origin(xyz=(x_pos, 0.0, 0.045)),
            material="machined_steel",
            name=name,
        )
    # Low bolt pads and slots make the root read as a real milling-vise base.
    for x_pos in (-0.24, 0.24):
        for y_pos in (-0.125, 0.125):
            base.visual(
                Box((0.095, 0.055, 0.010)),
                origin=Origin(xyz=(x_pos, y_pos, 0.050)),
                material="dark_cast_iron",
                name=f"clamp_pad_{x_pos}_{y_pos}",
            )
            base.visual(
                Box((0.055, 0.018, 0.004)),
                origin=Origin(xyz=(x_pos, y_pos, 0.056)),
                material="blued_steel",
                name=f"bolt_slot_{x_pos}_{y_pos}",
            )

    cross_slide = model.part("cross_slide")
    for x_pos, name in [(-0.16, "lower_saddle_0"), (0.16, "lower_saddle_1")]:
        cross_slide.visual(
            Box((0.115, 0.305, 0.012)),
            origin=Origin(xyz=(x_pos, 0.0, 0.006)),
            material="dark_cast_iron",
            name=name,
        )
    cross_slide.visual(
        Box((0.49, 0.305, 0.045)),
        origin=Origin(xyz=(0.0, 0.0, 0.028)),
        material="painted_cast_iron",
        name="cross_plate",
    )
    for y_pos, name in [(-0.062, "bed_bar_0"), (0.062, "bed_bar_1")]:
        cross_slide.visual(
            Box((0.43, 0.070, 0.058)),
            origin=Origin(xyz=(-0.015, y_pos, 0.075)),
            material="painted_cast_iron",
            name=name,
        )
    for y_pos, name in [(-0.064, "jaw_way_0"), (0.064, "jaw_way_1")]:
        cross_slide.visual(
            mesh_from_geometry(_dovetail_prism_x(0.39, 0.040, 0.064, 0.030), name),
            origin=Origin(xyz=(-0.025, y_pos, 0.104)),
            material="machined_steel",
            name=name,
        )

    cross_slide.visual(
        Box((0.105, 0.205, 0.130)),
        origin=Origin(xyz=(0.145, 0.0, 0.234)),
        material="painted_cast_iron",
        name="rear_jaw_block",
    )
    cross_slide.visual(
        Box((0.105, 0.205, 0.072)),
        origin=Origin(xyz=(0.145, 0.0, 0.135)),
        material="painted_cast_iron",
        name="rear_jaw_pedestal",
    )
    cross_slide.visual(
        Box((0.012, 0.180, 0.078)),
        origin=Origin(xyz=(0.087, 0.0, 0.242)),
        material="machined_steel",
        name="rear_jaw_face",
    )
    for y_pos in (-0.055, 0.0, 0.055):
        cross_slide.visual(
            Box((0.004, 0.006, 0.070)),
            origin=Origin(xyz=(0.079, y_pos, 0.242)),
            material="blued_steel",
            name=f"rear_face_groove_{y_pos}",
        )

    # A forked front screw bearing leaves a visible clearance hole for the screw.
    for y_pos, name in [(-0.048, "screw_post_0"), (0.048, "screw_post_1")]:
        cross_slide.visual(
            Box((0.032, 0.026, 0.088)),
            origin=Origin(xyz=(-0.242, y_pos, 0.091)),
            material="painted_cast_iron",
            name=name,
        )
    cross_slide.visual(
        Box((0.040, 0.070, 0.042)),
        origin=Origin(xyz=(-0.242, 0.0, 0.083)),
        material="painted_cast_iron",
        name="screw_bearing",
    )
    cross_slide.visual(
        Box((0.032, 0.122, 0.023)),
        origin=Origin(xyz=(-0.242, 0.0, 0.145)),
        material="painted_cast_iron",
        name="screw_bridge",
    )

    leadscrew = model.part("leadscrew")
    leadscrew.visual(
        Cylinder(radius=0.009, length=0.380),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material="machined_steel",
        name="screw_shaft",
    )
    for i, x_pos in enumerate((-0.150, -0.105, -0.060, -0.015, 0.030, 0.075, 0.120, 0.165)):
        leadscrew.visual(
            Cylinder(radius=0.0105, length=0.004),
            origin=Origin(xyz=(x_pos, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
            material="blued_steel",
            name=f"thread_crest_{i}",
        )
    leadscrew.visual(
        Cylinder(radius=0.015, length=0.080),
        origin=Origin(xyz=(-0.230, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material="machined_steel",
        name="wheel_hub",
    )
    leadscrew.visual(
        Cylinder(radius=0.048, length=0.015),
        origin=Origin(xyz=(-0.275, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material="blued_steel",
        name="handwheel",
    )
    leadscrew.visual(
        Cylinder(radius=0.0045, length=0.100),
        origin=Origin(xyz=(-0.275, 0.022, 0.0), rpy=(pi / 2.0, 0.0, 0.0)),
        material="machined_steel",
        name="wheel_spoke",
    )
    leadscrew.visual(
        Cylinder(radius=0.011, length=0.034),
        origin=Origin(xyz=(-0.275, 0.064, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material="black_handle",
        name="spinner_knob",
    )

    front_jaw = model.part("front_jaw")
    front_jaw.visual(
        Box((0.155, 0.182, 0.036)),
        origin=Origin(xyz=(0.0, 0.0, 0.018)),
        material="dark_cast_iron",
        name="jaw_saddle",
    )
    front_jaw.visual(
        Box((0.094, 0.205, 0.128)),
        origin=Origin(xyz=(0.0, 0.0, 0.098)),
        material="painted_cast_iron",
        name="front_jaw_block",
    )
    front_jaw.visual(
        Box((0.012, 0.180, 0.078)),
        origin=Origin(xyz=(0.053, 0.0, 0.108)),
        material="machined_steel",
        name="front_jaw_face",
    )
    for y_pos in (-0.055, 0.0, 0.055):
        front_jaw.visual(
            Box((0.004, 0.006, 0.070)),
            origin=Origin(xyz=(0.060, y_pos, 0.108)),
            material="blued_steel",
            name=f"front_face_groove_{y_pos}",
        )

    model.articulation(
        "cross_travel",
        ArticulationType.PRISMATIC,
        parent=base,
        child=cross_slide,
        origin=Origin(xyz=(0.0, 0.0, 0.095)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=350.0, velocity=0.18, lower=-0.060, upper=0.060),
    )
    model.articulation(
        "leadscrew_turn",
        ArticulationType.REVOLUTE,
        parent=cross_slide,
        child=leadscrew,
        origin=Origin(xyz=(-0.105, 0.0, 0.083)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=2.5, lower=0.0, upper=8.0),
    )
    model.articulation(
        "jaw_travel",
        ArticulationType.PRISMATIC,
        parent=cross_slide,
        child=front_jaw,
        origin=Origin(xyz=(-0.140, 0.0, 0.134)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=800.0, velocity=0.05, lower=0.0, upper=0.080),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
