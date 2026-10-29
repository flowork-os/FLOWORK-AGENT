# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, candy_vending_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: candy_vending_machine

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
def build_body_mesh():
    body = cq.Workplane("XY").box(0.3, 0.3, 1.2).translate((0, 0, 0.6))
    
    cut_box = cq.Workplane("XY").box(0.26, 0.26, 0.25)
    
    # Bin 2 interior: Z=0.9 to 1.15. Center: 1.025
    bin2_cut = cut_box.translate((0, 0, 1.025))
    body = body.cut(bin2_cut)
    
    # Bin 1 interior: Z=0.6 to 0.85. Center: 0.725
    bin1_cut = cut_box.translate((0, 0, 0.725))
    body = body.cut(bin1_cut)
    
    # Bin 0 interior: Z=0.3 to 0.55. Center: 0.425
    bin0_cut = cut_box.translate((0, 0, 0.425))
    body = body.cut(bin0_cut)
    
    # Retrieval interior: Z=0.05 to 0.25. Center: 0.15. Height: 0.2
    retrieval_cut = cq.Workplane("XY").box(0.26, 0.26, 0.2).translate((0, 0, 0.15))
    body = body.cut(retrieval_cut)
    
    # Front cutouts
    front_cut_box = cq.Workplane("XY").box(0.22, 0.2, 0.15)
    
    # Door cutout: Z=0.1 to 0.25. Center: 0.175
    door_cut = front_cut_box.translate((0, -0.15, 0.175))
    body = body.cut(door_cut)
    
    # Window 0 cutout: Z=0.4 to 0.55. Center: 0.475
    win0_cut = front_cut_box.translate((0, -0.15, 0.475))
    body = body.cut(win0_cut)
    
    # Window 1 cutout: Z=0.7 to 0.85. Center: 0.775
    win1_cut = front_cut_box.translate((0, -0.15, 0.775))
    body = body.cut(win1_cut)
    
    # Window 2 cutout: Z=1.0 to 1.15. Center: 1.075
    win2_cut = front_cut_box.translate((0, -0.15, 1.075))
    body = body.cut(win2_cut)
    
    return body
def build_dial_mesh():
    # Base cylinder
    dial = cq.Workplane("XY").circle(0.035).extrude(0.015)
    # Grip ridge
    ridge = cq.Workplane("XY").rect(0.015, 0.07).extrude(0.025)
    return dial.union(ridge)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="candy_vending_machine")
    
    body_part = model.part("body")
    body_part.visual(
        mesh_from_cadquery(build_body_mesh(), "body_mesh"),
        name="main_case",
        color=(0.8, 0.1, 0.1) # Red vending machine
    )
    
    # Add windows
    body_part.visual(
        Box((0.22, 0.01, 0.15)),
        origin=Origin(xyz=(0, -0.145, 0.475)),
        name="window_0",
        color=(0.8, 0.9, 1.0, 0.4)
    )
    body_part.visual(
        Box((0.22, 0.01, 0.15)),
        origin=Origin(xyz=(0, -0.145, 0.775)),
        name="window_1",
        color=(0.8, 0.9, 1.0, 0.4)
    )
    body_part.visual(
        Box((0.22, 0.01, 0.15)),
        origin=Origin(xyz=(0, -0.145, 1.075)),
        name="window_2",
        color=(0.8, 0.9, 1.0, 0.4)
    )
    
    # Add dials
    for i in range(3):
        z_pos = 0.325 + i * 0.3
        dial = model.part(f"dial_{i}")
        dial.visual(
            mesh_from_cadquery(build_dial_mesh(), f"dial_mesh_{i}"),
            origin=Origin(rpy=(math.pi/2, 0, 0)),
            name=f"dial_{i}_visual",
            color=(0.9, 0.9, 0.9) # Silver/metallic dials
        )
        model.articulation(
            f"body_to_dial_{i}",
            ArticulationType.CONTINUOUS,
            parent=body_part,
            child=dial,
            origin=Origin(xyz=(0, -0.148, z_pos)),
            axis=(0, 1, 0),
            motion_limits=MotionLimits(effort=5.0, velocity=10.0),
        )
        
    # Add retrieval door
    door = model.part("retrieval_door")
    door.visual(
        Box((0.21, 0.018, 0.14)),
        origin=Origin(xyz=(0, 0.01, 0.07)),
        name="door_panel",
        color=(0.7, 0.7, 0.7)
    )
    model.articulation(
        "body_to_door",
        ArticulationType.REVOLUTE,
        parent=body_part,
        child=door,
        origin=Origin(xyz=(0, -0.15, 0.105)),
        axis=(1, 0, 0),
        motion_limits=MotionLimits(lower=0.0, upper=math.pi/2)
    )
    
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
