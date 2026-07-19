from __future__ import annotations

import re
from pathlib import Path

ROUTER_FILE = Path("app/api/v1/router.py")

TARGETS = {
    "marketplace_connectors_router": (
        "app.api.v1.marketplace_connectors_router",
        "from app.api.v1.marketplace_connectors_router "
        "import router as marketplace_connectors_router",
    ),
    "amazon_connector_router": (
        "app.api.v1.amazon_connector_router",
        "from app.api.v1.amazon_connector_router "
        "import router as amazon_connector_router",
    ),
}


def remove_import_blocks(
    lines: list[str],
    module_name: str,
    alias: str,
) -> list[str]:
    output: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith(f"from {module_name} import"):
            block = [line]
            index += 1

            if "(" in line and ")" not in line:
                while index < len(lines):
                    block.append(lines[index])
                    index += 1
                    if ")" in block[-1]:
                        break

            if alias in "".join(block):
                continue

            output.extend(block)
            continue

        if (
            " import router as " in stripped
            and stripped.endswith(alias)
        ):
            index += 1
            continue

        output.append(line)
        index += 1

    return output


def remove_include_blocks(
    lines: list[str],
    alias: str,
) -> list[str]:
    output: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith(
            f"api_router.include_router({alias}"
        ):
            index += 1
            continue

        if stripped == "api_router.include_router(":
            block = [line]
            index += 1

            while index < len(lines):
                block.append(lines[index])
                index += 1
                if ")" in block[-1]:
                    break

            if alias in "".join(block):
                continue

            output.extend(block)
            continue

        output.append(line)
        index += 1

    return output


def insert_import(
    lines: list[str],
    import_line: str,
) -> list[str]:
    router_declaration = next(
        (
            index
            for index, line in enumerate(lines)
            if line.startswith("api_router = APIRouter")
        ),
        len(lines),
    )

    lines.insert(router_declaration, import_line)
    return lines


def insert_include(
    lines: list[str],
    alias: str,
) -> list[str]:
    include_indexes = [
        index
        for index, line in enumerate(lines)
        if line.strip().startswith(
            "api_router.include_router"
        )
    ]

    insertion_index = (
        include_indexes[-1] + 1
        if include_indexes
        else len(lines)
    )

    lines.insert(
        insertion_index,
        f"api_router.include_router({alias})",
    )
    return lines


def main() -> None:
    if not ROUTER_FILE.exists():
        raise SystemExit(
            f"Missing central router: {ROUTER_FILE}"
        )

    lines = ROUTER_FILE.read_text(
        encoding="utf-8"
    ).splitlines()

    for alias, (module_name, _) in TARGETS.items():
        lines = remove_import_blocks(
            lines,
            module_name,
            alias,
        )
        lines = remove_include_blocks(
            lines,
            alias,
        )

    for alias, (_, import_line) in TARGETS.items():
        lines = insert_import(
            lines,
            import_line,
        )
        lines = insert_include(
            lines,
            alias,
        )

    text = "\n".join(lines).rstrip() + "\n"

    ROUTER_FILE.write_text(
        text,
        encoding="utf-8",
    )

    for alias in TARGETS:
        import_count = text.count(
            f"router as {alias}"
        )
        include_count = len(
            re.findall(
                rf"api_router\.include_router\(\s*{alias}\s*\)",
                text,
            )
        )

        if import_count != 1:
            raise SystemExit(
                f"{alias} import count={import_count}; expected=1"
            )

        if include_count != 1:
            raise SystemExit(
                f"{alias} include count={include_count}; expected=1"
            )

    print(
        "Connector router registration cleanup passed."
    )


if __name__ == "__main__":
    main()
