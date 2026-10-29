# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_flash, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_flash

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

def _scale_shape(shape, s):
    """Honor unit_scale (e.g. models authored in mm, exported to meters with
    unit_scale=0.001): uniformly scale the B-rep about the origin."""
    if not s or s == 1.0 or shape is None:
        return shape
    try:
        return shape.transformGeometry(cq.Matrix([[s, 0, 0, 0], [0, s, 0, 0], [0, 0, s, 0]]))
    except Exception:
        return shape

def mesh_from_cadquery(model, name=None, **kwargs):
    return _CQMesh(_scale_shape(_to_shape(model), kwargs.get("unit_scale", 1.0)),
                   name=name if isinstance(name, str) else None)

def mesh_from_geometry(geometry, name=None, **kwargs):
    return _CQMesh(_scale_shape(_to_shape(geometry), kwargs.get("unit_scale", 1.0)),
                   name=name if isinstance(name, str) else None)

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
        self._raw_verts = [tuple(v) for v in (vertices or [])]
        self._raw_faces = [tuple(f) for f in (faces or [])]
        self._shape = None
        self._tess = None

    # subclasses call this with their cadquery shape
    def _set(self, shape):
        self._shape = _to_shape(shape) if not isinstance(shape, cq.Shape) else shape
        self._tess = None
        return self

    def _tessellate(self):
        """Triangle mesh (vertices, faces) of the B-rep — some model scripts read
        .vertices/.faces to manipulate raw geometry (e.g. axis swaps)."""
        if self._tess is None:
            if self._shape is None:
                self._tess = (list(self._raw_verts), list(self._raw_faces))
            else:
                try:
                    vs, ts = self._shape.tessellate(0.0005)
                    self._tess = ([(v.x, v.y, v.z) for v in vs],
                                  [tuple(int(i) for i in t) for t in ts])
                except Exception:
                    self._tess = (list(self._raw_verts), list(self._raw_faces))
        return self._tess

    @property
    def vertices(self):
        return self._raw_verts if self._raw_verts else self._tessellate()[0]

    @vertices.setter
    def vertices(self, v):
        # capture the B-rep's faces first so a vertices-ONLY reassignment
        # (read mesh -> transform verts -> assign back) doesn't lose the faces
        if self._shape is not None and not self._raw_faces:
            self._raw_faces = list(self._tessellate()[1])
        self._raw_verts = [tuple(x) for x in (v or [])]
        self._shape = None; self._tess = None

    @property
    def faces(self):
        return self._raw_faces if self._raw_faces else self._tessellate()[1]

    @faces.setter
    def faces(self, f):
        if self._shape is not None and not self._raw_verts:
            self._raw_verts = list(self._tessellate()[0])
        self._raw_faces = [tuple(x) for x in (f or [])]
        self._shape = None; self._tess = None

    def _cq(self):
        if self._shape is not None:
            return self._shape
        return _solid_from_triangles(self._raw_verts, self._raw_faces)

    # ---- mesh-style authoring (raw triangle fallback path) ----
    def add_vertex(self, x, y, z):
        self._raw_verts.append((float(x), float(y), float(z)))
        self._shape = None; self._tess = None
        return len(self._raw_verts) - 1

    def add_face(self, a, b, c):
        self._raw_faces.append((int(a), int(b), int(c)))
        self._shape = None; self._tess = None

    def copy(self):
        g = MeshGeometry(self._raw_verts, self._raw_faces)
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
        if self._shape is None and not self._raw_verts:
            self._shape = o          # empty accumulator: adopt other's shape
        else:
            a = self._cq()
            try:
                fused = a.fuse(o)
                if fused is None or fused.wrapped is None or fused.wrapped.IsNull():
                    raise ValueError("null fuse result")
                self._shape = fused
            except Exception:
                # OCC fuse can fail/return null on many thin/degenerate parts
                # (e.g. a balloon whisk's wire loops) — fall back to a non-boolean
                # Compound, which is equivalent for surface sampling / rendering.
                self._shape = cq.Compound.makeCompound([a, o])
        self._tess = None
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

