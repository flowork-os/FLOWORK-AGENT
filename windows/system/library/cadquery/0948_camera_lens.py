# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_lens, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_lens

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
def _axisymmetric_solid(profile: list[tuple[float, float]], *, segments: int = 96) -> MeshGeometry:
    """Closed stepped body around the local X axis.  Profile entries are (x, radius)."""
    geom = MeshGeometry()
    rings: list[list[int]] = []
    for x, radius in profile:
        ring: list[int] = []
        for i in range(segments):
            theta = 2.0 * math.pi * i / segments
            ring.append(geom.add_vertex(x, radius * math.cos(theta), radius * math.sin(theta)))
        rings.append(ring)

    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            geom.add_face(a[i], b[i], b[j])
            geom.add_face(a[i], b[j], a[j])

    # Cap the rear and front so the alloy barrel reads as a manufactured shell/skin.
    rear_center = geom.add_vertex(profile[0][0], 0.0, 0.0)
    front_center = geom.add_vertex(profile[-1][0], 0.0, 0.0)
    rear = rings[0]
    front = rings[-1]
    for i in range(segments):
        j = (i + 1) % segments
        geom.add_face(rear_center, rear[j], rear[i])
        geom.add_face(front_center, front[i], front[j])
    return geom
def _hollow_ring(
    *,
    length: float,
    inner_radius: float,
    outer_radius: float,
    segments: int = 96,
    rib_count: int = 0,
    rib_depth: float = 0.0,
) -> MeshGeometry:
    """Closed annular ring around local X, optionally with axial rubber ribs."""
    geom = MeshGeometry()
    xs = (-length / 2.0, length / 2.0)
    outer: list[list[int]] = []
    inner: list[list[int]] = []

    for x in xs:
        outer_ring: list[int] = []
        inner_ring: list[int] = []
        for i in range(segments):
            theta = 2.0 * math.pi * i / segments
            if rib_count:
                # Rounded high ribs with shallow valleys; the periodic profile remains one mesh.
                rib_phase = 0.5 + 0.5 * math.cos(rib_count * theta)
                radius = outer_radius + rib_depth * (rib_phase**3)
            else:
                radius = outer_radius
            c = math.cos(theta)
            s = math.sin(theta)
            outer_ring.append(geom.add_vertex(x, radius * c, radius * s))
            inner_ring.append(geom.add_vertex(x, inner_radius * c, inner_radius * s))
        outer.append(outer_ring)
        inner.append(inner_ring)

    # Outer and inner cylindrical surfaces.
    for i in range(segments):
        j = (i + 1) % segments
        geom.add_face(outer[0][i], outer[1][i], outer[1][j])
        geom.add_face(outer[0][i], outer[1][j], outer[0][j])
        geom.add_face(inner[0][j], inner[1][j], inner[1][i])
        geom.add_face(inner[0][j], inner[1][i], inner[0][i])

    # Annular end faces.
    for side in range(2):
        for i in range(segments):
            j = (i + 1) % segments
            if side == 0:
                geom.add_face(inner[side][i], outer[side][i], outer[side][j])
                geom.add_face(inner[side][i], outer[side][j], inner[side][j])
            else:
                geom.add_face(inner[side][j], outer[side][j], outer[side][i])
                geom.add_face(inner[side][j], outer[side][i], inner[side][i])
    return geom
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="super_telephoto_prime_lens")

    alloy = model.material("warm_white_alloy", rgba=(0.86, 0.84, 0.78, 1.0))
    satin_black = model.material("satin_black", rgba=(0.01, 0.011, 0.012, 1.0))
    rubber = model.material("ribbed_black_rubber", rgba=(0.006, 0.006, 0.006, 1.0))
    dark_metal = model.material("dark_anodized_metal", rgba=(0.10, 0.105, 0.11, 1.0))
    brushed_steel = model.material("brushed_bayonet_steel", rgba=(0.62, 0.63, 0.62, 1.0))
    glass = model.material("coated_front_glass", rgba=(0.18, 0.32, 0.42, 0.55))
    white_paint = model.material("engraved_white_paint", rgba=(1.0, 1.0, 0.92, 1.0))

    barrel = model.part("barrel")
    barrel_profile = [
        (-0.430, 0.045),
        (-0.402, 0.052),
        (-0.360, 0.058),
        (-0.285, 0.064),
        (-0.120, 0.070),
        (-0.060, 0.072),
        (0.070, 0.072),
        (0.100, 0.067),
        (0.155, 0.069),
        (0.180, 0.076),
        (0.310, 0.076),
        (0.335, 0.070),
        (0.385, 0.085),
        (0.455, 0.092),
    ]
    barrel.visual(
        mesh_from_geometry(_axisymmetric_solid(barrel_profile), "barrel_shell"),
        material=alloy,
        name="barrel_shell",
    )
    barrel.visual(
        Cylinder(radius=0.087, length=0.022),
        origin=Origin(xyz=(0.461, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=satin_black,
        name="front_inner_rim",
    )
    barrel.visual(
        Cylinder(radius=0.073, length=0.007),
        origin=Origin(xyz=(0.474, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=glass,
        name="front_element",
    )
    barrel.visual(
        Cylinder(radius=0.050, length=0.030),
        origin=Origin(xyz=(-0.432, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=brushed_steel,
        name="rear_mount_plate",
    )
    for idx, theta in enumerate((0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0)):
        radial = 0.047
        barrel.visual(
            Box((0.011, 0.031, 0.010)),
            origin=Origin(
                xyz=(-0.452, -radial * math.sin(theta), radial * math.cos(theta)),
                rpy=(theta, 0.0, 0.0),
            ),
            material=brushed_steel,
            name=f"bayonet_lug_{idx}",
        )
    barrel.visual(
        Box((0.006, 0.045, 0.014)),
        origin=Origin(xyz=(-0.407, 0.0, 0.051)),
        material=dark_metal,
        name="rear_weather_gasket",
    )

    collar = model.part("collar")
    collar.visual(
        mesh_from_geometry(
            _hollow_ring(length=0.082, inner_radius=0.075, outer_radius=0.089, segments=96),
            "collar_ring",
        ),
        material=dark_metal,
        name="collar_ring",
    )
    for idx, theta in enumerate((0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0)):
        pad_radius = 0.0735
        collar.visual(
            Box((0.016, 0.008, 0.003)),
            origin=Origin(
                xyz=(0.0, -pad_radius * math.sin(theta), pad_radius * math.cos(theta)),
                rpy=(theta, 0.0, 0.0),
            ),
            material=dark_metal,
            name=f"collar_bearing_pad_{idx}",
        )
    collar.visual(
        Box((0.066, 0.044, 0.040)),
        origin=Origin(xyz=(0.0, 0.0, -0.109)),
        material=dark_metal,
        name="foot_stem",
    )
    collar.visual(
        Box((0.165, 0.072, 0.023)),
        origin=Origin(xyz=(0.006, 0.0, -0.139)),
        material=dark_metal,
        name="foot_plate",
    )
    collar.visual(
        Box((0.142, 0.046, 0.010)),
        origin=Origin(xyz=(0.006, 0.0, -0.153)),
        material=satin_black,
        name="dovetail_sole",
    )

    focus_ring = model.part("focus_ring")
    focus_ring.visual(
        mesh_from_geometry(
            _hollow_ring(
                length=0.132,
                inner_radius=0.081,
                outer_radius=0.090,
                segments=144,
                rib_count=36,
                rib_depth=0.006,
            ),
            "focus_shell",
        ),
        material=rubber,
        name="focus_shell",
    )
    for idx, theta in enumerate((math.pi / 4.0, 3.0 * math.pi / 4.0, 5.0 * math.pi / 4.0, 7.0 * math.pi / 4.0)):
        pad_radius = 0.0785
        focus_ring.visual(
            Box((0.020, 0.007, 0.005)),
            origin=Origin(
                xyz=(0.0, -pad_radius * math.sin(theta), pad_radius * math.cos(theta)),
                rpy=(theta, 0.0, 0.0),
            ),
            material=rubber,
            name=f"focus_bearing_pad_{idx}",
        )
    focus_ring.visual(
        Box((0.040, 0.005, 0.003)),
        origin=Origin(xyz=(0.000, 0.0, 0.096)),
        material=white_paint,
        name="focus_mark",
    )

    model.articulation(
        "barrel_to_collar",
        ArticulationType.CONTINUOUS,
        parent=barrel,
        child=collar,
        origin=Origin(xyz=(-0.020, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=2.5),
    )
    model.articulation(
        "barrel_to_focus",
        ArticulationType.REVOLUTE,
        parent=barrel,
        child=focus_ring,
        origin=Origin(xyz=(0.245, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=3.0, velocity=1.8, lower=-1.75, upper=1.75),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
