import ast
from pathlib import Path

VERSIONS_DIR = Path("alembic/versions")


def _read_revision_metadata(path: Path) -> tuple[str, str | None]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    revision = None
    down_revision = None

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"revision", "down_revision"}:
                    value = ast.literal_eval(node.value)
                    if target.id == "revision":
                        revision = value
                    else:
                        down_revision = value

    if not revision:
        raise AssertionError(f"Missing revision in {path}")

    if isinstance(down_revision, (tuple, list)):
        raise AssertionError(f"Merge/branch down_revision is not allowed in {path}: {down_revision}")

    return revision, down_revision


def check_linear_history(versions_dir: Path = VERSIONS_DIR) -> dict:
    files = sorted(versions_dir.glob("*.py"))

    revisions = {}
    down_revisions = {}

    for path in files:
        revision, down_revision = _read_revision_metadata(path)
        if revision in revisions:
            raise AssertionError(f"Duplicate Alembic revision: {revision}")
        revisions[revision] = path
        down_revisions[revision] = down_revision

    referenced = {value for value in down_revisions.values() if value is not None}
    heads = sorted(set(revisions) - referenced)

    if len(heads) != 1:
        raise AssertionError(f"Expected exactly one Alembic head, found {heads}")

    for revision, down_revision in down_revisions.items():
        if down_revision is not None and down_revision not in revisions:
            raise AssertionError(
                f"Revision {revision} references missing down_revision {down_revision}"
            )

    return {
        "revision_count": len(revisions),
        "head": heads[0],
    }


if __name__ == "__main__":
    result = check_linear_history()
    print(f"Alembic linear history check passed. Head: {result['head']}. Revisions: {result['revision_count']}.")
