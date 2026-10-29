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
def _dovetail_prism_x(
    *,
    length: float,
    center_y: float,
    z0: float,
    bottom_width: float,
    top_width: float,
    height: float,
) -> MeshGeometry:
    """Trapezoidal dovetail rail extruded along local X."""
    profile = [
        (center_y - bottom_width / 2.0, z0),
        (center_y + bottom_width / 2.0, z0),
        (center_y + top_width / 2.0, z0 + height),
        (center_y - top_width / 2.0, z0 + height),
    ]
    geom = MeshGeometry()
    xs = (-length / 2.0, length / 2.0)
    for x in xs:
        for y, z in profile:
            geom.add_vertex(x, y, z)

    # End caps.
    geom.add_face(0, 1, 2)
    geom.add_face(0, 2, 3)
    geom.add_face(4, 6, 5)
    geom.add_face(4, 7, 6)

    # Side faces.
    for i in range(4):
        j = (i + 1) % 4
        a, b = i, j
        c, d = 4 + j, 4 + i
        geom.add_face(a, b, c)
        geom.add_face(a, c, d)
    return geom
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="compound_angle_vise")

    model.material("cast_blue", rgba=(0.05, 0.18, 0.32, 1.0))
    model.material("dark_cast", rgba=(0.035, 0.04, 0.045, 1.0))
    model.material("machined_steel", rgba=(0.62, 0.64, 0.62, 1.0))
    model.material("hardened_jaw", rgba=(0.80, 0.78, 0.70, 1.0))
    model.material("blackened_steel", rgba=(0.015, 0.014, 0.012, 1.0))

    base = model.part("base_plate")
    base.visual(
        Box((0.56, 0.32, 0.032)),
        origin=Origin(xyz=(0.0, 0.0, 0.016)),
        material="dark_cast",
        name="flat_base_plate",
    )
    for x in (-0.19, 0.19):
        for y in (-0.115, 0.115):
            base.visual(
                Box((0.105, 0.020, 0.002)),
                origin=Origin(xyz=(x, y, 0.033)),
                material="blackened_steel",
                name=f"mount_slot_{x:+.2f}_{y:+.2f}",
            )
    base.visual(
        Cylinder(radius=0.030, length=0.003),
        origin=Origin(xyz=(0.0, 0.0, 0.0335)),
        material="machined_steel",
        name="swivel_pivot_washer",
    )

    swivel = model.part("swivel_stage")
    swivel.visual(
        Cylinder(radius=0.170, length=0.035),
        origin=Origin(xyz=(0.0, 0.0, 0.0175)),
        material="cast_blue",
        name="swivel_disk",
    )
    swivel.visual(
        mesh_from_geometry(TorusGeometry(0.158, 0.0035, radial_segments=20, tubular_segments=64), "swivel_degree_ring"),
        origin=Origin(xyz=(0.0, 0.0, 0.038)),
        material="machined_steel",
        name="degree_ring",
    )
    swivel.visual(
        Cylinder(radius=0.055, length=0.034),
        origin=Origin(xyz=(0.0, 0.0, 0.052)),
        material="cast_blue",
        name="central_boss",
    )
    swivel.visual(
        Box((0.190, 0.205, 0.025)),
        origin=Origin(xyz=(0.0, 0.0, 0.0475)),
        material="cast_blue",
        name="tilt_yoke_foot",
    )
    for idx, y in enumerate((-0.125, 0.125)):
        swivel.visual(
            Box((0.090, 0.035, 0.120)),
            origin=Origin(xyz=(0.0, y, 0.095)),
            material="cast_blue",
            name=f"yoke_cheek_{idx}",
        )

    tilt = model.part("tilt_stage")
    tilt.visual(
        Cylinder(radius=0.017, length=0.300),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material="machined_steel",
        name="trunnion_pin",
    )
    tilt.visual(
        Box((0.460, 0.180, 0.040)),
        origin=Origin(xyz=(0.0, 0.0, 0.045)),
        material="cast_blue",
        name="tilting_bed",
    )
    for idx, y in enumerate((-0.075, 0.075)):
        tilt.visual(
            Box((0.080, 0.035, 0.035)),
            origin=Origin(xyz=(0.0, y, 0.015)),
            material="cast_blue",
            name=f"trunnion_lug_{idx}",
        )
    for idx, y in enumerate((-0.052, 0.052)):
        rail = _dovetail_prism_x(
            length=0.420,
            center_y=y,
            z0=0.063,
            bottom_width=0.026,
            top_width=0.045,
            height=0.018,
        )
        tilt.visual(
            mesh_from_geometry(rail, f"dovetail_way_{idx}"),
            origin=Origin(xyz=(-0.005, 0.0, 0.0)),
            material="machined_steel",
            name=f"dovetail_way_{idx}",
        )

    # The fixed jaw rises on two side ribs, leaving a central screw channel.
    for idx, y in enumerate((-0.060, 0.060)):
        tilt.visual(
            Box((0.075, 0.040, 0.042)),
            origin=Origin(xyz=(0.145, y, 0.083)),
            material="cast_blue",
            name=f"fixed_jaw_rib_{idx}",
        )
    tilt.visual(
        Box((0.080, 0.180, 0.095)),
        origin=Origin(xyz=(0.145, 0.0, 0.1495)),
        material="cast_blue",
        name="fixed_jaw_block",
    )
    tilt.visual(
        Box((0.009, 0.155, 0.070)),
        origin=Origin(xyz=(0.1005, 0.0, 0.148)),
        material="hardened_jaw",
        name="fixed_jaw_plate",
    )
    for idx, z in enumerate((0.122, 0.135, 0.148, 0.161, 0.174)):
        tilt.visual(
            Box((0.0015, 0.142, 0.003)),
            origin=Origin(xyz=(0.0953, 0.0, z)),
            material="blackened_steel",
            name=f"fixed_jaw_serration_{idx}",
        )

    tilt.visual(
        Box((0.035, 0.050, 0.005)),
        origin=Origin(xyz=(-0.205, 0.0, 0.0675)),
        material="cast_blue",
        name="screw_bearing_base",
    )
    tilt.visual(
        mesh_from_geometry(TorusGeometry(0.012, 0.003, radial_segments=16, tubular_segments=32), "front_screw_bearing"),
        origin=Origin(xyz=(-0.205, 0.0, 0.078), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="machined_steel",
        name="front_screw_bearing",
    )

    moving = model.part("moving_jaw")
    for idx, y in enumerate((-0.052, 0.052)):
        moving.visual(
            Box((0.120, 0.035, 0.018)),
            origin=Origin(xyz=(-0.040, y, 0.090)),
            material="cast_blue",
            name=f"slide_shoe_{idx}",
        )
    moving.visual(
        Box((0.150, 0.130, 0.006)),
        origin=Origin(xyz=(-0.040, 0.0, 0.100)),
        material="cast_blue",
        name="jaw_saddle",
    )
    moving.visual(
        Box((0.075, 0.180, 0.095)),
        origin=Origin(xyz=(-0.035, 0.0, 0.1485)),
        material="cast_blue",
        name="moving_jaw_block",
    )
    moving.visual(
        Box((0.009, 0.155, 0.070)),
        origin=Origin(xyz=(0.0070, 0.0, 0.148)),
        material="hardened_jaw",
        name="moving_jaw_plate",
    )
    for idx, z in enumerate((0.122, 0.135, 0.148, 0.161, 0.174)):
        moving.visual(
            Box((0.0015, 0.142, 0.003)),
            origin=Origin(xyz=(0.0122, 0.0, z)),
            material="blackened_steel",
            name=f"moving_jaw_serration_{idx}",
        )

    leadscrew = model.part("leadscrew")
    leadscrew.visual(
        Cylinder(radius=0.0065, length=0.390),
        origin=Origin(xyz=(-0.055, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="machined_steel",
        name="screw_shaft",
    )
    leadscrew.visual(
        Cylinder(radius=0.0095, length=0.012),
        origin=Origin(xyz=(-0.205, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="machined_steel",
        name="bearing_journal",
    )
    for idx, x in enumerate((-0.165, -0.140, -0.115, -0.090, -0.065, -0.040, -0.015, 0.010, 0.035, 0.060, 0.085, 0.110)):
        leadscrew.visual(
            Cylinder(radius=0.0082, length=0.003),
            origin=Origin(xyz=(x, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material="blackened_steel",
            name=f"thread_crest_{idx}",
        )
    leadscrew.visual(
        Cylinder(radius=0.015, length=0.024),
        origin=Origin(xyz=(-0.265, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="machined_steel",
        name="handwheel_hub",
    )
    leadscrew.visual(
        Cylinder(radius=0.006, length=0.070),
        origin=Origin(xyz=(-0.270, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="machined_steel",
        name="handle_stem",
    )
    leadscrew.visual(
        mesh_from_geometry(TorusGeometry(0.034, 0.004, radial_segments=16, tubular_segments=56), "handwheel_rim"),
        origin=Origin(xyz=(-0.265, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="blackened_steel",
        name="handwheel_rim",
    )
    leadscrew.visual(
        Cylinder(radius=0.0028, length=0.072),
        origin=Origin(xyz=(-0.265, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material="machined_steel",
        name="handwheel_spoke_y",
    )
    leadscrew.visual(
        Cylinder(radius=0.0028, length=0.072),
        origin=Origin(xyz=(-0.265, 0.0, 0.0)),
        material="machined_steel",
        name="handwheel_spoke_z",
    )
    leadscrew.visual(
        Cylinder(radius=0.004, length=0.110),
        origin=Origin(xyz=(-0.286, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material="machined_steel",
        name="tee_handle_bar",
    )
    for idx, y in enumerate((-0.055, 0.055)):
        leadscrew.visual(
            Sphere(radius=0.008),
            origin=Origin(xyz=(-0.286, y, 0.0)),
            material="blackened_steel",
            name=f"tee_handle_knob_{idx}",
        )

    model.articulation(
        "base_to_swivel",
        ArticulationType.REVOLUTE,
        parent=base,
        child=swivel,
        origin=Origin(xyz=(0.0, 0.0, 0.032)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=80.0, velocity=1.2, lower=-math.pi, upper=math.pi),
    )
    model.articulation(
        "swivel_to_tilt",
        ArticulationType.REVOLUTE,
        parent=swivel,
        child=tilt,
        origin=Origin(xyz=(0.0, 0.0, 0.125)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=100.0, velocity=0.8, lower=-0.65, upper=0.65),
    )
    model.articulation(
        "tilt_to_moving_jaw",
        ArticulationType.PRISMATIC,
        parent=tilt,
        child=moving,
        origin=Origin(xyz=(0.045, 0.0, 0.0)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=250.0, velocity=0.08, lower=0.0, upper=0.120),
    )
    model.articulation(
        "tilt_to_leadscrew",
        ArticulationType.CONTINUOUS,
        parent=tilt,
        child=leadscrew,
        origin=Origin(xyz=(0.0, 0.0, 0.078)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=8.0),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
