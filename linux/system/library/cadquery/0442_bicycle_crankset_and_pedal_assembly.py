# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bicycle_crankset_and_pedal_assembly, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bicycle_crankset_and_pedal_assembly

from __future__ import annotations

import cadquery as cq
import math
import numpy as np
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_Sewing,
)

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

# ===== gears (5 syms) =====
def circle3d_by3points(a, b, c):
    """Find a circle in 3D space defined by three points."""

    u = b - a
    w = np.cross(c - a, u)
    u = u / np.linalg.norm(u)
    w = w / np.linalg.norm(w)
    v = np.cross(w, u)

    bx = np.dot(b - a, u)
    cx, cy = np.dot(c - a, u), np.dot(c - a, v)

    h = ((cx - bx / 2.0) ** 2 + cy**2 - (bx / 2.0) ** 2) / (2.0 * cy)
    cc = a + u * (bx / 2.0) + v * h
    r = np.linalg.norm(a - cc)

    return r, cc

def rotation_matrix(axis, alpha):
    """Construct a 3D rotation transform matrix."""

    ux, uy, uz = axis
    sina, cosa = np.sin(alpha), np.cos(alpha)
    return np.array(
        (
            (
                cosa + (1.0 - cosa) * ux**2,
                ux * uy * (1.0 - cosa) - uz * sina,
                ux * uz * (1.0 - cosa) + uy * sina,
            ),
            (
                uy * ux * (1.0 - cosa) + uz * sina,
                cosa + (1.0 - cosa) * uy**2,
                uy * uz * (1.0 - cosa) - ux * sina,
            ),
            (
                uz * ux * (1.0 - cosa) - uy * sina,
                uz * uy * (1.0 - cosa) + ux * sina,
                cosa + (1.0 - cosa) * uz**2,
            ),
        )
    )

def make_shell(faces, tol=1e-2):
    """Like ``cq.Shell.makeShell`` but allows an explicit tolerance."""

    shell_builder = BRepBuilderAPI_Sewing(tol)
    for face in faces:
        shell_builder.Add(face.wrapped)
    shell_builder.Perform()
    return cq.Shell(shell_builder.SewedShape())

class GearBase:
    ka = 1.0
    kd = 1.25

    curve_points = 20
    surface_splines = 5

    wire_comb_tol = 1e-2
    spline_approx_tol = 1e-2
    shell_sewing_tol = 1e-2
    isection_tol = 1e-7
    spline_approx_min_deg = 3
    spline_approx_max_deg = 8

    def __init__(self, *args, **kv_args):
        raise NotImplementedError("Constructor is not defined")

    def build(self, **kv_params):
        params = {**self.build_params, **kv_params}
        return self._build(**params)

