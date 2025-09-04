#!/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import math
import random
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional, Union

import numpy as np
import open3d as o3d
import trimesh

DESCRIPTION = r'''
╭──────────────────────────────────────────────────────────────────────────╮
│                         URDF Visualizer (viz_urdf)                       │
│                                                                          │
│  Load a robot URDF (supports .dae/.obj/.stl) into a minimal Open3D GUI.  │
│  Keys:                                                                   │
│    v  toggle visuals        c  toggle collisions (default OFF)           │
│    a  toggle axes           g  toggle grid (±grid-size, 0.5 m cells)     │
│    l  reset joints          j  randomize joints within limits            │
│    f  frame once            x  exit                                      │
│                                                                          │
│  Notes: solid vertex/face/material colors are shown; textures are not.   │
╰──────────────────────────────────────────────────────────────────────────╯
'''

USAGE_EXAMPLES = "Example: ./viz_urdf.py -p ../urdf/robot.urdf -g 5\n"

# ---------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------
def abspath(p: str) -> str:
    return os.path.abspath(os.path.expanduser(p))

def validate_file_exists(p: str) -> None:
    if not os.path.isfile(p):
        sys.stderr.write(f"Error: file not found: {p}\n")
        sys.exit(1)

def rpy_to_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    Rz = np.array([[cy, -sy, 0],[sy, cy, 0],[0,0,1]])
    Ry = np.array([[cp, 0, sp],[0, 1, 0],[-sp,0,cp]])
    Rx = np.array([[1,0,0],[0,cr,-sr],[0,sr,cr]])
    return Rz @ Ry @ Rx

def make_T(R: np.ndarray, t: np.ndarray) -> np.ndarray:
    T = np.eye(4); T[:3,:3] = R; T[:3,3] = t; return T

def parse_xyz(s: Optional[str]) -> np.ndarray:
    if not s: return np.zeros(3)
    v = [float(x) for x in s.split()]
    return np.array(v if len(v)==3 else [0,0,0], dtype=float)

def parse_rpy(s: Optional[str]) -> np.ndarray:
    if not s: return np.zeros(3)
    v = [float(x) for x in s.split()]
    return np.array(v if len(v)==3 else [0,0,0], dtype=float)

def parse_scale(s: Optional[str]) -> np.ndarray:
    if not s: return np.ones(3)
    v = [float(x) for x in s.split()]
    if len(v)==1: v = [v[0], v[0], v[0]]
    return np.array(v, dtype=float)

# ---------------------------------------------------------------------
# URDF structures
# ---------------------------------------------------------------------
class VisualGeom:
    def __init__(self, filename: str, origin_T: np.ndarray, scale: np.ndarray):
        self.filename = filename
        self.origin_T = origin_T
        self.scale = scale

class CollisionGeom:
    def __init__(self, filename: str, origin_T: np.ndarray, scale: np.ndarray):
        self.filename = filename
        self.origin_T = origin_T
        self.scale = scale

class CollisionBox:
    def __init__(self, size: np.ndarray, origin_T: np.ndarray):
        self.size = size
        self.origin_T = origin_T

class LinkData:
    def __init__(self, name: str):
        self.name = name
        self.visuals: List[VisualGeom] = []
        self.collision_meshes: List[CollisionGeom] = []
        self.collision_boxes: List[CollisionBox] = []

class JointData:
    def __init__(self, name: str, jtype: str, parent: str, child: str,
                 origin_T: np.ndarray, axis: np.ndarray,
                 lower: Optional[float], upper: Optional[float]):
        self.name = name
        self.type = jtype
        self.parent = parent
        self.child = child
        self.origin_T = origin_T
        self.axis = axis
        self.lower = lower
        self.upper = upper

