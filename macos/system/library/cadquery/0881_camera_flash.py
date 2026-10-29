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
def _rounded_box(size: tuple[float, float, float], radius: float) -> cq.Workplane:
    """A simple consumer-electronics rounded rectangle solid."""

    solid = cq.Workplane("XY").box(size[0], size[1], size[2])
    if radius > 0.0:
        solid = solid.edges("|Z").fillet(radius)
    return solid
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="compact_speedlight_flash")

    matte_black = model.material("matte_black", rgba=(0.012, 0.012, 0.014, 1.0))
    satin_black = model.material("satin_black", rgba=(0.045, 0.045, 0.050, 1.0))
    rubber = model.material("rubber_black", rgba=(0.010, 0.010, 0.012, 1.0))
    dark_panel = model.material("smoked_panel", rgba=(0.020, 0.024, 0.030, 1.0))
    button_mat = model.material("button_gray", rgba=(0.14, 0.15, 0.16, 1.0))
    button_blue = model.material("mode_blue", rgba=(0.05, 0.16, 0.34, 1.0))
    diffuser = model.material("frosted_diffuser", rgba=(0.78, 0.86, 0.92, 0.62))
    reflector = model.material("soft_reflector", rgba=(0.95, 0.96, 0.90, 0.82))
    metal = model.material("brushed_metal", rgba=(0.55, 0.55, 0.52, 1.0))

    body = model.part("body")

    lower_body = _rounded_box((0.078, 0.052, 0.090), 0.006).translate((0.0, 0.0, 0.053))
    upper_step = _rounded_box((0.064, 0.044, 0.040), 0.005).translate((0.0, 0.0, 0.113))
    top_plate = _rounded_box((0.054, 0.038, 0.012), 0.004).translate((0.0, 0.0, 0.138))
    body_shell = lower_body.union(upper_step).union(top_plate)
    body.visual(
        mesh_from_cadquery(body_shell, "body_shell", tolerance=0.0006),
        material=matte_black,
        name="body_shell",
    )

    # Stepped battery door and molded panel breaks on the front face.
    body.visual(
        Box((0.062, 0.0022, 0.055)),
        origin=Origin(xyz=(0.0, -0.0271, 0.046)),
        material=dark_panel,
        name="battery_door",
    )
    body.visual(
        Box((0.068, 0.0030, 0.0030)),
        origin=Origin(xyz=(0.0, -0.0268, 0.093)),
        material=satin_black,
        name="body_step_line",
    )
    body.visual(
        Box((0.030, 0.0030, 0.014)),
        origin=Origin(xyz=(0.0, -0.0222, 0.108)),
        material=dark_panel,
        name="ready_window",
    )

    # Right-side control strip: the individual buttons below are articulated
    # child parts whose inner faces rest on this raised rubberized strip.
    body.visual(
        Box((0.0050, 0.020, 0.070)),
        origin=Origin(xyz=(0.0415, 0.001, 0.065)),
        material=rubber,
        name="control_strip",
    )
    body.visual(
        Box((0.0052, 0.016, 0.011)),
        origin=Origin(xyz=(0.0418, 0.001, 0.105)),
        material=dark_panel,
        name="control_display",
    )

    # Hot-shoe and shoe lock stack under the body.
    body.visual(
        Box((0.030, 0.022, 0.010)),
        origin=Origin(xyz=(0.0, 0.0, 0.003)),
        material=matte_black,
        name="shoe_pedestal",
    )
    body.visual(
        Cylinder(radius=0.023, length=0.006),
        origin=Origin(xyz=(0.0, 0.0, 0.0005)),
        material=satin_black,
        name="lock_wheel",
    )
    body.visual(
        Cylinder(radius=0.0075, length=0.018),
        origin=Origin(xyz=(0.0, 0.0, -0.002)),
        material=metal,
        name="shoe_screw",
    )
    body.visual(
        Box((0.050, 0.034, 0.004)),
        origin=Origin(xyz=(0.0, 0.0, -0.011)),
        material=metal,
        name="shoe_plate",
    )
    body.visual(
        Box((0.008, 0.038, 0.006)),
        origin=Origin(xyz=(-0.025, 0.0, -0.010)),
        material=metal,
        name="shoe_rail_0",
    )
    body.visual(
        Box((0.008, 0.038, 0.006)),
        origin=Origin(xyz=(0.025, 0.0, -0.010)),
        material=metal,
        name="shoe_rail_1",
    )
    body.visual(
        Box((0.044, 0.004, 0.006)),
        origin=Origin(xyz=(0.0, -0.019, -0.010)),
        material=metal,
        name="shoe_stop",
    )

    swivel = model.part("swivel")
    swivel.visual(
        Cylinder(radius=0.024, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, 0.005)),
        material=satin_black,
        name="turntable",
    )
    swivel.visual(
        Box((0.040, 0.030, 0.014)),
        origin=Origin(xyz=(0.0, 0.0, 0.016)),
        material=satin_black,
        name="swivel_neck",
    )
    swivel.visual(
        Box((0.120, 0.018, 0.010)),
        origin=Origin(xyz=(0.0, 0.004, 0.018)),
        material=satin_black,
        name="yoke_bridge",
    )
    swivel.visual(
        Box((0.010, 0.020, 0.050)),
        origin=Origin(xyz=(-0.065, 0.0, 0.039)),
        material=satin_black,
        name="yoke_arm_0",
    )
    swivel.visual(
        Box((0.010, 0.020, 0.050)),
        origin=Origin(xyz=(0.065, 0.0, 0.039)),
        material=satin_black,
        name="yoke_arm_1",
    )

    head = model.part("head")
    head_shell = _rounded_box((0.100, 0.056, 0.048), 0.006)
    head.visual(
        mesh_from_cadquery(head_shell, "head_shell", tolerance=0.0006),
        origin=Origin(xyz=(0.0, -0.011, 0.003)),
        material=matte_black,
        name="head_shell",
    )
    head.visual(
        Box((0.084, 0.004, 0.034)),
        origin=Origin(xyz=(0.0, -0.041, 0.003)),
        material=diffuser,
        name="front_lens",
    )
    head.visual(
        Box((0.074, 0.002, 0.022)),
        origin=Origin(xyz=(0.0, -0.0432, 0.0025)),
        material=reflector,
        name="flash_tube_window",
    )
    head.visual(
        Box((0.094, 0.006, 0.005)),
        origin=Origin(xyz=(0.0, -0.042, 0.024)),
        material=satin_black,
        name="lens_top_bezel",
    )
    head.visual(
        Box((0.094, 0.006, 0.005)),
        origin=Origin(xyz=(0.0, -0.042, -0.018)),
        material=satin_black,
        name="lens_bottom_bezel",
    )
    head.visual(
        Box((0.005, 0.006, 0.040)),
        origin=Origin(xyz=(-0.045, -0.042, 0.003)),
        material=satin_black,
        name="lens_side_bezel_0",
    )
    head.visual(
        Box((0.005, 0.006, 0.040)),
        origin=Origin(xyz=(0.045, -0.042, 0.003)),
        material=satin_black,
        name="lens_side_bezel_1",
    )
    head.visual(
        Cylinder(radius=0.009, length=0.010),
        origin=Origin(xyz=(-0.055, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=metal,
        name="pivot_pin_0",
    )
    head.visual(
        Cylinder(radius=0.009, length=0.010),
        origin=Origin(xyz=(0.055, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=metal,
        name="pivot_pin_1",
    )

    model.articulation(
        "body_to_swivel",
        ArticulationType.REVOLUTE,
        parent=body,
        child=swivel,
        origin=Origin(xyz=(0.0, 0.0, 0.144)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=1.8, velocity=2.0, lower=-math.pi, upper=math.pi),
    )
    model.articulation(
        "swivel_to_head",
        ArticulationType.REVOLUTE,
        parent=swivel,
        child=head,
        origin=Origin(xyz=(0.0, 0.0, 0.045)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=1.5, velocity=1.6, lower=-0.15, upper=1.55),
    )

    # Four separate prismatic mode buttons on the side strip.  Positive travel
    # moves inward along -X, as a real push button would compress into the body.
    button_positions = [
        ("mode_button_0", 0.084, button_blue),
        ("mode_button_1", 0.068, button_mat),
        ("mode_button_2", 0.052, button_mat),
        ("mode_button_3", 0.036, button_mat),
    ]
    for name, z_pos, material in button_positions:
        button = model.part(name)
        button.visual(
            Box((0.006, 0.014, 0.010)),
            origin=Origin(),
            material=material,
            name="cap",
        )
        model.articulation(
            f"body_to_{name}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(xyz=(0.047, 0.001, z_pos)),
            axis=(-1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=0.6, velocity=0.08, lower=0.0, upper=0.004),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