def _profile_points_3d(profile):
    points = [(float(x), float(y), float(z)) for (x, y, z) in profile]
    cleaned = []
    for pt in points:
        if not cleaned or not (abs(cleaned[-1][0] - pt[0]) <= 1e-9 and abs(cleaned[-1][1] - pt[1]) <= 1e-9 and abs(cleaned[-1][2] - pt[2]) <= 1e-9):
            cleaned.append(pt)
    if len(cleaned) >= 2 and abs(cleaned[0][0] - cleaned[-1][0]) <= 1e-9 and abs(cleaned[0][1] - cleaned[-1][1]) <= 1e-9 and abs(cleaned[0][2] - cleaned[-1][2]) <= 1e-9:
        cleaned = cleaned[:-1]
    if len(cleaned) < 2:
        raise ValidationError("Profile must have at least 2 unique points")
    return cleaned

def rounded_rect_profile(width, height, radius, *, corner_segments=6):
    width = float(width); height = float(height); radius = float(radius)
    if width <= 0 or height <= 0:
        raise ValidationError("width/height must be positive")
    corner_segments = max(1, int(corner_segments))
    max_r = 0.5 * min(width, height)
    if radius < 0 or radius > max_r:
        raise ValidationError("radius must be within [0, %s]" % max_r)
    hw = width * 0.5; hh = height * 0.5
    if radius <= 1e-12:
        return [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    r = radius

    def arc(cx, cy, a0, a1):
        out = []
        for i in range(corner_segments + 1):
            t = i / corner_segments
            a = a0 + (a1 - a0) * t
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return out

    pts = []
    pts.extend(arc(hw - r, -hh + r, -math.pi / 2.0, 0.0))
    pts.extend(arc(hw - r, hh - r, 0.0, math.pi / 2.0)[1:])
    pts.extend(arc(-hw + r, hh - r, math.pi / 2.0, math.pi)[1:])
    pts.extend(arc(-hw + r, -hh + r, math.pi, 3.0 * math.pi / 2.0)[1:])
    return pts

# ===== lathe_extrude_loft (4 syms) =====
def _loft_side_faces(rings, closed):
    """Ruled side-wall faces between consecutive 3D rings (matched point counts).
    Each quad is split into two planar triangles, matching the sdk mesh exactly."""
    faces = []
    ring_count = len(rings[0])
    seg = ring_count if closed else ring_count - 1
    for i in range(len(rings) - 1):
        a_ring = rings[i]
        b_ring = rings[i + 1]
        for j in range(seg):
            j2 = (j + 1) % ring_count
            quad = (a_ring[j], a_ring[j2], b_ring[j2], b_ring[j])
            for tri in ((quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])):
                if (tri[0] == tri[1] or tri[1] == tri[2] or tri[2] == tri[0]):
                    continue
                try:
                    w = cq.Wire.makePolygon([cq.Vector(*p) for p in tri], close=True)
                    faces.append(cq.Face.makeFromWires(w))
                except Exception:
                    continue
    return faces

def _xy_area(ring):
    a = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        a += x1 * y2 - x2 * y1
    return a * 0.5

def _loft_solid(rings, *, cap, closed, ruled=True):
    """Loft through a list of 3D rings. cap+closed -> solid via makeLoft;
    otherwise an open side-wall shell. Rings are oriented consistently first."""
    rings = [list(r) for r in rings]
    if len(rings) < 2:
        raise ValidationError("Loft requires at least two profiles")
    base = _xy_area(rings[0])
    if abs(base) > 1e-9:
        if base < 0:
            rings = [list(reversed(r)) for r in rings]
            base = -base
        for idx in range(len(rings)):
            if _xy_area(rings[idx]) * base < 0:
                rings[idx] = list(reversed(rings[idx]))
    if cap and closed:
        wires = [cq.Wire.makePolygon([cq.Vector(*p) for p in r], close=True) for r in rings]
        return cq.Solid.makeLoft(wires, ruled)
    faces = _loft_side_faces(rings, closed)
    if not faces:
        raise ValidationError("Loft produced no valid side faces")
    return cq.Shell.makeShell(faces)