class URDFModel:
    def __init__(self, urdf_path: str):
        self.urdf_path = abspath(urdf_path)
        self.base_dir = os.path.dirname(self.urdf_path)
        self.links: Dict[str, LinkData] = {}
        self.joints: Dict[str, JointData] = {}
        self.child_to_joint: Dict[str, str] = {}
        self.parent_to_children: Dict[str, List[str]] = {}
        self.root_link: Optional[str] = None

    def resolve_mesh_path(self, fname: str) -> str:
        if fname.startswith("package://"):
            fname = fname[len("package://"):]
        return fname if os.path.isabs(fname) else os.path.join(self.base_dir, fname)

    def parse(self):
        root = ET.parse(self.urdf_path).getroot()
        # links
        for le in root.findall("link"):
            lname = le.attrib["name"]
            link = LinkData(lname)
            # visuals
            for ve in le.findall("visual"):
                origin = ve.find("origin")
                xyz = parse_xyz(origin.attrib.get("xyz")) if origin is not None else np.zeros(3)
                rpy = parse_rpy(origin.attrib.get("rpy")) if origin is not None else np.zeros(3)
                T = make_T(rpy_to_matrix(*rpy), xyz)
                geom = ve.find("geometry")
                if geom is not None and geom.find("mesh") is not None:
                    me = geom.find("mesh")
                    fn = me.attrib.get("filename")
                    if fn:
                        sc = parse_scale(me.attrib.get("scale"))
                        link.visuals.append(VisualGeom(self.resolve_mesh_path(fn), T, sc))
            # collisions
            for ce in le.findall("collision"):
                origin = ce.find("origin")
                xyz = parse_xyz(origin.attrib.get("xyz")) if origin is not None else np.zeros(3)
                rpy = parse_rpy(origin.attrib.get("rpy")) if origin is not None else np.zeros(3)
                T = make_T(rpy_to_matrix(*rpy), xyz)
                geom = ce.find("geometry")
                if geom is not None:
                    me = geom.find("mesh")
                    be = geom.find("box")
                    if me is not None and me.attrib.get("filename"):
                        fn = me.attrib.get("filename")
                        sc = parse_scale(me.attrib.get("scale"))
                        link.collision_meshes.append(CollisionGeom(self.resolve_mesh_path(fn), T, sc))
                    elif be is not None and be.attrib.get("size"):
                        size = parse_xyz(be.attrib.get("size"))
                        link.collision_boxes.append(CollisionBox(size, T))
            self.links[lname] = link

        # joints
        for je in root.findall("joint"):
            jname = je.attrib["name"]
            jtype = je.attrib.get("type", "fixed")
            parent = je.find("parent").attrib["link"]
            child  = je.find("child").attrib["link"]
            origin = je.find("origin")
            xyz = parse_xyz(origin.attrib.get("xyz")) if origin is not None else np.zeros(3)
            rpy = parse_rpy(origin.attrib.get("rpy")) if origin is not None else np.zeros(3)
            origin_T = make_T(rpy_to_matrix(*rpy), xyz)
            axis_e = je.find("axis")
            axis = parse_xyz(axis_e.attrib.get("xyz")) if axis_e is not None else np.array([0,0,1], dtype=float)
            lower = upper = None
            limit = je.find("limit")
            if limit is not None:
                if "lower" in limit.attrib: lower = float(limit.attrib["lower"])
                if "upper" in limit.attrib: upper = float(limit.attrib["upper"])
            jd = JointData(jname, jtype, parent, child, origin_T, axis, lower, upper)
            self.joints[jname] = jd
            self.child_to_joint[child] = jname
            self.parent_to_children.setdefault(parent, []).append(child)

        # root link
        all_links = set(self.links.keys())
        child_links = set(self.child_to_joint.keys())
        roots = list(all_links - child_links)
        self.root_link = roots[0] if roots else None

    def fk(self, qmap: Dict[str,float]) -> Dict[str,np.ndarray]:
        if self.root_link is None: return {}
        world_T = {self.root_link: np.eye(4)}
        stack = [self.root_link]
        while stack:
            parent = stack.pop()
            Tp = world_T[parent]
            for child in self.parent_to_children.get(parent, []):
                jn = self.child_to_joint.get(child)
                if jn is None: continue
                jd = self.joints[jn]
                q = qmap.get(jn, 0.0)
                if jd.type in ("revolute","continuous"):
                    axis = jd.axis / (np.linalg.norm(jd.axis)+1e-12)
                    K = np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
                    Rm = np.eye(3) + math.sin(q)*K + (1-math.cos(q))*(K@K)
                    Tm = make_T(Rm, np.zeros(3))
                elif jd.type=="prismatic":
                    Tm = make_T(np.eye(3), jd.axis*q)
                else:
                    Tm = np.eye(4)
                world_T[child] = Tp @ jd.origin_T @ Tm
                stack.append(child)
        return world_T

