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

# ===== primitives (2 syms) =====
def _coerce_positive_radii3(value, *, name):
    """Verbatim port of the sdk helper: accept a positive scalar or a positive
    3-sequence and return an (rx, ry, rz) tuple."""
    if isinstance(value, (int, float)):
        radius = float(value)
        if radius <= 0.0:
            raise ValidationError("%s must be positive" % name)
        return (radius, radius, radius)
    if len(value) != 3:
        raise ValidationError("%s must be a positive float or a 3-sequence" % name)
    rx = float(value[0])
    ry = float(value[1])
    rz = float(value[2])
    if rx <= 0.0 or ry <= 0.0 or rz <= 0.0:
        raise ValidationError("%s values must be positive" % name)
    return (rx, ry, rz)

class DomeGeometry(MeshGeometry):
    def __init__(self, radius, *, radial_segments=24, height_segments=12, closed=True):
        super().__init__()
        rx, ry, rz = _coerce_positive_radii3(radius, name="radius")
        # upper hemisphere (z>=0) of a unit sphere, scaled to the half-ellipsoid
        hemi = cq.Solid.makeSphere(
            1.0, angleDegrees1=0, angleDegrees2=90, angleDegrees3=360
        )
        m = cq.Matrix([[rx, 0, 0, 0], [0, ry, 0, 0], [0, 0, rz, 0]])
        solid = hemi.transformGeometry(m)
        self._set(solid)

