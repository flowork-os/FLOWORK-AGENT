# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bicycle_dropper_seatpost_assembly, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bicycle_dropper_seatpost_assembly

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

# ===== model =====
import math
import cadquery as cq
def _tube_mesh(
    outer_radius: float,
    inner_radius: float,
    length: float,
    name: str,
):
    """Simple hollow tube, authored from z=0 to z=length."""
    shape = cq.Workplane("XY").circle(outer_radius).circle(inner_radius).extrude(length)
    return mesh_from_cadquery(shape, name, tolerance=0.00045, angular_tolerance=0.08)
def _ring_shape(outer_radius: float, inner_radius: float, length: float, z_bottom: float):
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length)
        .translate((0.0, 0.0, z_bottom))
    )
def _boot_mesh(name: str):
    """Corrugated rubber bellows that clears the sliding stanchion."""
    inner_radius = 0.0134
    boot = _ring_shape(0.0156, inner_radius, 0.064, 0.0)
    # Raised ribs give the soft boot a believable accordion profile while the
    # thin inner sleeve keeps all ribs connected as one physical rubber part.
    for z in (0.004, 0.016, 0.028, 0.040, 0.052):
        boot = boot.union(_ring_shape(0.0183, inner_radius, 0.007, z))
    boot = boot.union(_ring_shape(0.0192, inner_radius, 0.009, -0.001))
    boot = boot.union(_ring_shape(0.0172, inner_radius, 0.008, 0.057))
    return mesh_from_cadquery(boot, name, tolerance=0.0005, angular_tolerance=0.08)