# ---------------------------------------------------------------------
# mesh helpers & color handling
# ---------------------------------------------------------------------
def _apply_scale(geom: Union[o3d.geometry.TriangleMesh,o3d.geometry.LineSet], s: np.ndarray):
    S = np.eye(4); S[0,0],S[1,1],S[2,2] = s
    geom.transform(S)

def _paint_uniform(mesh: o3d.geometry.TriangleMesh, rgb=(0.7,0.7,0.7)):
    mesh.paint_uniform_color(rgb)

def trimesh_to_o3d(mesh: trimesh.Trimesh, default=(0.7,0.7,0.7)) -> Optional[o3d.geometry.TriangleMesh]:
    if mesh.is_empty or not mesh.faces.size: return None
    g = o3d.geometry.TriangleMesh()
    g.vertices = o3d.utility.Vector3dVector(np.asarray(mesh.vertices))
    g.triangles = o3d.utility.Vector3iVector(np.asarray(mesh.faces))
    # try to preserve colors
    colored = False
    try:
        vis = getattr(mesh, "visual", None)
        if vis is not None:
            vc = getattr(vis, "vertex_colors", None)
            if vc is not None and len(vc):
                c = np.asarray(vc, dtype=np.float32)
                if c.max() > 1.0: c /= 255.0
                if c.shape[1] >= 3:
                    g.vertex_colors = o3d.utility.Vector3dVector(c[:, :3]); colored = True
            if not colored:
                fc = getattr(vis, "face_colors", None)
                if fc is not None and len(fc):
                    c0 = np.asarray(fc[0], dtype=np.float32)
                    if c0.max() > 1.0: c0 /= 255.0
                    _paint_uniform(g, (float(c0[0]), float(c0[1]), float(c0[2]))); colored = True
            if not colored:
                mat = getattr(vis, "material", None)
                for attr in ("main_color","diffuse","ambient","specular","color"):
                    val = getattr(mat, attr, None) if mat is not None else None
                    if val is not None:
                        cc = np.asarray(val, dtype=np.float32).flatten()
                        if cc.size >= 3:
                            if cc.max()>1.0: cc/=255.0
                            _paint_uniform(g, (float(cc[0]), float(cc[1]), float(cc[2]))); colored = True; break
    except Exception:
        pass
    if not colored:
        _paint_uniform(g, default)
    g.compute_vertex_normals()
    return g

def _collada_extract_material_colors(mesh_path: str) -> List[np.ndarray]:
    """Optional fallback via pycollada to read per-material diffuse colors."""
    colors: List[np.ndarray] = []
    try:
        import collada  # pycollada
        dae = collada.Collada(mesh_path)
        for mat in getattr(dae, "materials", []):
            eff = getattr(mat, "effect", None)
            if eff is None:
                continue
            diff = getattr(eff, "diffuse", None)
            if hasattr(diff, "sampler"):  # texture map → skip
                continue
            if diff is None:
                continue
            arr = np.array(diff, dtype=float).flatten()
            if arr.size >= 3:
                if arr.max() > 1.0: arr /= 255.0
                colors.append(arr[:3])
    except Exception:
        pass
    return colors

