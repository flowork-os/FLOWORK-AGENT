# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_pump_with_t_handle, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_pump_with_t_handle

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
import cadquery as cq
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="service_station_pump")

    base_mat = model.material("base_dark", color=(0.20, 0.20, 0.22, 1.0))
    steel_mat = model.material("steel", color=(0.72, 0.74, 0.76, 1.0))
    gauge_mat = model.material("gauge_dark", color=(0.13, 0.14, 0.15, 1.0))
    grip_mat = model.material("grip_black", color=(0.10, 0.10, 0.10, 1.0))
    knob_mat = model.material("selector_red", color=(0.70, 0.12, 0.08, 1.0))

    base_height = 0.050
    base_pedestal_height = 0.032
    barrel_height = 0.720
    barrel_outer_r = 0.040
    barrel_inner_r = 0.033
    rod_radius = 0.010
    rod_hidden = 0.470
    rod_exposed = 0.235
    plunger_travel = 0.260
    gauge_mount_z = 0.430

    base_shape = (
        cq.Workplane("XY")
        .box(0.340, 0.220, base_height, centered=(True, True, False))
        .faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .circle(0.055)
        .extrude(base_pedestal_height)
    )

    barrel_body = cq.Workplane("XY").cylinder(barrel_height, barrel_outer_r, centered=(True, True, False))
    barrel_bore = cq.Workplane("XY").cylinder(
        barrel_height - 0.010,
        barrel_inner_r,
        centered=(True, True, False),
    ).translate((0.0, 0.0, 0.010))
    top_gland = (
        cq.Workplane("XY")
        .cylinder(0.032, barrel_outer_r + 0.007, centered=(True, True, False))
        .translate((0.0, 0.0, barrel_height - 0.016))
    )
    top_gland_hole = (
        cq.Workplane("XY")
        .cylinder(0.038, rod_radius + 0.0025, centered=(True, True, False))
        .translate((0.0, 0.0, barrel_height - 0.019))
    )
    barrel_shape = (
        barrel_body.cut(barrel_bore)
        .union(top_gland)
        .cut(top_gland_hole)
    )

    gauge_case_depth = 0.046
    gauge_case_back_y = barrel_outer_r + 0.039
    gauge_case_front_y = gauge_case_back_y + gauge_case_depth
    clamp_outer_r = barrel_outer_r + 0.012
    clamp_inner_r = barrel_outer_r - 0.001
    clamp_band = (
        cq.Workplane("XY")
        .circle(clamp_outer_r)
        .circle(clamp_inner_r)
        .extrude(0.058, both=True)
        .cut(
            cq.Workplane("XY")
            .box(0.180, 0.094, 0.180, centered=True)
            .translate((0.0, -0.047, 0.0))
        )
    )
    gauge_arm = (
        cq.Workplane("XY")
        .box(0.044, 0.036, 0.120, centered=True)
        .translate((0.0, clamp_outer_r + 0.018, 0.0))
    )
    gauge_case = (
        cq.Workplane("XY")
        .box(0.110, gauge_case_depth, 0.150, centered=True)
        .edges("|Z")
        .fillet(0.010)
        .faces(">Y")
        .workplane(centerOption="CenterOfMass")
        .circle(0.038)
        .cutBlind(-0.004)
        .translate((0.0, gauge_case_back_y + gauge_case_depth / 2.0, 0.0))
    )
    selector_boss = (
        cq.Workplane("XZ")
        .circle(0.012)
        .extrude(0.006)
        .translate((0.032, gauge_case_front_y, -0.038))
    )
    gauge_shape = clamp_band.union(gauge_arm).union(gauge_case).union(selector_boss)

    plunger_top_collar = cq.Workplane("XY").circle(0.021).extrude(0.010)
    handle_shape = cq.Workplane("XY").circle(0.014).extrude(0.064).translate((0.0, 0.0, rod_exposed - 0.006))
    handle_crossbar = (
        cq.Workplane("YZ")
        .circle(0.012)
        .extrude(0.220, both=True)
        .translate((0.0, 0.0, rod_exposed + 0.030))
    )
    left_grip = (
        cq.Workplane("YZ")
        .circle(0.017)
        .extrude(0.045, both=True)
        .translate((-0.127, 0.0, rod_exposed + 0.030))
    )
    right_grip = (
        cq.Workplane("YZ")
        .circle(0.017)
        .extrude(0.045, both=True)
        .translate((0.127, 0.0, rod_exposed + 0.030))
    )

    knob_core = cq.Workplane("XZ").circle(0.008).extrude(0.006)
    knob_shape = knob_core.faces(">Y").workplane(centerOption="CenterOfMass").circle(0.016).extrude(0.013)

    base = model.part("base")
    base.visual(mesh_from_cadquery(base_shape, "base_shell"), material=base_mat, name="base_shell")

    barrel = model.part("barrel")
    barrel.visual(mesh_from_cadquery(barrel_shape, "barrel_shell"), material=steel_mat, name="barrel_shell")

    gauge_housing = model.part("gauge_housing")
    gauge_housing.visual(
        mesh_from_cadquery(gauge_shape, "gauge_housing_shell"),
        material=gauge_mat,
        name="gauge_housing_shell",
    )

    plunger = model.part("plunger")
    piston_shape = (
        cq.Workplane("XY")
        .cylinder(0.016, barrel_inner_r - 0.004, centered=(True, True, False))
        .translate((0.0, 0.0, -0.255))
    )
    rod_shape = (
        cq.Workplane("XY").cylinder(
            rod_hidden + rod_exposed,
            rod_radius,
            centered=(True, True, False),
        )
        .translate((0.0, 0.0, -rod_hidden))
        .union(plunger_top_collar)
        .union(piston_shape)
    )
    plunger.visual(mesh_from_cadquery(rod_shape, "plunger_rod"), material=steel_mat, name="plunger_rod")
    plunger.visual(mesh_from_cadquery(handle_shape, "plunger_boss"), material=steel_mat, name="plunger_boss")
    plunger.visual(mesh_from_cadquery(handle_crossbar, "handle_crossbar"), material=grip_mat, name="handle_crossbar")
    plunger.visual(mesh_from_cadquery(left_grip, "handle_left_grip"), material=grip_mat, name="handle_left_grip")
    plunger.visual(mesh_from_cadquery(right_grip, "handle_right_grip"), material=grip_mat, name="handle_right_grip")

    selector_knob = model.part("selector_knob")
    selector_knob.visual(
        mesh_from_cadquery(knob_shape, "selector_knob_shell"),
        material=knob_mat,
        name="selector_knob_shell",
    )

    model.articulation(
        "base_to_barrel",
        ArticulationType.FIXED,
        parent=base,
        child=barrel,
        origin=Origin(xyz=(0.0, 0.0, base_height + base_pedestal_height)),
    )

    model.articulation(
        "barrel_to_gauge_housing",
        ArticulationType.FIXED,
        parent=barrel,
        child=gauge_housing,
        origin=Origin(xyz=(0.0, 0.0, gauge_mount_z)),
    )

    model.articulation(
        "barrel_to_plunger",
        ArticulationType.PRISMATIC,
        parent=barrel,
        child=plunger,
        origin=Origin(xyz=(0.0, 0.0, barrel_height + 0.016)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=130.0,
            velocity=0.65,
            lower=0.0,
            upper=plunger_travel,
        ),
    )

    model.articulation(
        "gauge_housing_to_selector_knob",
        ArticulationType.REVOLUTE,
        parent=gauge_housing,
        child=selector_knob,
        origin=Origin(xyz=(0.032, gauge_case_front_y + 0.006, -0.038)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=2.0,
            velocity=4.0,
            lower=-1.25,
            upper=1.25,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
