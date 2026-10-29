# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, branching_tree_with_three_independent_rotary_branches, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: branching_tree_with_three_independent_rotary_branches

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

# ===== model =====
import math
import cadquery as cq
def _mat(model: ArticulatedObject, name: str, rgba) -> Material:
    return model.material(name, rgba=rgba)
def _annular_bearing(outer_radius: float, inner_radius: float, length: float, name: str):
    """Centered hard-surface bearing race with a true through bore."""
    body = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length)
        .translate((0.0, 0.0, -length / 2.0))
    )
    # Eight small axial bolt counterbores give the housing a machined flange
    # reading without needing separate floating screw geometry.
    for i in range(8):
        a = i * math.tau / 8.0
        x = math.cos(a) * (outer_radius * 0.72)
        y = math.sin(a) * (outer_radius * 0.72)
        cutter = cq.Workplane("XY").center(x, y).circle(0.005).extrude(length * 1.4).translate(
            (0.0, 0.0, -length * 0.7)
        )
        body = body.cut(cutter)
    return mesh_from_cadquery(body, name, tolerance=0.0008, angular_tolerance=0.08)
def _spoked_rotor(radius: float, bore_radius: float, thickness: float, name: str):
    """One-piece rotating flange with lightening pockets and a central bore."""
    body = (
        cq.Workplane("XY")
        .circle(radius)
        .circle(bore_radius)
        .extrude(thickness)
        .translate((0.0, 0.0, -thickness / 2.0))
    )
    for i in range(6):
        a = i * math.tau / 6.0
        pocket = (
            cq.Workplane("XY")
            .center(math.cos(a) * radius * 0.48, math.sin(a) * radius * 0.48)
            .rect(radius * 0.36, radius * 0.13)
            .extrude(thickness * 1.4)
            .translate((0.0, 0.0, -thickness * 0.7))
            .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), math.degrees(a))
        )
        body = body.cut(pocket)
    return mesh_from_cadquery(body, name, tolerance=0.0008, angular_tolerance=0.08)
def _rod_between(part, name: str, start, end, radius: float, material):
    sx, sy, sz = start
    ex, ey, ez = end
    dx, dy, dz = ex - sx, ey - sy, ez - sz
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    ux, uy, uz = dx / length, dy / length, dz / length
    pitch = math.acos(max(-1.0, min(1.0, uz)))
    yaw = math.atan2(uy, ux)
    part.visual(
        Cylinder(radius=radius, length=length),
        origin=Origin(
            xyz=((sx + ex) / 2.0, (sy + ey) / 2.0, (sz + ez) / 2.0),
            rpy=(0.0, pitch, yaw),
        ),
        material=material,
        name=name,
    )
def _box(part, name: str, size, xyz, material, rpy=(0.0, 0.0, 0.0)):
    part.visual(Box(size), origin=Origin(xyz=xyz, rpy=rpy), material=material, name=name)