def _cylinder_between(part, start, end, radius, *, material: Material, name: str):
    """Add a cylinder whose local +Z axis spans start -> end in part coordinates."""
    sx, sy, sz = start
    ex, ey, ez = end
    vx, vy, vz = ex - sx, ey - sy, ez - sz
    length = math.sqrt(vx * vx + vy * vy + vz * vz)
    if length <= 0.0:
        raise ValueError("cylinder endpoints must be distinct")
    ux, uy, uz = vx / length, vy / length, vz / length
    yaw = math.atan2(uy, ux)
    pitch = math.atan2(math.sqrt(ux * ux + uy * uy), uz)
    part.visual(
        Cylinder(radius=radius, length=length),
        origin=Origin(
            xyz=((sx + ex) * 0.5, (sy + ey) * 0.5, (sz + ez) * 0.5),
            rpy=(0.0, pitch, yaw),
        ),
        material=material,
        name=name,
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="external_cable_dropper_seatpost")

    matte_black = model.material("matte_black", rgba=(0.015, 0.017, 0.018, 1.0))
    satin_black = model.material("satin_black", rgba=(0.03, 0.033, 0.035, 1.0))
    rubber = model.material("soft_black_rubber", rgba=(0.004, 0.004, 0.004, 1.0))
    stanchion = model.material("brushed_stanchion", rgba=(0.62, 0.64, 0.62, 1.0))
    bronze = model.material("bronze_bushing", rgba=(0.72, 0.48, 0.18, 1.0))
    steel = model.material("stainless_bolts", rgba=(0.72, 0.72, 0.69, 1.0))
    label = model.material("muted_gray_label", rgba=(0.25, 0.27, 0.27, 1.0))

    outer = model.part("outer_sleeve")
    outer.visual(
        _tube_mesh(0.0155, 0.0136, 0.300, "outer_post_sleeve"),
        material=matte_black,
        name="outer_tube",
    )
    outer.visual(
        _tube_mesh(0.0188, 0.0129, 0.027, "top_wiper_collar"),
        origin=Origin(xyz=(0.0, 0.0, 0.292)),
        material=satin_black,
        name="top_collar",
    )
    outer.visual(
        _tube_mesh(0.0147, 0.0118, 0.040, "linear_bushing"),
        origin=Origin(xyz=(0.0, 0.0, 0.270)),
        material=bronze,
        name="linear_bushing",
    )
    outer.visual(
        _boot_mesh("rubber_gap_boot"),
        origin=Origin(xyz=(0.0, 0.0, 0.314)),
        material=rubber,
        name="rubber_boot",
    )
    outer.visual(
        Box((0.0020, 0.020, 0.085)),
        origin=Origin(xyz=(0.0159, 0.0, 0.160)),
        material=label,
        name="sleeve_logo_panel",
    )
    # Cable stop and lower guide clamp are integral to the fixed outer sleeve.
    outer.visual(
        Box((0.043, 0.013, 0.011)),
        origin=Origin(xyz=(0.037, 0.0, 0.176)),
        material=satin_black,
        name="cable_stop",
    )
    outer.visual(
        Box((0.043, 0.012, 0.009)),
        origin=Origin(xyz=(0.037, 0.0, 0.025)),
        material=satin_black,
        name="cable_guide",
    )
    _cylinder_between(
        outer,
        (0.056, 0.0, 0.028),
        (0.056, 0.0, 0.190),
        0.0033,
        material=rubber,
        name="cable_housing",
    )
    _cylinder_between(
        outer,
        (0.056, 0.0, 0.176),
        (0.032, 0.0, 0.118),
        0.0013,
        material=steel,
        name="exposed_cable",
    )
    # Two yoke tabs around the lever hub, plus a bridge that visibly grows out
    # of the lower sleeve wall.
    outer.visual(
        Box((0.014, 0.005, 0.036)),
        origin=Origin(xyz=(0.027, 0.0115, 0.105)),
        material=satin_black,
        name="pivot_tab_0",
    )
    outer.visual(
        Box((0.014, 0.005, 0.036)),
        origin=Origin(xyz=(0.027, -0.0115, 0.105)),
        material=satin_black,
        name="pivot_tab_1",
    )
    outer.visual(
        Box((0.013, 0.026, 0.006)),
        origin=Origin(xyz=(0.0205, 0.0, 0.119)),
        material=satin_black,
        name="pivot_bridge",
    )

    inner = model.part("inner_post")
    inner.visual(
        Cylinder(radius=0.0120, length=0.450),
        # The child frame is at the sleeve entry.  The post extends below it so
        # it remains retained inside the bushing at full travel.
        origin=Origin(xyz=(0.0, 0.0, 0.095)),
        material=stanchion,
        name="inner_tube",
    )
    inner.visual(
        Cylinder(radius=0.0150, length=0.018),
        origin=Origin(xyz=(0.0, 0.0, 0.323)),
        material=satin_black,
        name="clamp_base_collar",
    )
    inner.visual(
        Box((0.036, 0.032, 0.020)),
        origin=Origin(xyz=(0.0, 0.0, 0.330)),
        material=satin_black,
        name="clamp_head",
    )
    inner.visual(
        Box((0.076, 0.046, 0.014)),
        origin=Origin(xyz=(0.0, 0.0, 0.345)),
        material=satin_black,
        name="lower_cradle",
    )
    # Saddle rails captured between the lower and upper cradles.
    for idx, y in enumerate((-0.014, 0.014)):
        inner.visual(
            Cylinder(radius=0.0035, length=0.090),
            origin=Origin(xyz=(0.0, y, 0.355), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=steel,
            name=f"saddle_rail_{idx}",
        )
    inner.visual(
        Box((0.074, 0.044, 0.008)),
        origin=Origin(xyz=(0.0, 0.0, 0.3625)),
        material=satin_black,
        name="upper_cradle",
    )
    for idx, x in enumerate((-0.025, 0.025)):
        inner.visual(
            Cylinder(radius=0.0030, length=0.038),
            origin=Origin(xyz=(x, 0.0, 0.354)),
            material=steel,
            name=f"clamp_bolt_{idx}",
        )
        inner.visual(
            Cylinder(radius=0.0054, length=0.0045),
            origin=Origin(xyz=(x, 0.0, 0.371)),
            material=steel,
            name=f"bolt_head_{idx}",
        )
        inner.visual(
            Cylinder(radius=0.0048, length=0.004),
            origin=Origin(xyz=(x, 0.0, 0.336)),
            material=steel,
            name=f"barrel_nut_{idx}",
        )

    lever = model.part("cable_lever")
    lever.visual(
        Cylinder(radius=0.0060, length=0.014),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=steel,
        name="lever_hub",
    )
    _cylinder_between(
        lever,
        (0.004, 0.0, -0.004),
        (0.017, 0.0, -0.056),
        0.0030,
        material=satin_black,
        name="lever_blade",
    )
    lever.visual(
        Sphere(radius=0.0048),
        origin=Origin(xyz=(0.018, 0.0, -0.058)),
        material=steel,
        name="cable_anchor",
    )
    _cylinder_between(
        lever,
        (0.017, 0.0, -0.055),
        (0.025, 0.0, -0.083),
        0.0012,
        material=steel,
        name="cable_tail",
    )

    model.articulation(
        "sleeve_to_post",
        ArticulationType.PRISMATIC,
        parent=outer,
        child=inner,
        origin=Origin(xyz=(0.0, 0.0, 0.300)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=180.0, velocity=0.25, lower=0.0, upper=0.100),
    )
    model.articulation(
        "sleeve_to_lever",
        ArticulationType.REVOLUTE,
        parent=outer,
        child=lever,
        origin=Origin(xyz=(0.027, 0.0, 0.105)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=4.0, lower=0.0, upper=0.65),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
