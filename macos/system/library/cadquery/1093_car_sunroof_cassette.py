# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, car_sunroof_cassette, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: car_sunroof_cassette

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
def _rounded_plate(length: float, width: float, thickness: float, radius: float):
    """CadQuery rounded rectangle plate centered on the local origin."""
    sketch = cq.Sketch().rect(length, width).vertices().fillet(radius)
    return cq.Workplane("XY").placeSketch(sketch).extrude(thickness).translate(
        (0.0, 0.0, -thickness / 2.0)
    )
def _rounded_ring(
    outer_length: float,
    outer_width: float,
    inner_length: float,
    inner_width: float,
    thickness: float,
    outer_radius: float,
    inner_radius: float,
):
    """CadQuery rectangular ring with rounded outside and aperture corners."""
    sketch = (
        cq.Sketch()
        .rect(outer_length, outer_width, tag="outer")
        .vertices(tag="outer")
        .fillet(outer_radius)
        .reset()
        .rect(inner_length, inner_width, mode="s", tag="inner")
        .vertices(tag="inner")
        .fillet(inner_radius)
    )
    return cq.Workplane("XY").placeSketch(sketch).extrude(thickness).translate(
        (0.0, 0.0, -thickness / 2.0)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="automotive_sunroof_cassette")

    e_coat = model.material("satin_black_e_coat", rgba=(0.015, 0.017, 0.018, 1.0))
    rubber = model.material("molded_black_rubber", rgba=(0.002, 0.002, 0.002, 1.0))
    rail_metal = model.material("brushed_anodized_aluminum", rgba=(0.55, 0.57, 0.56, 1.0))
    drain_plastic = model.material("black_drain_plastic", rgba=(0.018, 0.018, 0.016, 1.0))
    fastener = model.material("zinc_fastener_heads", rgba=(0.64, 0.62, 0.55, 1.0))
    tinted_glass = model.material("smoked_tempered_glass", rgba=(0.02, 0.07, 0.10, 0.45))
    frit = model.material("black_ceramic_frit", rgba=(0.0, 0.0, 0.0, 0.92))

    cassette = model.part("cassette")

    roof_frame = _rounded_ring(
        outer_length=1.90,
        outer_width=1.10,
        inner_length=1.24,
        inner_width=0.80,
        thickness=0.028,
        outer_radius=0.080,
        inner_radius=0.055,
    )
    cassette.visual(
        mesh_from_cadquery(roof_frame, "roof_frame", tolerance=0.0015),
        origin=Origin(xyz=(0.0, 0.0, 0.014)),
        material=e_coat,
        name="roof_frame",
    )

    seal_ring = _rounded_ring(
        outer_length=1.24,
        outer_width=0.80,
        inner_length=1.08,
        inner_width=0.71,
        thickness=0.018,
        outer_radius=0.050,
        inner_radius=0.040,
    )
    cassette.visual(
        mesh_from_cadquery(seal_ring, "rubber_seal", tolerance=0.001),
        origin=Origin(xyz=(0.0, 0.0, 0.036)),
        material=rubber,
        name="rubber_seal",
    )

    cassette.visual(
        Box((0.54, 0.70, 0.018)),
        origin=Origin(xyz=(0.725, 0.0, 0.035)),
        material=e_coat,
        name="rear_trough",
    )
    cassette.visual(
        Box((0.44, 0.28, 0.030)),
        origin=Origin(xyz=(-0.775, 0.0, 0.046)),
        material=drain_plastic,
        name="motor_housing",
    )
    cassette.visual(
        Cylinder(radius=0.017, length=0.88),
        origin=Origin(xyz=(-0.775, 0.0, 0.070), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=drain_plastic,
        name="drive_cable_tube",
    )

    for side_index, side in enumerate((1.0, -1.0)):
        y = side * 0.440
        cassette.visual(
            Box((1.70, 0.130, 0.024)),
            origin=Origin(xyz=(0.100, y, 0.038)),
            material=rail_metal,
            name=f"rail_base_{side_index}",
        )
        cassette.visual(
            Box((1.66, 0.070, 0.006)),
            origin=Origin(xyz=(0.110, y, 0.053)),
            material=rubber,
            name=f"guide_lane_{side_index}",
        )
        cassette.visual(
            Box((1.62, 0.016, 0.042)),
            origin=Origin(xyz=(0.110, side * 0.380, 0.069)),
            material=rail_metal,
            name=f"guide_lip_inner_{side_index}",
        )
        cassette.visual(
            Box((1.62, 0.016, 0.042)),
            origin=Origin(xyz=(0.110, side * 0.500, 0.069)),
            material=rail_metal,
            name=f"guide_lip_outer_{side_index}",
        )

        for screw_index, x in enumerate((-0.55, -0.12, 0.35, 0.78)):
            cassette.visual(
                Cylinder(radius=0.018, length=0.008),
                origin=Origin(xyz=(x, y, 0.054)),
                material=fastener,
                name=f"screw_head_{side_index}_{screw_index}",
            )

    for drain_index, (x, y) in enumerate(
        ((-0.780, 0.455), (0.770, 0.455), (-0.780, -0.455), (0.770, -0.455))
    ):
        side = 1.0 if y > 0.0 else -1.0
        cassette.visual(
            Cylinder(radius=0.033, length=0.042),
            origin=Origin(xyz=(x, y, 0.047)),
            material=drain_plastic,
            name=f"drain_pot_{drain_index}",
        )
        cassette.visual(
            Cylinder(radius=0.011, length=0.190),
            origin=Origin(xyz=(x, side * 0.575, 0.044), rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=drain_plastic,
            name=f"drain_nipple_{drain_index}",
        )

    glass = model.part("glass_panel")
    glass.visual(
        mesh_from_cadquery(_rounded_plate(1.05, 0.68, 0.018, 0.055), "glass_pane"),
        material=tinted_glass,
        name="glass_pane",
    )
    glass.visual(
        mesh_from_cadquery(
            _rounded_ring(1.05, 0.68, 0.87, 0.50, 0.006, 0.055, 0.040),
            "ceramic_border",
        ),
        origin=Origin(xyz=(0.0, 0.0, 0.012)),
        material=frit,
        name="ceramic_border",
    )
    glass.visual(
        Box((0.30, 0.045, 0.004)),
        origin=Origin(xyz=(-0.485, 0.0, 0.011)),
        material=frit,
        name="front_frit_band",
    )

    for side_index, side in enumerate((1.0, -1.0)):
        for station_name, x in (("front", -0.340), ("rear", 0.340)):
            glass.visual(
                Box((0.190, 0.055, 0.014)),
                origin=Origin(xyz=(x, side * 0.440, 0.041)),
                material=rail_metal,
                name=f"shoe_{station_name}_{side_index}",
            )
            glass.visual(
                Box((0.205, 0.110, 0.010)),
                origin=Origin(xyz=(x, side * 0.395, 0.031)),
                material=rail_metal,
                name=f"support_arm_{station_name}_{side_index}",
            )
            glass.visual(
                Box((0.120, 0.030, 0.052)),
                origin=Origin(xyz=(x, side * 0.335, 0.016)),
                material=frit,
                name=f"edge_tab_{station_name}_{side_index}",
            )

    model.articulation(
        "cassette_to_glass",
        ArticulationType.PRISMATIC,
        parent=cassette,
        child=glass,
        origin=Origin(xyz=(0.0, 0.0, 0.064)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=180.0, velocity=0.35, lower=0.0, upper=0.420),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