def load_meshes_as_o3d(mesh_path: str, scale: np.ndarray, default=(0.7,0.7,0.7)) -> List[o3d.geometry.TriangleMesh]:
    out: List[o3d.geometry.TriangleMesh] = []
    try:
        tm = trimesh.load_mesh(mesh_path, process=False)
        # trimesh may return a list, a Trimesh, or a Scene
        if isinstance(tm, list):
            for sub in tm:
                if isinstance(sub, trimesh.Trimesh):
                    g = trimesh_to_o3d(sub, default)
                    if g is not None:
                        _apply_scale(g, scale); out.append(g)
        elif isinstance(tm, trimesh.Trimesh):
            g = trimesh_to_o3d(tm, default)
            if g is not None:
                _apply_scale(g, scale); out.append(g)
        elif isinstance(tm, trimesh.Scene):
            try:
                for name, geom in tm.geometry.items():
                    g = trimesh_to_o3d(geom, default)
                    if g is None:
                        continue
                    try:
                        T = tm.graph.get_transform(name)
                    except Exception:
                        T = np.eye(4)
                    g.transform(T)
                    _apply_scale(g, scale)
                    out.append(g)
            except Exception:
                # Fallback: baked meshes (if supported)
                try:
                    baked = tm.dump(concatenate=False)
                    for sub in baked:
                        g = trimesh_to_o3d(sub, default)
                        if g is not None:
                            _apply_scale(g, scale)
                            out.append(g)
                except Exception:
                    pass
    except Exception as e:
        sys.stderr.write(f"Warning: failed to load mesh '{mesh_path}': {e}\n")

    # If we loaded meshes but they still look gray and you have pycollada,
    # try to paint uniform diffuse per material (best-effort; no textures).
    if out:
        cols = _collada_extract_material_colors(mesh_path)
        if cols:
            for i, m in enumerate(out):
                # don't override explicit vertex colors
                if hasattr(m, "has_vertex_colors") and m.has_vertex_colors():
                    continue
                c = cols[min(i, len(cols)-1)]
                m.paint_uniform_color((float(c[0]), float(c[1]), float(c[2])))

    return out

def make_wireframe_box(size: np.ndarray, color=(1.0,0.0,0.0)) -> o3d.geometry.LineSet:
    hx, hy, hz = size/2.0
    pts = np.array([[-hx,-hy,-hz],[hx,-hy,-hz],[hx,hy,-hz],[-hx,hy,-hz],
                    [-hx,-hy,hz],[hx,-hy,hz],[hx,hy,hz],[-hx,hy,hz]], dtype=float)
    edges = [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]]
    ls = o3d.geometry.LineSet()
    ls.points = o3d.utility.Vector3dVector(pts)
    ls.lines  = o3d.utility.Vector2iVector(edges)
    ls.colors = o3d.utility.Vector3dVector([color]*len(edges))
    return ls

def make_world_grid(span=5.0, step=0.5, z=0.0, color=(0.80,0.80,0.80)) -> o3d.geometry.LineSet:
    xs = np.arange(-span, span + 1e-9, step)
    lines, pts = [], []
    for x in xs:
        pts.append([x,-span,z]); pts.append([x,span,z]); lines.append([len(pts)-2,len(pts)-1])
    for y in xs:
        pts.append([-span,y,z]); pts.append([span,y,z]); lines.append([len(pts)-2,len(pts)-1])
    ls = o3d.geometry.LineSet()
    ls.points = o3d.utility.Vector3dVector(np.array(pts, dtype=float))
    ls.lines  = o3d.utility.Vector2iVector(np.array(lines, dtype=np.int32))
    ls.colors = o3d.utility.Vector3dVector([color]*len(lines))
    return ls

