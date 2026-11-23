"""Static AST gate enforcing native Blender 5.2.3 LTS APIs across repository scripts."""
import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKIP_PARTS = {".git", ".venv", "__pycache__", "node_modules"}
BSDF_V2_GUARD_SOCKETS = {
    "Subsurface Weight", "Subsurface Scale", "Specular IOR Level",
    "Anisotropic", "Thickness", "Sheen Tint", "Coat Weight",
    "Sheen Weight", "Transmission Weight", "Subsurface", "Specular", "Clearcoat",
}
SHIM_GETATTR_NAMES = {
    "use_nodes", "blend_method", "shadow_method",
    "fcurves", "channelbag", "channelbags", "layers",
}


def _iter_python_files():
    return sorted(p for p in REPO_ROOT.rglob("*.py") if not (SKIP_PARTS & set(p.parts)))


def _imports_bpy(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(a.name == "bpy" or a.name.startswith("bpy.") for a in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module and (node.module == "bpy" or node.module.startswith("bpy.")):
            return True
    return False


def find_blender_5_2_violations(source: str, filename: str = "<script>") -> list[str]:
    tree = ast.parse(source, filename=filename)
    cb_vars = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.For) and isinstance(node.target, ast.Name)
                and isinstance(node.iter, ast.Attribute) and node.iter.attr == "channelbags"):
            cb_vars.add(node.target.id)
        elif (isinstance(node, ast.Assign) and isinstance(node.value, ast.Subscript)
              and isinstance(node.value.value, ast.Attribute) and node.value.value.attr == "channelbags"):
            cb_vars.update(t.id for t in node.targets if isinstance(t, ast.Name))

    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if node.attr == "use_nodes":
                issues.append(f"{filename}:{node.lineno}: deprecated .use_nodes access")
            elif node.attr in {"blend_method", "shadow_method"}:
                issues.append(f"{filename}:{node.lineno}: removed Material.{node.attr}")
            elif node.attr == "channelbag":
                issues.append(f"{filename}:{node.lineno}: pre-5.0 .channelbag shim")
            elif node.attr == "fcurves":
                is_cb = ((isinstance(node.value, ast.Name) and node.value.id in cb_vars)
                         or (isinstance(node.value, ast.Subscript)
                             and isinstance(node.value.value, ast.Attribute)
                             and node.value.value.attr == "channelbags"))
                if not is_cb:
                    issues.append(f"{filename}:{node.lineno}: pre-5.0 Action.fcurves access")
        elif isinstance(node, ast.Constant) and node.value == "BLENDER_EEVEE_NEXT":
            issues.append(f"{filename}:{node.lineno}: removed BLENDER_EEVEE_NEXT engine")
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
              and node.func.id in {"getattr", "hasattr"} and len(node.args) >= 2
              and isinstance(node.args[1], ast.Constant) and node.args[1].value in SHIM_GETATTR_NAMES):
            issues.append(f"{filename}:{node.lineno}: pre-5.0 {node.func.id}(..., {node.args[1].value!r}) shim")
        elif isinstance(node, ast.Compare) and isinstance(node.left, ast.Constant) and node.left.value in BSDF_V2_GUARD_SOCKETS:
            if any(isinstance(op, (ast.In, ast.NotIn)) and isinstance(c, ast.Attribute) and c.attr == "inputs"
                   for op, c in zip(node.ops, node.comparators)):
                issues.append(f"{filename}:{node.lineno}: pre-4.0 Principled BSDF socket guard {node.left.value!r}")
        elif isinstance(node, ast.Try):
            for sub in ast.walk(node):
                if (isinstance(sub, ast.Subscript) and isinstance(sub.value, ast.Attribute)
                        and sub.value.attr == "inputs" and isinstance(sub.slice, ast.Constant)
                        and sub.slice.value in BSDF_V2_GUARD_SOCKETS):
                    issues.append(f"{filename}:{node.lineno}: pre-4.0 Principled BSDF try/except shim {sub.slice.value!r}")
    return issues


def test_all_python_files_parse_and_have_zero_use_nodes():
    files = _iter_python_files()
    assert len(files) >= 388
    use_nodes_hits = []
    for path in files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        use_nodes_hits.extend(
            f"{rel}:{n.lineno}" for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == "use_nodes"
        )
    assert use_nodes_hits == []


def test_all_blender_scripts_use_native_5_2_apis():
    bpy_scripts = 0
    violations = []
    for path in _iter_python_files():
        source = path.read_text(encoding="utf-8")
        rel = path.relative_to(REPO_ROOT).as_posix()
        if _imports_bpy(ast.parse(source, filename=rel)):
            bpy_scripts += 1
            violations.extend(find_blender_5_2_violations(source, rel))
    assert bpy_scripts >= 228
    assert violations == []


def test_ast_gate_rejects_deprecated_fixtures():
    bad_fixtures = [
        "import bpy\nbpy.data.materials.new('M').use_nodes = True\n",
        "import bpy\n_ = mat.use_nodes\n",
        "import bpy\nscene.render.engine = 'BLENDER_EEVEE_NEXT'\n",
        "import bpy\nmat.blend_method = 'HASHED'\n",
        "import bpy\nfcs = list(act.fcurves)\n",
        "import bpy\ncbs = getattr(strip, 'channelbags', [])\n",
        "import bpy\nif 'Specular IOR Level' in bsdf.inputs:\n    pass\n",
    ]
    for snippet in bad_fixtures:
        assert find_blender_5_2_violations(snippet), f"Expected violation for:\n{snippet}"

    clean = (
        "import bpy\n"
        "scene.render.engine = 'BLENDER_EEVEE'\n"
        "scene.render.use_compositing = False\n"
        "if mat.node_tree:\n"
        "    bsdf = mat.node_tree.nodes['Principled BSDF']\n"
        "for layer in act.layers:\n"
        "    for strip in layer.strips:\n"
        "        for cb in strip.channelbags:\n"
        "            _ = list(cb.fcurves)\n"
    )
    assert find_blender_5_2_violations(clean) == []
