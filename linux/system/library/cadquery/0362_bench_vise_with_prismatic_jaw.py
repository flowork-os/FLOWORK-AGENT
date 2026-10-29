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
    model = ArticulatedObject(name="bench_vise")
    
    mat_cast_iron = model.material("cast_iron", color=(0.2, 0.2, 0.22))
    mat_steel = model.material("steel", color=(0.75, 0.75, 0.8))
    mat_hard_steel = model.material("hard_steel", color=(0.3, 0.3, 0.35))
    
    # 1. Base
    base_plate = cq.Workplane("XY").box(0.26, 0.16, 0.02).translate((0, 0, 0.01))
    body_block = cq.Workplane("XY").box(0.16, 0.08, 0.08).translate((-0.02, 0, 0.06))
    fixed_jaw = cq.Workplane("XY").box(0.04, 0.12, 0.06).translate((0.04, 0, 0.13))
    anvil = cq.Workplane("XY").box(0.06, 0.06, 0.01).translate((-0.06, 0, 0.105))
    
    base_shape = base_plate.union(body_block).union(fixed_jaw).union(anvil)
    
    slide_hole = cq.Workplane("XY").box(0.20, 0.042, 0.042).translate((-0.02, 0, 0.06))
    base_shape = base_shape.cut(slide_hole)
    
    nut_block = cq.Workplane("XY").box(0.02, 0.018, 0.04).translate((-0.08, 0, 0.058))
    base_shape = base_shape.union(nut_block)
    
    nut_hole = cq.Workplane("YZ").cylinder(0.04, 0.009).translate((-0.08, 0, 0.06))
    base_shape = base_shape.cut(nut_hole)
    
    fixed_jaw_plate = cq.Workplane("XY").box(0.012, 0.10, 0.04).translate((0.064, 0, 0.14))
    
    base = model.part("base")
    base.visual(mesh_from_cadquery(base_shape, "base_body"), material=mat_cast_iron)
    base.visual(mesh_from_cadquery(fixed_jaw_plate, "fixed_jaw_plate_mesh"), name="fixed_jaw_plate", material=mat_hard_steel)
    
    # 2. Sliding Jaw
    slide_bar_outer = cq.Workplane("XY").box(0.20, 0.04, 0.04).translate((-0.10, 0, 0.06))
    slide_bar_inner = cq.Workplane("XY").box(0.20, 0.02, 0.03).translate((-0.10, 0, 0.055))
    slide_bar = slide_bar_outer.cut(slide_bar_inner)
    
    dynamic_jaw = cq.Workplane("XY").box(0.04, 0.12, 0.10).translate((0.02, 0, 0.11))
    screw_boss = cq.Workplane("XY").box(0.04, 0.06, 0.06).translate((0.06, 0, 0.07))
    
    sliding_jaw_shape = slide_bar.union(dynamic_jaw).union(screw_boss)
    
    screw_boss_hole = cq.Workplane("YZ").cylinder(0.10, 0.009).translate((0.06, 0, 0.06))
    sliding_jaw_shape = sliding_jaw_shape.cut(screw_boss_hole)
    
    dynamic_jaw_plate = cq.Workplane("XY").box(0.012, 0.10, 0.04).translate((-0.004, 0, 0.14))
    
    sliding_jaw = model.part("sliding_jaw")
    sliding_jaw.visual(mesh_from_cadquery(sliding_jaw_shape, "sliding_jaw_body"), material=mat_cast_iron)
    sliding_jaw.visual(mesh_from_cadquery(dynamic_jaw_plate, "dynamic_jaw_plate_mesh"), name="dynamic_jaw_plate", material=mat_hard_steel)
    
    # 3. Screw
    screw_rod = cq.Workplane("YZ").cylinder(0.35, 0.008).translate((-0.175, 0, 0))
    screw_head = cq.Workplane("YZ").cylinder(0.02, 0.015).translate((0.01, 0, 0))
    handle_hub = cq.Workplane("YZ").cylinder(0.03, 0.018).translate((0.035, 0, 0))
    screw_shape = screw_rod.union(screw_head).union(handle_hub)
    
    handle_hole = cq.Workplane("XZ").cylinder(0.05, 0.005).translate((0.035, 0, 0))
    screw_shape = screw_shape.cut(handle_hole)
    
    screw = model.part("screw")
    screw.visual(mesh_from_cadquery(screw_shape, "screw_body"), material=mat_steel)
    
    # 4. Handle
    handle_rod = cq.Workplane("XZ").cylinder(0.15, 0.004)
    handle_cap1 = cq.Workplane("XZ").cylinder(0.01, 0.007).translate((0, 0.075, 0))
    handle_cap2 = cq.Workplane("XZ").cylinder(0.01, 0.007).translate((0, -0.075, 0))
    handle_shape = handle_rod.union(handle_cap1).union(handle_cap2)
    
    handle = model.part("handle")
    handle.visual(mesh_from_cadquery(handle_shape, "handle_body"), material=mat_steel)
    
    # Articulations
    
    # jaw_slide: base -> sliding_jaw
    # sliding_jaw origin at X=0.08 so when q=0, the dynamic plate (local X=-0.01) is at world X=0.07
    # which touches the fixed plate (world X=0.06 to 0.07).
    model.articulation(
        "jaw_slide",
        ArticulationType.PRISMATIC,
        parent=base,
        child=sliding_jaw,
        origin=Origin(xyz=(0.08, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=1000.0, velocity=0.1, lower=0.0, upper=0.10)
    )
    
    # screw_turn: sliding_jaw -> screw
    model.articulation(
        "screw_turn",
        ArticulationType.REVOLUTE,
        parent=sliding_jaw,
        child=screw,
        origin=Origin(xyz=(0.08, 0.0, 0.06)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=10.0, velocity=10.0, lower=-100.0, upper=100.0)
    )
    
    # handle_slide: screw -> handle
    model.articulation(
        "handle_slide",
        ArticulationType.PRISMATIC,
        parent=screw,
        child=handle,
        origin=Origin(xyz=(0.035, 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=5.0, velocity=1.0, lower=-0.05, upper=0.05)
    )
    
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