class SpurGear(GearBase):
    def __init__(
        self,
        module,
        teeth_number,
        width,
        pressure_angle=20.0,
        helix_angle=0.0,
        clearance=0.0,
        backlash=0.0,
        addendum_coeff=None,
        dedendum_coeff=None,
        **build_params,
    ):
        if addendum_coeff is not None and addendum_coeff <= 0:
            raise ValueError("Addendum coefficient (addendum_coeff) must be greater than 0.")
        if dedendum_coeff is not None and dedendum_coeff <= 0:
            raise ValueError("Dedendum coefficient (dedendum_coeff) must be greater than 0.")

        self.ka = addendum_coeff if addendum_coeff is not None else self.ka
        self.kd = dedendum_coeff if dedendum_coeff is not None else self.kd
        self.m = m = module
        self.z = z = teeth_number
        self.a0 = a0 = np.radians(pressure_angle)
        self.clearance = clearance
        self.backlash = backlash
        self.helix_angle = np.radians(helix_angle)
        self.width = width

        d0 = m * z
        adn = self.ka / (z / d0)
        ddn = self.kd / (z / d0)

        if 2.0 * ddn + 2.0 * clearance >= d0:
            raise ValueError(
                "Invalid dedendum or clearance: resulting dedendum circle diameter is negative or zero."
            )

        da = d0 + 2.0 * adn
        dd = d0 - 2.0 * ddn - 2.0 * clearance
        s0 = m * (np.pi / 2.0 - backlash * np.tan(a0))
        inv_a0 = np.tan(a0) - a0

        self.r0 = r0 = d0 / 2.0
        self.ra = ra = da / 2.0
        self.rd = rd = dd / 2.0
        self.rb = rb = np.cos(a0) * d0 / 2.0
        self.rr = rr = max(rb, rd)
        self.tau = tau = np.pi * 2.0 / z

        if helix_angle != 0.0:
            self.twist_angle = width / (r0 * np.tan(np.pi / 2.0 - self.helix_angle))
        else:
            self.surface_splines = 2
            self.twist_angle = 0.0

        self.build_params = build_params

        r = np.linspace(rr, ra, self.curve_points)
        cos_a = r0 / r * np.cos(a0)
        a = np.arccos(np.clip(cos_a, -1.0, 1.0))
        inv_a = np.tan(a) - a
        s = r * (s0 / d0 + inv_a0 - inv_a)
        phi = s / r
        self.t_lflank_pts = np.dstack(
            (np.cos(phi) * r, np.sin(phi) * r, np.zeros(self.curve_points))
        ).squeeze()

        b = np.linspace(phi[-1], -phi[-1], self.curve_points)
        self.t_tip_pts = np.dstack(
            (np.cos(b) * ra, np.sin(b) * ra, np.zeros(self.curve_points))
        ).squeeze()

        self.t_rflank_pts = np.dstack(
            ((np.cos(-phi) * r)[::-1], (np.sin(-phi) * r)[::-1], np.zeros(self.curve_points))
        ).squeeze()

        rho = tau - phi[0] * 2.0
        p1 = np.array((self.t_rflank_pts[-1][0], self.t_rflank_pts[-1][1], 0.0))
        p2 = np.array((np.cos(-phi[0] - rho / 2.0) * rd, np.sin(-phi[0] - rho / 2.0) * rd, 0.0))
        p3 = np.array((np.cos(-phi[0] - rho) * rr, np.sin(-phi[0] - rho) * rr, 0.0))

        bcr, bcxy = circle3d_by3points(p1, p2, p3)
        t1 = np.arctan2(p1[1] - bcxy[1], p1[0] - bcxy[0])
        t2 = np.arctan2(p3[1] - bcxy[1], p3[0] - bcxy[0])
        if t1 < 0.0:
            t1 += np.pi * 2.0
        if t2 < 0.0:
            t2 += np.pi * 2.0
        t1, t2 = min(t1, t2), max(t1, t2)
        t = np.linspace(t1 + np.pi * 2.0, t2 + np.pi * 2.0, self.curve_points)
        self.t_root_pts = np.dstack(
            (bcxy[0] + bcr * np.cos(t), bcxy[1] + bcr * np.sin(t), np.zeros(self.curve_points))
        ).squeeze()

    def tooth_points(self):
        return np.concatenate(
            (self.t_lflank_pts, self.t_tip_pts, self.t_rflank_pts, self.t_root_pts)
        )

    def gear_points(self):
        tpts = self.tooth_points()
        pts = tpts.copy()
        angle = self.tau
        for _ in range(self.z - 1):
            pts = np.concatenate((pts, tpts @ rotation_matrix((0.0, 0.0, 1.0), angle)))
            angle += self.tau
        return pts

    def _build_tooth_faces(self, twist_angle_a, twist_angle_b, z_pos, width):
        surf_splines = int(np.ceil(abs(self.twist_angle) / np.pi))
        surf_splines = max(1, surf_splines) * self.surface_splines
        spline_tf = np.linspace(
            (twist_angle_a, z_pos), (twist_angle_b, z_pos + width), surf_splines
        )
        t_faces = []
        for spline in (
            self.t_lflank_pts,
            self.t_tip_pts,
            self.t_rflank_pts,
            self.t_root_pts,
        ):
            face_pts = []
            for a, z in spline_tf:
                r_mat = rotation_matrix((0.0, 0.0, 1.0), a)
                pts = spline.copy()
                pts[:, 2] = z
                pts = pts @ r_mat
                face_pts.append([cq.Vector(*pt) for pt in pts])
            face = cq.Face.makeSplineApprox(
                face_pts,
                tol=self.spline_approx_tol,
                minDeg=self.spline_approx_min_deg,
                maxDeg=self.spline_approx_max_deg,
            )
            t_faces.append(face)
        return t_faces

    def _build_gear_faces(self):
        t_faces = self._build_tooth_faces(0.0, self.twist_angle, 0.0, self.width)
        faces = []
        for i in range(self.z):
            for tf in t_faces:
                faces.append(
                    tf.rotate(
                        (0.0, 0.0, 0.0),
                        (0.0, 0.0, 1.0),
                        np.degrees(self.tau * i),
                    )
                )
        wp = cq.Workplane("XY").add(faces)
        topface_wires = cq.Wire.combine(wp.edges("<Z").vals(), tol=self.wire_comb_tol)
        topface = cq.Face.makeFromWires(topface_wires[0])
        botface_wires = cq.Wire.combine(wp.edges(">Z").vals(), tol=self.wire_comb_tol)
        botface = cq.Face.makeFromWires(botface_wires[0])
        wp = wp.add(topface).add(botface)
        return wp.vals()

    def _make_bore(self, body, bore_d):
        if bore_d is None:
            return body
        return (
            cq.Workplane("XY")
            .add(body)
            .faces("<Z")
            .workplane()
            .circle(bore_d / 2.0)
            .cutThruAll()
            .val()
        )

    def _make_teeth_cutout_wire(self, plane, t1, t2, twist_angle):
        at1 = t1 * self.tau + self.tau / 2.0 + twist_angle
        at2 = t2 * self.tau + self.tau / 2.0 + twist_angle
        p1x = np.cos(at1)
        p1y = np.sin(at1)
        p2x = np.cos((at1 + at2) / 2.0)
        p2y = np.sin((at1 + at2) / 2.0)
        p3x = np.cos(at2)
        p3y = np.sin(at2)
        rc = self.ra + 1.0
        rd = self.rd - 0.01
        return (
            plane.moveTo(p1x * rd, p1y * rd)
            .lineTo(p1x * rc, p1y * rc)
            .threePointArc((p2x * rc, p2y * rc), (p3x * rc, p3y * rc))
            .lineTo(p3x * rd, p3y * rd)
            .threePointArc((p2x * rd, p2y * rd), (p1x * rd, p1y * rd))
            .close()
        )

    def _remove_teeth(self, body, t1, t2):
        plane = cq.Workplane("XY").workplane(offset=-0.1).add(body)
        if self.twist_angle == 0.0:
            cutout = self._make_teeth_cutout_wire(plane, t1, t2, 0.0).extrude(
                self.width + 0.2,
                combine=False,
            )
        else:
            cutout = self._make_teeth_cutout_wire(plane, t1, t2, 0.0).twistExtrude(
                self.width + 0.2,
                np.degrees(-self.twist_angle),
                combine=False,
            )
        return cq.Workplane("XY").add(body).cut(cutout).val()

    def _make_missing_teeth(self, body, missing_teeth):
        if missing_teeth is None:
            return body
        if isinstance(missing_teeth[0], (list, tuple)):
            for t1, t2 in missing_teeth:
                body = self._remove_teeth(body, t1, t2)
        else:
            t1, t2 = missing_teeth
            body = self._remove_teeth(body, t1, t2)
        return body

    def _make_recess(
        self,
        body,
        hub_d,
        recess_d,
        recess=None,
        bottom_recess=None,
        bottom_hub_d=None,
        bottom_recess_d=None,
    ):
        if recess is None and bottom_recess is None:
            return body
        if recess is not None:
            assert recess_d is not None, "Top face recess diameter is not set"
        if bottom_recess is not None:
            assert bottom_recess_d is not None or recess_d is not None, (
                "Bottom face recess diameter is not set"
            )
        if recess:
            body = cq.Workplane("XY").add(body).faces(">Z").workplane()
            if hub_d is not None:
                body = body.circle(hub_d / 2.0)
            body = body.circle(recess_d / 2.0).cutBlind(-recess).val()
        if bottom_recess:
            body = cq.Workplane("XY").add(body).faces("<Z").workplane()
            if bottom_hub_d is None:
                bottom_hub_d = hub_d
            if bottom_recess_d is None:
                bottom_recess_d = recess_d
            if bottom_hub_d is not None:
                body = body.circle(bottom_hub_d / 2.0)
            body = body.circle(bottom_recess_d / 2.0).cutBlind(-bottom_recess).val()
        return body

    def _make_hub(self, body, hub_d, hub_length, bore_d):
        if hub_length is None:
            return body
        assert hub_d is not None, "Hub diameter is not set"
        body = cq.Workplane("XY").add(body).faces(">Z").workplane()
        if bore_d is not None:
            body = body.circle(bore_d / 2.0)
        body = body.circle(hub_d / 2.0).extrude(hub_length)
        return body.val()

    def _make_spokes(self, body, spokes_id, spokes_od, n_spokes, spoke_width, spoke_fillet):
        if n_spokes is None:
            return body
        assert n_spokes > 1, "Number of spokes must be > 1"
        assert spoke_width is not None, "Spoke width is not set"
        assert spokes_od is not None, "Outer spokes diameter is not set"
        if spokes_id is None:
            r1 = spoke_width / 2.0
        else:
            r1 = max(spoke_width / 2.0, spokes_id / 2.0)
        r2 = spokes_od / 2.0
        r1 += 0.0001
        r2 -= 0.0001
        tau = np.pi * 2.0 / n_spokes
        a1 = np.arcsin((spoke_width / 2.0) / (spokes_id / 2.0))
        a2 = np.arcsin((spoke_width / 2.0) / (spokes_od / 2.0))
        a3 = tau - a2
        a4 = tau - a1
        cutout = (
            cq.Workplane("XY")
            .workplane(offset=-0.1)
            .moveTo(np.cos(a1) * r1, np.sin(a1) * r1)
            .lineTo(np.cos(a2) * r2, np.sin(a2) * r2)
            .radiusArc((np.cos(a3) * r2, np.sin(a3) * r2), -r2)
            .lineTo(np.cos(a4) * r1, np.sin(a4) * r1)
            .radiusArc((np.cos(a1) * r1, np.sin(a1) * r1), r1)
            .close()
            .extrude(self.width + 1.0)
        )
        if spoke_fillet is not None:
            cutout = cutout.edges("|Z").fillet(spoke_fillet)
        body = cq.Workplane("XY").add(body)
        for i in range(n_spokes):
            body = body.cut(
                cutout.rotate(
                    (0.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0),
                    np.degrees(tau * i),
                )
            )
        return body.val()

    def _make_chamfer(self, body, chamfer=None, chamfer_top=None, chamfer_bottom=None):
        e = 0.01
        if chamfer is None and chamfer_top is None and chamfer_bottom is None:
            return body
        if chamfer is not None:
            if chamfer_top is None:
                chamfer_top = chamfer
            if chamfer_bottom is None:
                chamfer_bottom = chamfer
        if chamfer_top is not None:
            if isinstance(chamfer_top, (list, tuple)):
                wx, wy = chamfer_top
            else:
                wx, wy = chamfer_top, chamfer_top
            cutter = (
                cq.Workplane("XZ")
                .moveTo(self.ra - wx, self.width + e)
                .hLine(wx + e)
                .vLine(-wy - e)
                .close()
                .revolve()
            )
            body = cq.Workplane("XY").add(body).cut(cutter)
        if chamfer_bottom is not None:
            if isinstance(chamfer_bottom, (list, tuple)):
                wx, wy = chamfer_bottom
            else:
                wx, wy = chamfer_bottom, chamfer_bottom
            cutter = (
                cq.Workplane("XZ")
                .moveTo(self.ra + e, wy)
                .vLine(-wy - e)
                .hLine(-wx - e)
                .close()
                .revolve()
            )
            body = cq.Workplane("XY").add(body).cut(cutter)
        return body.val()

    def _build(
        self,
        bore_d=None,
        missing_teeth=None,
        hub_d=None,
        hub_length=None,
        recess_d=None,
        recess=None,
        bottom_recess=None,
        bottom_recess_d=None,
        bottom_hub_d=None,
        n_spokes=None,
        spoke_width=None,
        spoke_fillet=None,
        spokes_id=None,
        spokes_od=None,
        chamfer=None,
        chamfer_top=None,
        chamfer_bottom=None,
        *args,
        **kv_args,
    ):
        faces = self._build_gear_faces()
        shell = make_shell(faces, tol=self.shell_sewing_tol)
        body = cq.Solid.makeSolid(shell)
        body = self._make_chamfer(body, chamfer, chamfer_top, chamfer_bottom)
        body = self._make_bore(body, bore_d)
        body = self._make_missing_teeth(body, missing_teeth)
        body = self._make_recess(
            body,
            hub_d,
            recess_d,
            recess,
            bottom_recess=bottom_recess,
            bottom_hub_d=bottom_hub_d,
            bottom_recess_d=bottom_recess_d,
        )
        body = self._make_hub(body, hub_d, hub_length, bore_d)
        if spokes_id is None:
            spokes_id = hub_d
        if spokes_od is None:
            spokes_od = recess_d
        body = self._make_spokes(body, spokes_id, spokes_od, n_spokes, spoke_width, spoke_fillet)
        return body