class LoftGeometry(MeshGeometry):
    """Loft through a sequence of closed 3D profiles (each a list of (x,y,z))."""

    def __init__(self, profiles, *, cap=True, closed=True):
        super().__init__()
        profile_list = [_profile_points_3d(p) for p in profiles]
        if len(profile_list) < 2:
            raise ValidationError("Loft requires at least two profiles")

        ring_count = len(profile_list[0])
        if closed and ring_count < 3:
            raise ValidationError("Closed loft profiles must have at least 3 points")
        for profile in profile_list:
            if len(profile) != ring_count:
                raise ValidationError("Loft profiles must have the same point count")

        self._set(_loft_solid(profile_list, cap=cap, closed=closed))

# ===== model =====
import math
def _rounded_xy_section(width_x: float, width_y: float, z: float, radius: float):
    return [(x, y, z) for x, y in rounded_rect_profile(width_x, width_y, radius, corner_segments=8)]
def _rounded_profile_section(width_y: float, height_z: float, x: float, radius: float):
    return [(y, z, x) for y, z in rounded_rect_profile(width_y, height_z, radius, corner_segments=8)]
def _body_shell_mesh():
    return LoftGeometry(
        [
            _rounded_xy_section(0.043, 0.070, 0.012, 0.010),
            _rounded_xy_section(0.048, 0.074, 0.066, 0.012),
            _rounded_xy_section(0.042, 0.066, 0.120, 0.010),
        ],
        cap=True,
        closed=True,
    )