# ===== model =====
import math
OUTER_TOP_Z = 0.045
OUTER_BOTTOM_Z = -0.900
OUTER_SIDE = 0.240
OUTER_BORE = 0.170
INNER_SIDE = 0.138
POST_LENGTH = 0.900
POST_TRAVEL = 0.650
HINGE_X = -0.125
HINGE_Z = 0.018
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="telescoping_street_bollard")

    galvanized = model.material("galvanized_steel", rgba=(0.55, 0.58, 0.60, 1.0))
    dark_steel = model.material("dark_oiled_steel", rgba=(0.08, 0.09, 0.10, 1.0))
    safety_yellow = model.material("safety_yellow", rgba=(0.98, 0.72, 0.08, 1.0))
    black = model.material("black_band", rgba=(0.02, 0.02, 0.018, 1.0))
    concrete = model.material("brushed_concrete", rgba=(0.48, 0.47, 0.43, 1.0))
    rubber = model.material("dark_rubber", rgba=(0.015, 0.015, 0.014, 1.0))

    outer_sleeve = model.part("outer_sleeve")
    slab_outer = 0.660
    slab_hole = OUTER_SIDE
    slab_thickness = 0.070
    slab_band = (slab_outer - slab_hole) * 0.5
    outer_sleeve.visual(
        Box((slab_outer, slab_band, slab_thickness)),
        origin=Origin(xyz=(0.0, (slab_outer + slab_hole) * 0.25, -slab_thickness * 0.5)),
        material=concrete,
        name="concrete_front",
    )
    outer_sleeve.visual(
        Box((slab_outer, slab_band, slab_thickness)),
        origin=Origin(xyz=(0.0, -(slab_outer + slab_hole) * 0.25, -slab_thickness * 0.5)),
        material=concrete,
        name="concrete_rear",
    )
    outer_sleeve.visual(
        Box((slab_band, slab_hole, slab_thickness)),
        origin=Origin(xyz=((slab_outer + slab_hole) * 0.25, 0.0, -slab_thickness * 0.5)),
        material=concrete,
        name="concrete_side_0",
    )
    outer_sleeve.visual(
        Box((slab_band, slab_hole, slab_thickness)),
        origin=Origin(xyz=(-(slab_outer + slab_hole) * 0.25, 0.0, -slab_thickness * 0.5)),
        material=concrete,
        name="concrete_side_1",
    )

    sleeve_height = OUTER_TOP_Z - OUTER_BOTTOM_Z
    outer_sleeve.visual(
        Box((OUTER_SIDE, (OUTER_SIDE - OUTER_BORE) * 0.5, sleeve_height)),
        origin=Origin(xyz=(0.0, (OUTER_SIDE + OUTER_BORE) * 0.25, (OUTER_TOP_Z + OUTER_BOTTOM_Z) * 0.5)),
        material=galvanized,
        name="sleeve_front_wall",
    )
    outer_sleeve.visual(
        Box((OUTER_SIDE, (OUTER_SIDE - OUTER_BORE) * 0.5, sleeve_height)),
        origin=Origin(xyz=(0.0, -(OUTER_SIDE + OUTER_BORE) * 0.25, (OUTER_TOP_Z + OUTER_BOTTOM_Z) * 0.5)),
        material=galvanized,
        name="sleeve_rear_wall",
    )
    outer_sleeve.visual(
        Box(((OUTER_SIDE - OUTER_BORE) * 0.5, OUTER_BORE, sleeve_height)),
        origin=Origin(xyz=((OUTER_SIDE + OUTER_BORE) * 0.25, 0.0, (OUTER_TOP_Z + OUTER_BOTTOM_Z) * 0.5)),
        material=galvanized,
        name="sleeve_side_wall_0",
    )
    outer_sleeve.visual(
        Box(((OUTER_SIDE - OUTER_BORE) * 0.5, OUTER_BORE, sleeve_height)),
        origin=Origin(xyz=(-(OUTER_SIDE + OUTER_BORE) * 0.25, 0.0, (OUTER_TOP_Z + OUTER_BOTTOM_Z) * 0.5)),
        material=galvanized,
        name="sleeve_side_wall_1",
    )
    flange_outer = 0.285
    flange_inner = 0.178
    flange_thickness = (flange_outer - flange_inner) * 0.5
    flange_z = OUTER_TOP_Z - 0.006
    outer_sleeve.visual(
        Box((flange_outer, flange_thickness, 0.012)),
        origin=Origin(xyz=(0.0, (flange_outer + flange_inner) * 0.25, flange_z)),
        material=galvanized,
        name="flange_front",
    )
    outer_sleeve.visual(
        Box((flange_outer, flange_thickness, 0.012)),
        origin=Origin(xyz=(0.0, -(flange_outer + flange_inner) * 0.25, flange_z)),
        material=galvanized,
        name="flange_rear",
    )
    outer_sleeve.visual(
        Box((flange_thickness, flange_inner, 0.012)),
        origin=Origin(xyz=((flange_outer + flange_inner) * 0.25, 0.0, flange_z)),
        material=galvanized,
        name="flange_side_0",
    )
    outer_sleeve.visual(
        Box((flange_thickness, flange_inner, 0.012)),
        origin=Origin(xyz=(-(flange_outer + flange_inner) * 0.25, 0.0, flange_z)),
        material=galvanized,
        name="flange_side_1",
    )
    outer_sleeve.visual(
        Box((OUTER_SIDE, OUTER_SIDE, 0.006)),
        origin=Origin(xyz=(0.0, 0.0, OUTER_BOTTOM_Z + 0.010)),
        material=dark_steel,
        name="dark_socket_bottom",
    )

    inner_post = model.part("inner_post")
    inner_post.visual(
        Box((INNER_SIDE, INNER_SIDE, POST_LENGTH)),
        origin=Origin(xyz=(0.0, 0.0, -POST_LENGTH * 0.5)),
        material=safety_yellow,
        name="post_body",
    )
    # Four narrow black bands are modeled as shallow strapped plates on the square post.
    for idx, zc in enumerate((-0.165, -0.330)):
        inner_post.visual(
            Box((INNER_SIDE + 0.004, 0.006, 0.040)),
            origin=Origin(xyz=(0.0, INNER_SIDE * 0.5 + 0.003, zc)),
            material=black,
            name=f"front_band_{idx}",
        )
        inner_post.visual(
            Box((INNER_SIDE + 0.004, 0.006, 0.040)),
            origin=Origin(xyz=(0.0, -INNER_SIDE * 0.5 - 0.003, zc)),
            material=black,
            name=f"rear_band_{idx}",
        )
        inner_post.visual(
            Box((0.006, INNER_SIDE + 0.004, 0.040)),
            origin=Origin(xyz=(INNER_SIDE * 0.5 + 0.003, 0.0, zc)),
            material=black,
            name=f"side_band_{idx}_0",
        )
        inner_post.visual(
            Box((0.006, INNER_SIDE + 0.004, 0.040)),
            origin=Origin(xyz=(-INNER_SIDE * 0.5 - 0.003, 0.0, zc)),
            material=black,
            name=f"side_band_{idx}_1",
        )
    inner_post.visual(
        Box((0.016, 0.095, 0.025)),
        origin=Origin(xyz=(-0.077, 0.0, -0.0125)),
        material=dark_steel,
        name="hinge_leaf",
    )
    inner_post.visual(
        Box((INNER_SIDE + 0.010, INNER_SIDE + 0.010, 0.010)),
        origin=Origin(xyz=(0.0, 0.0, -0.005)),
        material=dark_steel,
        name="top_plate",
    )

    model.articulation(
        "sleeve_to_post",
        ArticulationType.PRISMATIC,
        parent=outer_sleeve,
        child=inner_post,
        origin=Origin(xyz=(0.0, 0.0, OUTER_TOP_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=250.0, velocity=0.18, lower=0.0, upper=POST_TRAVEL),
    )

    cap = model.part("cap")
    cap.visual(
        Box((0.300, 0.300, 0.016)),
        # The child frame is the hinge pin axis; in the closed pose the plate
        # extends along +X from that pin and rests on the sleeve rim.
        origin=Origin(xyz=(0.150, 0.0, -0.010)),
        material=galvanized,
        name="cap_plate",
    )
    dome_mesh = DomeGeometry(0.105, radial_segments=40, height_segments=10, closed=True)
    dome_mesh.scale(1.0, 1.0, 0.24)
    dome_mesh.translate(0.150, 0.0, -0.002)
    cap.visual(
        mesh_from_geometry(dome_mesh, "raised_dome_cap"),
        material=galvanized,
        name="dome",
    )
    cap.visual(
        Cylinder(radius=0.012, length=0.220),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_steel,
        name="hinge_barrel",
    )
    cap.visual(
        Cylinder(radius=0.006, length=0.240),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=rubber,
        name="hinge_pin",
    )

    model.articulation(
        "post_to_cap",
        ArticulationType.REVOLUTE,
        parent=inner_post,
        child=cap,
        origin=Origin(xyz=(HINGE_X, 0.0, HINGE_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=1.6, lower=0.0, upper=1.55),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