# ===== gears cq.Workplane plugin (cq_gears workflow) =====
def _gear_plugin(self, gear_, *a, **k):
    body = gear_.build(*a, **k)
    if hasattr(body, "val"):
        body = body.val()           # Workplane -> Shape
    return self.eachpoint(lambda loc: body.located(loc), True)


def _addgear_plugin(self, gear_, *a, **k):
    return self.union(_gear_plugin(self, gear_, *a, **k))


cq.Workplane.gear = _gear_plugin
cq.Workplane.addGear = _addgear_plugin


# ===== model =====
import cadquery as cq
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="crankset_assembly")

    # Materials
    bb_mat = Material(color=(0.15, 0.15, 0.15), name="bb_mat")
    crank_mat = Material(color=(0.8, 0.8, 0.85), name="crank_mat")
    chainring_mat = Material(color=(0.2, 0.2, 0.2), name="chainring_mat")
    pedal_mat = Material(color=(0.05, 0.05, 0.05), name="pedal_mat")

    # ---------------------------------------------------------
    # 1. Bottom Bracket (Base)
    # ---------------------------------------------------------
    bb_part = model.part("bottom_bracket")
    
    # Shell: Y-axis cylinder
    bb_shell = cq.Workplane("XZ").cylinder(0.068, 0.02)
    
    # Frame stubs
    seat_tube = cq.Workplane("XY").center(0, 0).circle(0.016).extrude(0.15).rotate((0,0,0), (0,1,0), -15)
    down_tube = cq.Workplane("XY").center(0, 0).circle(0.018).extrude(0.15).rotate((0,0,0), (0,1,0), 60)
    
    # Chainstays (using YZ plane, extruding along -X)
    chainstay_l = (cq.Workplane("YZ").center(0.025, 0)
                   .circle(0.01)
                   .workplane(offset=-0.15)
                   .center(0.03, 0)
                   .circle(0.008)
                   .loft())
    chainstay_r = (cq.Workplane("YZ").center(-0.025, 0)
                   .circle(0.01)
                   .workplane(offset=-0.15)
                   .center(-0.03, 0)
                   .circle(0.008)
                   .loft())
    
    bb_body = bb_shell.union(seat_tube).union(down_tube).union(chainstay_l).union(chainstay_r)
    bb_part.visual(mesh_from_cadquery(bb_body, "bb_mesh"), name="bb_frame", material=bb_mat)

    # ---------------------------------------------------------
    # 2. Crankset (Rotating)
    # ---------------------------------------------------------
    crank_part = model.part("crankset")
    
    # Spindle
    spindle = cq.Workplane("XZ").cylinder(0.14, 0.012)
    
    # Right Crank Arm (at Y = -0.06, extending to Z = 0.17)
    r_crank = (cq.Workplane("XZ")
               .workplane(offset=0.06)
               .moveTo(0, 0).circle(0.02)
               .extrude(0.015)
               .union(
                   cq.Workplane("XZ").workplane(offset=0.06)
                   .moveTo(0, 0.17).circle(0.015)
                   .extrude(0.015)
               )
               .union(
                   cq.Workplane("XZ").workplane(offset=0.06)
                   .polyline([(-0.02, 0), (0.02, 0), (0.015, 0.17), (-0.015, 0.17)])
                   .close()
                   .extrude(0.015)
               ))
               
    # Left Crank Arm (at Y = 0.06, extending to Z = -0.17)
    l_crank = (cq.Workplane("XZ")
               .workplane(offset=-0.06)
               .moveTo(0, 0).circle(0.02)
               .extrude(-0.015)
               .union(
                   cq.Workplane("XZ").workplane(offset=-0.06)
                   .moveTo(0, -0.17).circle(0.015)
                   .extrude(-0.015)
               )
               .union(
                   cq.Workplane("XZ").workplane(offset=-0.06)
                   .polyline([(-0.02, 0), (0.02, 0), (0.015, -0.17), (-0.015, -0.17)])
                   .close()
                   .extrude(-0.015)
               ))
               
    # Spider (4 arms)
    spider = (cq.Workplane("XZ").workplane(offset=0.05)
              .polarArray(0.045, 45, 360, 4)
              .rect(0.09, 0.015)
              .extrude(0.005))
              
    # Pedal Axles
    r_axle = (cq.Workplane("XZ").workplane(offset=0.07)
              .center(0, 0.17)
              .circle(0.006)
              .extrude(0.09)) # reaches Y = -0.16
    l_axle = (cq.Workplane("XZ").workplane(offset=-0.07)
              .center(0, -0.17)
              .circle(0.006)
              .extrude(-0.09)) # reaches Y = 0.16
              
    crank_core = spindle.union(r_crank).union(l_crank).union(spider).union(r_axle).union(l_axle)
    crank_part.visual(mesh_from_cadquery(crank_core, "crank_core"), name="core", material=crank_mat)
    
    # Chainring
    chainring_gear = SpurGear(module=0.004, teeth_number=45, width=0.004, bore_d=0.13)
    chainring_body = cq.Workplane("XZ").workplane(offset=0.052).gear(chainring_gear).val()
    crank_part.visual(mesh_from_cadquery(chainring_body, "chainring"), name="chainring", material=chainring_mat)

    # ---------------------------------------------------------
    # 3. Pedals
    # ---------------------------------------------------------
    # Base pedal body centered at origin
    pedal_body = (cq.Workplane("XY")
                  .box(0.10, 0.08, 0.02)
                  .faces(">Y").workplane().circle(0.007).cutThruAll())
    
    pins = (cq.Workplane("XY").workplane(offset=0.01)
            .rect(0.08, 0.06, forConstruction=True)
            .vertices()
            .circle(0.002).extrude(0.002))
    pins_bottom = (cq.Workplane("XY").workplane(offset=-0.01)
                   .rect(0.08, 0.06, forConstruction=True)
                   .vertices()
                   .circle(0.002).extrude(-0.002))
    
    pedal_mesh = pedal_body.union(pins).union(pins_bottom)
    
    r_pedal = model.part("right_pedal")
    r_pedal.visual(mesh_from_cadquery(pedal_mesh, "r_pedal_mesh"), name="body", material=pedal_mat)
    
    l_pedal = model.part("left_pedal")
    l_pedal.visual(mesh_from_cadquery(pedal_mesh, "l_pedal_mesh"), name="body", material=pedal_mat)

    # ---------------------------------------------------------
    # Articulations
    # ---------------------------------------------------------
    # Crankset to Bottom Bracket
    model.articulation(
        "bb_to_crankset",
        ArticulationType.CONTINUOUS,
        parent=bb_part,
        child=crank_part,
        origin=Origin(xyz=(0, 0, 0)),
        axis=(0, -1, 0),
        motion_limits=MotionLimits(effort=10.0, velocity=10.0),
    )
    
    # Right Pedal to Crankset
    model.articulation(
        "crankset_to_r_pedal",
        ArticulationType.CONTINUOUS,
        parent=crank_part,
        child=r_pedal,
        origin=Origin(xyz=(0, -0.12, 0.17)),
        axis=(0, -1, 0),
        motion_limits=MotionLimits(effort=2.0, velocity=10.0),
    )
    
    # Left Pedal to Crankset
    model.articulation(
        "crankset_to_l_pedal",
        ArticulationType.CONTINUOUS,
        parent=crank_part,
        child=l_pedal,
        origin=Origin(xyz=(0, 0.12, -0.17)),
        axis=(0, -1, 0),
        motion_limits=MotionLimits(effort=2.0, velocity=10.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