# ---------------------------------------------------------------------
# drawables for a configuration
# ---------------------------------------------------------------------
def build_drawables(model: URDFModel, q: Dict[str,float]) -> Tuple[List[o3d.geometry.Geometry], List[o3d.geometry.Geometry]]:
    Tlink = model.fk(q)
    visuals: List[o3d.geometry.Geometry] = []
    collisions: List[o3d.geometry.Geometry] = []
    for lname, link in model.links.items():
        Tworld = Tlink.get(lname)
        if Tworld is None: continue
        for vg in link.visuals:
            meshes = load_meshes_as_o3d(vg.filename, vg.scale, default=(0.65,0.75,0.9))
            if not meshes and os.path.isfile(vg.filename):
                print(f"[viz] Loaded 0 meshes from: {vg.filename} (exists=True) — check format/colors")
            for m in meshes:
                m.transform(Tworld @ vg.origin_T); visuals.append(m)
        for cg in link.collision_meshes:
            meshes = load_meshes_as_o3d(cg.filename, cg.scale, default=(0.9,0.2,0.2))
            for m in meshes:
                m.transform(Tworld @ cg.origin_T)
                m.paint_uniform_color((0.9,0.2,0.2))
                collisions.append(m)
        for cb in link.collision_boxes:
            box = make_wireframe_box(cb.size, color=(1.0,0.0,0.0))
            box.transform(Tworld @ cb.origin_T); collisions.append(box)
    return visuals, collisions

def scene_aabb(geoms: List[o3d.geometry.Geometry]) -> Optional[o3d.geometry.AxisAlignedBoundingBox]:
    bb = None
    for g in geoms:
        try:
            gb = g.get_axis_aligned_bounding_box()
            bb = gb if bb is None else bb + gb
        except Exception:
            pass
    return bb

# ---------------------------------------------------------------------
# joints
# ---------------------------------------------------------------------
def joint_limits(model: URDFModel) -> Dict[str, Tuple[float,float,str]]:
    lims: Dict[str, Tuple[float,float,str]] = {}
    for jn, jd in model.joints.items():
        if jd.type in ("revolute","continuous"):
            lims[jn] = (jd.lower if jd.lower is not None else -math.pi,
                        jd.upper if jd.upper is not None else  math.pi,
                        jd.type)
        elif jd.type=="prismatic":
            lims[jn] = (jd.lower if jd.lower is not None else 0.0,
                        jd.upper if jd.upper is not None else 0.0,
                        jd.type)
    return lims

def zero_config(lims: Dict[str,Tuple[float,float,str]]) -> Dict[str,float]:
    return {k:0.0 for k in lims}

def random_config(lims: Dict[str,Tuple[float,float,str]]) -> Dict[str,float]:
    q = {}
    for k,(lo,hi,typ) in lims.items():
        q[k] = random.uniform(lo,hi) if typ in ("revolute","continuous","prismatic") else 0.0
    return q

