# %% Imports and fixed Jupytext format
"""Export inputs with Jupytext py:hydrogen; preserve source except CRLF/CR to LF."""

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path


HYDROGEN_FORMAT = {
    "extension": ".py",
    "format_name": "hydrogen",
    "comment_magics": False,
    "cell_metadata_filter": "-all",
    "notebook_metadata_filter": "-all",
}


def _jupytext():
    try:
        import jupytext
        from nbformat import NotebookNode
    except ImportError as error:
        raise ValueError("Jupytext is required in the selected Python environment; "
                         "check existing environments before installing dependencies.") from error
    return jupytext, NotebookNode


# %% Input validation and text rendering
def source_text(cell):
    """Return the exact source string defined by the notebook file format."""
    if "source" not in cell:
        raise ValueError("A cell is missing its source field.")
    source = cell["source"]
    if isinstance(source, str):
        return source
    if isinstance(source, list) and all(isinstance(part, str) for part in source):
        return "".join(source)
    raise ValueError("Cell source must be a string or a list of strings.")


def _cells(notebook):
    if not isinstance(notebook, dict) or notebook.get("nbformat") != 4:
        raise ValueError("Only nbformat 4 notebooks are supported.")
    cells = notebook.get("cells")
    if not isinstance(cells, list):
        raise ValueError("Notebook cells must be a list.")
    metadata = notebook.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("Notebook metadata must be an object.")
    declared_python = False
    for key, language_key in (("language_info", "name"), ("kernelspec", "language")):
        section = metadata.get(key, {})
        if not isinstance(section, dict):
            raise ValueError("Notebook language metadata must be an object.")
        language = section.get(language_key, "")
        if not isinstance(language, str):
            raise ValueError("Notebook language metadata must contain strings.")
        if language and not language.lower().startswith(("python", "ipython")):
            raise ValueError("The notebook declares a non-Python language.")
        declared_python = declared_python or bool(language)
    kernel_name = metadata.get("kernelspec", {}).get("name", "")
    if not declared_python and isinstance(kernel_name, str) and (
        kernel_name.lower() in ("ir", "r")
        or kernel_name.lower().startswith(
            ("julia", "r-", "bash", "javascript", "scala", "ruby", "octave", "matlab")
        )
    ):
        raise ValueError("The notebook declares a known non-Python kernel.")
    for index, cell in enumerate(cells, 1):
        if not isinstance(cell, dict) or cell.get("cell_type") not in ("code", "markdown", "raw"):
            raise ValueError("Unsupported cell type at cell {}.".format(index))
        source_text(cell)
    return cells


def normalize_newlines(source):
    """Only the line-ending changes explicitly accepted by the user."""
    return source.replace("\r\n", "\n").replace("\r", "\n")


def _verify_rendered(cells, text):
    """Account for every output character using original cell lengths, not splitting markers."""
    cursor = 0
    for index, cell in enumerate(cells, 1):
        kind = cell["cell_type"]
        suffix = "" if kind == "code" else " [" + kind + "]"
        marker = re.match(r"[ \t]*" + re.escape("# %%" + suffix) + r"\n", text[cursor:])
        if marker is None:
            raise ValueError("Unexpected Jupytext cell marker at cell {}.".format(index))
        cursor += marker.end()
        source = normalize_newlines(source_text(cell))
        expected = source if kind == "code" else "\n".join(
            "# " + line if line else "#" for line in source.split("\n")
        )
        if text[cursor:cursor + len(expected)] != expected:
            raise ValueError("Jupytext changed source beyond CRLF/CR normalization at cell {}; "
                             "no output was written.".format(index))
        cursor += len(expected)
        while cursor < len(text) and text[cursor] == "\n":
            cursor += 1
    if cursor != len(text):
        raise ValueError("Unexpected content outside original cell sources; no output was written.")


def _render(notebook):
    """Use the public Jupytext writer, then verify all source and discarded-payload boundaries."""
    cells = _cells(notebook)
    jupytext, NotebookNode = _jupytext()
    clean_cells = []
    for cell in cells:
        clean = NotebookNode(cell_type=cell["cell_type"],
                             source=normalize_newlines(source_text(cell)), metadata={})
        if cell["cell_type"] == "code":
            clean.update(execution_count=None, outputs=[])
        clean_cells.append(clean)
    # Do not let notebook options, language/active metadata, or image payloads alter export.
    clean_notebook = NotebookNode(nbformat=4, nbformat_minor=5, metadata={}, cells=clean_cells)
    text = jupytext.writes(clean_notebook, fmt=dict(HYDROGEN_FORMAT))
    _verify_rendered(cells, text)
    return text.encode("utf-8")