def _cylinder(part, name: str, radius: float, length: float, xyz, material, rpy=(0.0, 0.0, 0.0)):
    part.visual(
        Cylinder(radius=radius, length=length),
        origin=Origin(xyz=xyz, rpy=rpy),
        material=material,
        name=name,
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="rotary_branching_tree_study")

    dark_steel = _mat(model, "dark_blasted_steel", (0.12, 0.13, 0.13, 1.0))
    gunmetal = _mat(model, "gunmetal_casting", (0.23, 0.25, 0.25, 1.0))
    machined = _mat(model, "machined_bearing_steel", (0.58, 0.60, 0.58, 1.0))
    cover_mat = _mat(model, "removable_blackened_cover", (0.06, 0.065, 0.07, 1.0))
    stop_mat = _mat(model, "oxide_limit_stop", (0.42, 0.30, 0.13, 1.0))
    arm_mat = _mat(model, "satin_rigid_arm", (0.34, 0.38, 0.40, 1.0))
    fastener_mat = _mat(model, "dark_socket_fasteners", (0.03, 0.035, 0.04, 1.0))

    backbone = model.part("backbone")

    # Central fabricated spine and base: one root part with a visibly triangulated,
    # serviceable mechanical structure rather than a decorative enclosure.
    _box(backbone, "spine_tube", (0.12, 0.10, 1.22), (0.0, 0.0, 0.61), gunmetal)
    _box(backbone, "base_plate", (0.50, 0.36, 0.035), (0.0, 0.0, 0.0175), dark_steel)
    _box(backbone, "base_cross_rib", (0.42, 0.055, 0.065), (0.0, 0.0, 0.07), gunmetal)
    _box(backbone, "base_long_rib", (0.055, 0.30, 0.065), (0.0, 0.0, 0.07), gunmetal)
    _box(backbone, "top_cap_rail_0", (0.24, 0.050, 0.025), (0.0, 0.068, 1.2325), dark_steel)
    _box(backbone, "top_cap_rail_1", (0.24, 0.050, 0.025), (0.0, -0.068, 1.2325), dark_steel)
    _box(backbone, "rear_access_cover", (0.085, 0.008, 0.34), (0.0, -0.054, 0.66), cover_mat)
    _box(backbone, "front_access_cover", (0.086, 0.008, 0.24), (0.0, 0.054, 0.29), cover_mat)

    # Fasteners are slightly proud and locally embedded into their removable covers
    # so they read as bolted-on panels while remaining one supported root part.
    for ix, x in enumerate((-0.030, 0.030)):
        for iz, z in enumerate((0.53, 0.79)):
            _cylinder(
                backbone,
                f"rear_cover_screw_{ix}_{iz}",
                0.006,
                0.006,
                (x, -0.058, z),
                fastener_mat,
                rpy=(math.pi / 2.0, 0.0, 0.0),
            )
    for ix, x in enumerate((-0.030, 0.030)):
        for iz, z in enumerate((0.20, 0.38)):
            _cylinder(
                backbone,
                f"front_cover_screw_{ix}_{iz}",
                0.0055,
                0.006,
                (x, 0.058, z),
                fastener_mat,
                rpy=(math.pi / 2.0, 0.0, 0.0),
            )

    # Three offset bearing stations are connected by real brackets and a diagonal
    # tube backbone.  Their axes are deliberately separated: Z, Y, and X.
    upper_origin = (0.0, 0.0, 1.26)
    middle_origin = (0.0, 0.155, 0.76)
    lower_origin = (-0.155, 0.0, 0.38)

    # Upper horizontal bearing stack.
    backbone.visual(
        _annular_bearing(0.095, 0.034, 0.060, "upper_bearing_race"),
        origin=Origin(xyz=upper_origin),
        material=machined,
        name="upper_bearing_race",
    )
    _box(backbone, "upper_bridge_plate", (0.22, 0.16, 0.030), (0.0, 0.0, 1.205), dark_steel)
    _box(backbone, "upper_yoke_web", (0.055, 0.155, 0.105), (0.0, 0.0, 1.165), gunmetal)
    _box(backbone, "upper_stop_plus", (0.024, 0.026, 0.035), (0.030, 0.088, 1.305), stop_mat)
    _box(backbone, "upper_stop_minus", (0.024, 0.026, 0.035), (-0.030, 0.088, 1.305), stop_mat)

    # Middle front bearing, axis along world Y.
    backbone.visual(
        _annular_bearing(0.083, 0.031, 0.070, "middle_bearing_race"),
        origin=Origin(xyz=middle_origin, rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=machined,
        name="middle_bearing_race",
    )
    _box(backbone, "middle_side_cheek_0", (0.035, 0.120, 0.070), (0.055, 0.087, 0.76), dark_steel)
    _box(backbone, "middle_side_cheek_1", (0.035, 0.120, 0.070), (-0.055, 0.087, 0.76), dark_steel)
    _box(backbone, "middle_top_web", (0.10, 0.125, 0.030), (0.0, 0.087, 0.83), gunmetal)
    _box(backbone, "middle_bottom_web", (0.10, 0.125, 0.030), (0.0, 0.087, 0.69), gunmetal)
    _box(backbone, "middle_stop_top", (0.052, 0.026, 0.020), (0.055, 0.192, 0.823), stop_mat)
    _box(backbone, "middle_stop_bottom", (0.052, 0.026, 0.020), (0.055, 0.192, 0.697), stop_mat)

    # Lower side bearing, axis along world X.
    backbone.visual(
        _annular_bearing(0.078, 0.029, 0.070, "lower_bearing_race"),
        origin=Origin(xyz=lower_origin, rpy=(0.0, math.pi / 2.0, 0.0)),
        material=machined,
        name="lower_bearing_race",
    )
    _box(backbone, "lower_upper_saddle", (0.125, 0.13, 0.022), (-0.087, 0.0, 0.424), dark_steel)
    _box(backbone, "lower_lower_saddle", (0.125, 0.13, 0.022), (-0.087, 0.0, 0.336), dark_steel)
    _box(backbone, "lower_front_web", (0.125, 0.030, 0.095), (-0.087, 0.055, 0.38), gunmetal)
    _box(backbone, "lower_rear_web", (0.125, 0.030, 0.095), (-0.087, -0.055, 0.38), gunmetal)
    _box(backbone, "lower_stop_front", (0.025, 0.048, 0.022), (-0.165, 0.060, 0.425), stop_mat)
    _box(backbone, "lower_stop_rear", (0.025, 0.048, 0.022), (-0.165, -0.030, 0.425), stop_mat)

    # Triangulated external spine rods tie the bearing stations and base into
    # a clear load path.  The small overlaps at their endpoints are same-part
    # welded/sleeved joints.
    _rod_between(backbone, "front_upper_diag", (0.052, 0.060, 0.16), (0.052, 0.060, 1.17), 0.010, dark_steel)
    _rod_between(backbone, "rear_upper_diag", (-0.052, -0.060, 0.16), (-0.052, -0.060, 1.17), 0.010, dark_steel)
    _rod_between(backbone, "front_cross_diag", (-0.055, 0.060, 0.20), (0.055, 0.060, 1.08), 0.008, dark_steel)
    _rod_between(backbone, "rear_cross_diag", (0.055, -0.060, 0.20), (-0.055, -0.060, 1.08), 0.008, dark_steel)
    _rod_between(backbone, "middle_to_upper_tie", (0.045, 0.13, 0.81), (0.070, 0.04, 1.22), 0.007, dark_steel)
    _rod_between(backbone, "lower_to_middle_tie", (-0.13, 0.045, 0.43), (-0.030, 0.135, 0.72), 0.007, dark_steel)

    # Upper branch rotates in a horizontal envelope about the vertical bearing.
    upper_branch = model.part("upper_branch")
    _cylinder(upper_branch, "upper_shaft", 0.026, 0.088, (0.0, 0.0, 0.0), machined)
    upper_branch.visual(
        _spoked_rotor(0.069, 0.017, 0.020, "upper_rotor_flange"),
        origin=Origin(xyz=(0.0, 0.0, 0.054)),
        material=machined,
        name="upper_rotor_flange",
    )
    _box(upper_branch, "upper_arm_box", (0.62, 0.062, 0.045), (0.36, 0.0, 0.074), arm_mat)
    _box(upper_branch, "upper_arm_cap", (0.16, 0.088, 0.016), (0.69, 0.0, 0.074), cover_mat)
    _box(upper_branch, "upper_top_gusset", (0.23, 0.020, 0.082), (0.16, 0.041, 0.078), dark_steel)
    _box(upper_branch, "upper_bottom_gusset", (0.23, 0.020, 0.082), (0.16, -0.041, 0.078), dark_steel)
    _box(upper_branch, "upper_end_pad", (0.034, 0.085, 0.070), (0.69, 0.0, 0.074), gunmetal)
    for i, x in enumerate((0.14, 0.28, 0.50, 0.64)):
        _cylinder(upper_branch, f"upper_cap_screw_{i}", 0.0048, 0.010, (x, 0.0, 0.0865), fastener_mat)

    # Middle branch: independent pitch-like rotary axis, offset forward of the spine.
    middle_branch = model.part("middle_branch")
    _cylinder(
        middle_branch,
        "middle_shaft",
        0.024,
        0.100,
        (0.0, 0.0, 0.0),
        machined,
        rpy=(-math.pi / 2.0, 0.0, 0.0),
    )
    middle_branch.visual(
        _spoked_rotor(0.062, 0.016, 0.018, "middle_rotor_flange"),
        origin=Origin(xyz=(0.0, 0.056, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=machined,
        name="middle_rotor_flange",
    )
    _box(middle_branch, "middle_arm_box", (0.58, 0.050, 0.055), (0.34, 0.078, 0.0), arm_mat)
    _box(middle_branch, "middle_top_plate", (0.25, 0.018, 0.085), (0.17, 0.083, 0.045), dark_steel)
    _box(middle_branch, "middle_bottom_plate", (0.25, 0.018, 0.085), (0.17, 0.083, -0.045), dark_steel)
    _box(middle_branch, "middle_access_cover", (0.19, 0.010, 0.070), (0.47, 0.108, 0.0), cover_mat)
    _box(middle_branch, "middle_end_pad", (0.034, 0.078, 0.080), (0.64, 0.078, 0.0), gunmetal)
    for i, x in enumerate((0.42, 0.52)):
        for j, z in enumerate((-0.023, 0.023)):
            _cylinder(
                middle_branch,
                f"middle_cover_screw_{i}_{j}",
                0.0045,
                0.008,
                (x, 0.113, z),
                fastener_mat,
                rpy=(-math.pi / 2.0, 0.0, 0.0),
            )

    # Lower branch: separate side axis, with its own guide plates and stop window.
    lower_branch = model.part("lower_branch")
    _cylinder(
        lower_branch,
        "lower_shaft",
        0.023,
        0.096,
        (0.0, 0.0, 0.0),
        machined,
        rpy=(0.0, math.pi / 2.0, 0.0),
    )
    lower_branch.visual(
        _spoked_rotor(0.058, 0.015, 0.018, "lower_rotor_flange"),
        origin=Origin(xyz=(-0.044, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=machined,
        name="lower_rotor_flange",
    )
    _box(lower_branch, "lower_arm_box", (0.052, 0.50, 0.052), (-0.078, -0.305, 0.0), arm_mat)
    _box(lower_branch, "lower_side_plate_a", (0.084, 0.21, 0.016), (-0.083, -0.16, 0.028), dark_steel)
    _box(lower_branch, "lower_side_plate_b", (0.084, 0.21, 0.016), (-0.083, -0.16, -0.028), dark_steel)
    _box(lower_branch, "lower_access_cover", (0.012, 0.17, 0.064), (-0.108, -0.39, 0.0), cover_mat)
    _box(lower_branch, "lower_end_pad", (0.078, 0.034, 0.074), (-0.078, -0.570, 0.0), gunmetal)
    for i, y in enumerate((-0.34, -0.44)):
        for j, z in enumerate((-0.021, 0.021)):
            _cylinder(
                lower_branch,
                f"lower_cover_screw_{i}_{j}",
                0.0044,
                0.008,
                (-0.114, y, z),
                fastener_mat,
                rpy=(0.0, math.pi / 2.0, 0.0),
            )

    model.articulation(
        "upper_axis",
        ArticulationType.REVOLUTE,
        parent=backbone,
        child=upper_branch,
        origin=Origin(xyz=upper_origin),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=120.0, velocity=1.2, lower=-0.72, upper=0.72),
        motion_properties=MotionProperties(damping=0.8, friction=0.15),
    )
    model.articulation(
        "middle_axis",
        ArticulationType.REVOLUTE,
        parent=backbone,
        child=middle_branch,
        origin=Origin(xyz=middle_origin),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=95.0, velocity=1.0, lower=-0.58, upper=0.62),
        motion_properties=MotionProperties(damping=0.7, friction=0.12),
    )
    model.articulation(
        "lower_axis",
        ArticulationType.REVOLUTE,
        parent=backbone,
        child=lower_branch,
        origin=Origin(xyz=lower_origin),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=85.0, velocity=1.0, lower=-0.68, upper=0.55),
        motion_properties=MotionProperties(damping=0.7, friction=0.12),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
