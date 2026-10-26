# [FL_INDEX: keywords="code_concat, context_packer, token_counter, llm_context, zero_api" | purpose="Autonomous repository concatenation and LLM context packing engine"]
"""
Code Concat Engine - Pure Local Python (Zero Third-Party APIs)
Adopts jub0t/concat architecture natively for Flowork OS.
Concatenates source repositories, builds tree hierarchy, filters binaries/ignored paths,
and outputs token-estimated bundles in Markdown, XML, or Plain text.
"""

import os
import sys
import json
import fnmatch

IGNORE_PATTERNS = {
    ".git", ".svn", ".hg", "__pycache__", "node_modules", "target", "dist",
    "build", ".venv", "venv", ".idea", ".vscode", ".next", ".nuxt", ".FL_BIN",
    "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dll", "*.dylib", "*.exe", "*.bin",
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.ico", "*.pdf", "*.zip", "*.tar",
    "*.gz", "*.7z", "*.mp4", "*.mp3", "*.wav", "*.ogg", "*.flac", "*.woff",
    "*.woff2", "*.ttf", "*.eot", "*.lock", "package-lock.json", "yarn.lock"
}

def is_ignored(path, base_path):
    rel_path = os.path.relpath(path, base_path)
    parts = rel_path.split(os.sep)
    for part in parts:
        for pat in IGNORE_PATTERNS:
            if fnmatch.fnmatch(part, pat):
                return True
    return False

def is_binary(file_path):
    try:
        with open(file_path, "tr") as check_file:
            check_file.read(512)
            return False
    except UnicodeDecodeError:
        return True
    except Exception:
        return True

def generate_ascii_tree(dir_path, base_path=None, prefix=""):
    if base_path is None:
        base_path = dir_path
    
    entries = []
    try:
        raw_entries = sorted(os.listdir(dir_path))
    except Exception as e:
        return f"[Error accessing directory: {e}]\n"

    for entry in raw_entries:
        full = os.path.join(dir_path, entry)
        if not is_ignored(full, base_path):
            entries.append(entry)

    tree_str = ""
    for index, entry in enumerate(entries):
        full = os.path.join(dir_path, entry)
        is_last = (index == len(entries) - 1)
        connector = "└── " if is_last else "├── "
        tree_str += f"{prefix}{connector}{entry}\n"
        if os.path.isdir(full):
            sub_prefix = prefix + ("    " if is_last else "│   ")
            tree_str += generate_ascii_tree(full, base_path, sub_prefix)
    return tree_str

def estimate_tokens(text):
    # Rule of thumb for standard subword tokenizers (approx 3.8 - 4 characters per token)
    return max(1, len(text) // 4)

def process_concat(target_path, output_format="markdown", include_tree=True):
    if not os.path.exists(target_path):
        return {"success": False, "error": f"Path not found: {target_path}"}

    target_path = os.path.abspath(target_path)
    base_name = os.path.basename(target_path)
    
    collected_files = []
    if os.path.isfile(target_path):
        collected_files.append(target_path)
        base_dir = os.path.dirname(target_path)
    else:
        base_dir = target_path
        for root, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d), base_dir)]
            for file in sorted(files):
                full_path = os.path.join(root, file)
                if not is_ignored(full_path, base_dir) and not is_binary(full_path):
                    collected_files.append(full_path)

    output_lines = []
    
    if output_format == "xml":
        output_lines.append("<repository>")
        output_lines.append(f"  <name>{base_name}</name>")
        output_lines.append(f"  <total_files>{len(collected_files)}</total_files>")
        if include_tree and os.path.isdir(target_path):
            output_lines.append("  <structure>")
            output_lines.append(f"<![CDATA[\n{generate_ascii_tree(target_path)}]]>")
            output_lines.append("  </structure>")
        output_lines.append("  <files>")
        for fpath in collected_files:
            rel = os.path.relpath(fpath, base_dir)
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                output_lines.append(f'    <file path="{rel}">')
                output_lines.append(f"<![CDATA[\n{content}\n]]>")
                output_lines.append("    </file>")
            except Exception as e:
                output_lines.append(f'    <file path="{rel}" error="{str(e)}" />')
        output_lines.append("  </files>")
        output_lines.append("</repository>")
    else:  # markdown default
        output_lines.append(f"# Codebase Context: `{base_name}`")
        output_lines.append(f"Total Files Packed: {len(collected_files)}\n")
        if include_tree and os.path.isdir(target_path):
            output_lines.append("## Repository Tree Structure\n```text")
            output_lines.append(f"{base_name}/")
            output_lines.append(generate_ascii_tree(target_path).rstrip())
            output_lines.append("```\n")
        output_lines.append("## File Manifest & Source Code\n")
        for fpath in collected_files:
            rel = os.path.relpath(fpath, base_dir)
            ext = os.path.splitext(fpath)[1].lstrip(".") or "txt"
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                output_lines.append(f"### File: `{rel}`\n```{ext}")
                output_lines.append(content)
                output_lines.append("```\n")
            except Exception as e:
                output_lines.append(f"### File: `{rel}` (Error: {e})\n")

    full_output = "\n".join(output_lines)
    tokens = estimate_tokens(full_output)
    
    return {
        "success": True,
        "base_path": target_path,
        "files_packed": len(collected_files),
        "estimated_tokens": tokens,
        "output_chars": len(full_output),
        "content": full_output
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: concat_engine.py <target_path> [format] [output_file]"}))
        sys.exit(1)
        
    t_path = sys.argv[1]
    fmt = sys.argv[2] if len(sys.argv) > 2 else "markdown"
    out_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    res = process_concat(t_path, output_format=fmt)
    if not res.get("success"):
        print(json.dumps(res))
        sys.exit(1)
        
    if out_file:
        try:
            with open(out_file, "w", encoding="utf-8") as out:
                out.write(res["content"])
            res["saved_to"] = out_file
            del res["content"] # do not dump huge output to stdout if saved
        except Exception as e:
            res["file_save_error"] = str(e)
            
    print(json.dumps(res, indent=2))