def render_notebook(notebook):
    """Return verified Hydrogen text; Markdown/raw have typed comment markers."""
    return _render(notebook).decode("utf-8")


# %% Non-executing conversion and preservation report
def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _warnings(notebook, cells):
    warnings = []
    metadata = notebook.get("metadata", {})
    if not (metadata.get("language_info", {}).get("name")
            or metadata.get("kernelspec", {}).get("language")):
        warnings.append("No explicit kernel language was supplied; source was preserved as given.")
    if any(line.lstrip().startswith(("%", "!"))
           for cell in cells if cell["cell_type"] == "code"
           for line in source_text(cell).splitlines()):
        warnings.append("Magic/shell syntax was preserved. Run by cell in IPython/Jupyter; "
                        "%%bash requires a working Bash executable, and ! uses the host shell.")
    if any(line.startswith("# %%") for cell in cells
           for line in source_text(cell).splitlines()):
        warnings.append("Existing percent markers were retained; editor cell boundaries may differ.")
    return warnings


def convert_notebook(input_path, output_path):
    """Write a new .py file; never overwrite input or an existing output."""
    input_path = Path(input_path).resolve()
    output_path = Path(output_path).resolve()
    if input_path == output_path:
        raise ValueError("Input and output paths must differ.")
    if input_path.suffix.lower() != ".ipynb":
        raise ValueError("Input filename must have the .ipynb extension.")
    if output_path.suffix.lower() != ".py":
        raise ValueError("Output filename must have the .py extension.")
    if output_path.exists():
        raise FileExistsError("Output already exists; select a new output filename.")
    if not output_path.parent.is_dir():
        raise FileNotFoundError("Output parent directory does not exist.")
    original = input_path.read_bytes()
    notebook = json.loads(original.decode("utf-8-sig"))
    cells = _cells(notebook)
    rendered = _render(notebook)
    original_hash = _sha256(original)
    counts = collections.Counter(cell["cell_type"] for cell in cells)
    outputs = [item for cell in cells if isinstance(cell.get("outputs"), list)
               for item in cell["outputs"]]
    report = {
        "converter": "jupytext",
        "format": "py:hydrogen",
        "jupytext_version": _jupytext()[0].__version__,
        "line_endings": "LF",
        "source_preservation": "exact after CRLF/CR to LF normalization",
        "entire_output_verified": True,
        "input": str(input_path),
        "output": str(output_path),
        "input_sha256": original_hash,
        "output_sha256": _sha256(rendered),
        "input_unchanged": True,
        "input_bytes": len(original),
        "output_bytes": len(rendered),
        "cell_counts": dict(counts),
        "code_cells_preserved": counts["code"],
        "markdown_cells_commented": counts["markdown"],
        "raw_cells_commented": counts["raw"],
        "inserted_percent_markers": len(cells),
        "discarded_outputs": len(outputs),
        "discarded_image_output_bundles": sum(
            isinstance(item, dict) and isinstance(item.get("data"), dict)
            and any(key.startswith("image/") for key in item["data"])
            for item in outputs
        ),
        "discarded_attachments": sum(len(cell["attachments"]) for cell in cells
                                     if isinstance(cell.get("attachments"), dict)),
        "warnings": _warnings(notebook, cells),
    }
    if _sha256(input_path.read_bytes()) != original_hash:
        raise ValueError("Input changed during conversion; no output was written.")
    with output_path.open("xb") as handle:
        handle.write(rendered)
    if output_path.read_bytes() != rendered:
        raise OSError("Output verification failed.")
    if _sha256(input_path.read_bytes()) != original_hash:
        raise ValueError("Input changed while writing; the new output reflects the initial input.")
    return report


# %% Command-line entry point (does not run notebook code)
def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Source .ipynb (read only)")
    parser.add_argument("output", type=Path, help="New .py file in an existing directory")
    args = parser.parse_args(argv)
    try:
        report = convert_notebook(args.input, args.output)
    except (OSError, ValueError, TypeError) as error:
        print("Conversion failed: {}".format(error), file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