def _head_shell_mesh():
    raw = LoftGeometry(
        [
            _rounded_profile_section(0.052, 0.040, -0.014, 0.008),
            _rounded_profile_section(0.060, 0.046, 0.032, 0.010),
            _rounded_profile_section(0.056, 0.042, 0.083, 0.008),
        ],
        cap=True,
        closed=True,
    )
    mapped = MeshGeometry()
    for y, z, x in raw.vertices:
        mapped.add_vertex(x, y, z)
    for a, b, c in raw.faces:
        mapped.add_face(a, b, c)
    return mapped
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="professional_camera_flash")

    satin_black = model.material("satin_black", rgba=(0.025, 0.027, 0.030, 1.0))
    dark_plastic = model.material("dark_plastic", rgba=(0.055, 0.058, 0.064, 1.0))
    rubber = model.material("button_rubber", rgba=(0.090, 0.092, 0.098, 1.0))
    panel_black = model.material("panel_black", rgba=(0.010, 0.012, 0.014, 1.0))
    screen_glass = model.material("screen_glass", rgba=(0.10, 0.18, 0.20, 0.75))
    diffuser = model.material("diffuser", rgba=(0.92, 0.90, 0.78, 0.65))
    metal = model.material("brushed_metal", rgba=(0.62, 0.64, 0.66, 1.0))
    label_grey = model.material("label_grey", rgba=(0.42, 0.43, 0.45, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_geometry(_body_shell_mesh(), "flash_body_shell"),
        material=satin_black,
        name="body_shell",
    )
    body.visual(
        Box((0.060, 0.088, 0.012)),
        origin=Origin(xyz=(0.000, 0.000, 0.006)),
        material=dark_plastic,
        name="mount_foot_plate",
    )
    body.visual(
        Box((0.068, 0.012, 0.005)),
        origin=Origin(xyz=(0.000, 0.036, 0.0025)),
        material=metal,
        name="mount_rail_0",
    )
    body.visual(
        Box((0.068, 0.012, 0.005)),
        origin=Origin(xyz=(0.000, -0.036, 0.0025)),
        material=metal,
        name="mount_rail_1",
    )
    body.visual(
        Box((0.036, 0.036, 0.0025)),
        origin=Origin(xyz=(0.000, 0.000, -0.00125)),
        material=metal,
        name="hotshoe_contact",
    )
    body.visual(
        Box((0.0030, 0.056, 0.094)),
        origin=Origin(xyz=(-0.0238, 0.000, 0.075)),
        material=panel_black,
        name="rear_panel",
    )
    body.visual(
        Box((0.0010, 0.029, 0.020)),
        origin=Origin(xyz=(-0.0274, 0.000, 0.090)),
        material=screen_glass,
        name="screen",
    )
    body.visual(
        Box((0.0018, 0.034, 0.025)),
        origin=Origin(xyz=(-0.0262, 0.000, 0.090)),
        material=label_grey,
        name="screen_bezel",
    )
    body.visual(
        Cylinder(radius=0.026, length=0.006),
        origin=Origin(xyz=(0.000, 0.000, 0.123)),
        material=dark_plastic,
        name="swivel_socket",
    )

    yoke = model.part("yoke")
    yoke.visual(
        Cylinder(radius=0.025, length=0.010),
        origin=Origin(xyz=(0.000, 0.000, 0.005)),
        material=dark_plastic,
        name="swivel_disc",
    )
    yoke.visual(
        Cylinder(radius=0.015, length=0.020),
        origin=Origin(xyz=(0.000, 0.000, 0.020)),
        material=dark_plastic,
        name="swivel_neck",
    )
    yoke.visual(
        Box((0.038, 0.090, 0.014)),
        origin=Origin(xyz=(0.024, 0.000, 0.026)),
        material=dark_plastic,
        name="yoke_bridge",
    )
    for side_index, side_y in enumerate((-0.040, 0.040)):
        yoke.visual(
            Box((0.020, 0.008, 0.075)),
            origin=Origin(xyz=(0.034, side_y, 0.055)),
            material=dark_plastic,
            name=f"yoke_arm_{side_index}",
        )
        yoke.visual(
            Cylinder(radius=0.011, length=0.005),
            origin=Origin(
                xyz=(0.036, side_y + (0.006 if side_y > 0 else -0.006), 0.055),
                rpy=(math.pi / 2.0, 0.0, 0.0),
            ),
            material=metal,
            name=f"axis_boss_{side_index}",
        )

    head = model.part("head")
    head.visual(
        mesh_from_geometry(_head_shell_mesh(), "flash_head_shell"),
        material=satin_black,
        name="head_shell",
    )
    head.visual(
        Box((0.004, 0.052, 0.036)),
        origin=Origin(xyz=(0.0845, 0.000, 0.000)),
        material=diffuser,
        name="front_diffuser",
    )
    head.visual(
        Box((0.002, 0.050, 0.032)),
        origin=Origin(xyz=(0.0875, 0.000, 0.000)),
        material=diffuser,
        name="fresnel_face",
    )
    head.visual(
        Cylinder(radius=0.0055, length=0.072),
        origin=Origin(xyz=(0.000, 0.000, 0.000), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=metal,
        name="tilt_axle",
    )
    for side_index, side_y in enumerate((-0.0340, 0.0340)):
        head.visual(
            Cylinder(radius=0.009, length=0.004),
            origin=Origin(xyz=(0.000, side_y, 0.000), rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=metal,
            name=f"trunnion_cap_{side_index}",
        )

    model.articulation(
        "body_to_yoke",
        ArticulationType.REVOLUTE,
        parent=body,
        child=yoke,
        origin=Origin(xyz=(0.000, 0.000, 0.126)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=4.0, velocity=2.4, lower=-math.pi, upper=math.pi),
    )
    model.articulation(
        "yoke_to_head",
        ArticulationType.REVOLUTE,
        parent=yoke,
        child=head,
        origin=Origin(xyz=(0.036, 0.000, 0.055)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=3.0, velocity=2.0, lower=-0.25, upper=1.35),
    )

    button_positions = [
        (0.000, 0.116, 0.006, 0.014, 0.008),
        (0.000, 0.064, 0.006, 0.014, 0.008),
        (-0.023, 0.090, 0.006, 0.010, 0.012),
        (0.023, 0.090, 0.006, 0.010, 0.012),
        (-0.018, 0.048, 0.006, 0.013, 0.008),
        (0.018, 0.048, 0.006, 0.013, 0.008),
        (-0.016, 0.030, 0.006, 0.012, 0.007),
        (0.016, 0.030, 0.006, 0.012, 0.007),
    ]
    for index, (local_y, local_z, _thick_x, size_y, size_z) in enumerate(button_positions):
        button = model.part(f"button_{index}")
        button.visual(
            Box((0.0030, size_y, size_z)),
            origin=Origin(xyz=(-0.0015, 0.000, 0.000)),
            material=rubber,
            name="button_cap",
        )
        button.visual(
            Box((0.0010, size_y * 0.55, size_z * 0.35)),
            origin=Origin(xyz=(-0.0035, 0.000, 0.000)),
            material=label_grey,
            name="button_mark",
        )
        model.articulation(
            f"body_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(xyz=(-0.0253, local_y, local_z)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=0.6, velocity=0.06, lower=0.0, upper=0.0025),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