# ---------------------------------------------------------------------
# viewer
# ---------------------------------------------------------------------
def run_viewer(urdf_path: str, grid_span: float):
    urdf_path = abspath(urdf_path)
    validate_file_exists(urdf_path)

    model = URDFModel(urdf_path); model.parse()
    lims = joint_limits(model); q = zero_config(lims)
    visuals, collisions = build_drawables(model, q)

    state = {
        "q": q, "lims": lims, "model": model,
        "visuals": visuals, "collisions": collisions,
        "show_visuals": True,
        "show_collisions": False,  # default OFF
        "show_axes": True,
        "show_grid": True,         # grid spans ±grid_span
        "should_close": False,
    }

    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window("viz_urdf (Open3D)", width=1280, height=800, visible=True)

    opt = vis.get_render_option()
    try:
        opt.background_color = np.array([0.96, 0.97, 0.99], dtype=np.float32)
        opt.mesh_show_back_face = True
        opt.line_width = 2.0
    except Exception:
        pass

    axes = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.4)
    grid = make_world_grid(span=grid_span, step=0.5, z=0.0, color=(0.80,0.80,0.80))

    # Establish bbox once (like pressing R)
    vis.clear_geometries()
    vis.add_geometry(grid, reset_bounding_box=True)  # seed bbox
    if state["show_axes"]:
        vis.add_geometry(axes, reset_bounding_box=False)
    if state["show_visuals"]:
        for g in state["visuals"]:
            vis.add_geometry(g, reset_bounding_box=False)
    if state["show_collisions"]:
        for g in state["collisions"]:
            vis.add_geometry(g, reset_bounding_box=False)

    vis.poll_events()
    vis.update_renderer()

    try:
        ctr = vis.get_view_control()
        ctr.reset_view_point(True)  # default Open3D placement
    except Exception:
        pass

    geoms = state["visuals"] if state["visuals"] else state["collisions"]
    print("\n→ Loaded:", urdf_path)
    print(f"   Visual geoms: {len(visuals)}  Collision geoms: {len(collisions)}")
    if geoms:
        bb = scene_aabb(geoms)
        if bb is not None:
            print(f"   AABB min {np.round(bb.get_min_bound(),3)}, max {np.round(bb.get_max_bound(),3)}")
    print("Controls: [v] visuals  [c] collisions  [a] axes  [g] grid  [l] reset  [j] randomize  [f] frame  [x] exit")
    print("Tip: press H in the window for Open3D camera help.")

    def refresh():
        vis.clear_geometries()
        if state["show_grid"]:
            vis.add_geometry(grid, reset_bounding_box=False)
        if state["show_axes"]:
            vis.add_geometry(axes, reset_bounding_box=False)
        if state["show_visuals"]:
            for gg in state["visuals"]:
                vis.add_geometry(gg, reset_bounding_box=False)
        if state["show_collisions"]:
            for gc in state["collisions"]:
                vis.add_geometry(gc, reset_bounding_box=False)
        vis.update_renderer()

    def rebuild(qmap: Dict[str,float]):
        V, C = build_drawables(state["model"], qmap)
        state["visuals"], state["collisions"] = V, C
        refresh()

    def frame_once():
        try:
            ctr = vis.get_view_control()
            ctr.reset_view_point(True)
            vis.update_renderer()
            print("→ Framed once.")
        except Exception:
            print("→ Frame: reset_view_point not available.")

    # callbacks
    def on_v(_): state["show_visuals"] = not state["show_visuals"]; refresh(); print("→ Visuals:", "ON" if state["show_visuals"] else "OFF"); return True
    def on_c(_): state["show_collisions"] = not state["show_collisions"]; refresh(); print("→ Collisions:", "ON" if state["show_collisions"] else "OFF"); return True
    def on_a(_): state["show_axes"] = not state["show_axes"]; refresh(); print("→ Axes:", "ON" if state["show_axes"] else "OFF"); return True
    def on_g(_): state["show_grid"] = not state["show_grid"]; refresh(); print("→ Grid:", "ON" if state["show_grid"] else "OFF"); return True
    def on_l(_): state["q"] = zero_config(state["lims"]); rebuild(state["q"]); print("→ Joints reset"); return True
    def on_j(_): state["q"] = random_config(state["lims"]); rebuild(state["q"]); print("→ Joints randomized"); return True
    def on_f(_): frame_once(); return True
    def on_x(_): state["should_close"] = True; return True

    for key, cb in [('v', on_v), ('V', on_v),
                    ('c', on_c), ('C', on_c),
                    ('a', on_a), ('A', on_a),
                    ('g', on_g), ('G', on_g),
                    ('l', on_l), ('L', on_l),
                    ('j', on_j), ('J', on_j),
                    ('f', on_f), ('F', on_f),
                    ('x', on_x), ('X', on_x)]:
        vis.register_key_callback(ord(key), cb)

    while True:
        if state["should_close"]:
            break
        if not vis.poll_events():
            break
        vis.update_renderer()

    vis.destroy_window()

# ---------------------------------------------------------------------
# main
# ---------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        prog="viz_urdf.py",
        description=DESCRIPTION + "\n" + USAGE_EXAMPLES,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-p","--path", required=True, metavar="ROBOT.urdf",
                        help="Path to the input URDF (.dae/.obj/.stl visuals supported)")
    parser.add_argument("-g","--grid-size", type=float, default=5.0, metavar="M",
                        help="Grid half-span in meters (grid spans ±M). Cells are 0.5 m. Default: 5.0")
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr); sys.exit(0)
    args = parser.parse_args()
    run_viewer(args.path, grid_span=max(0.5, float(args.grid_size)))

if __name__ == "__main__":
    main()

