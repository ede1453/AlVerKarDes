from collections import Counter

from fastapi.routing import APIRoute

from app.main import app


def main():
    route_pairs = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        for method in route.methods or []:
            if method in {"HEAD", "OPTIONS"}:
                continue
            route_pairs.append((method, route.path))

    duplicates = [
        {"method": method, "path": path, "count": count}
        for (method, path), count in Counter(route_pairs).items()
        if count > 1
    ]

    if duplicates:
        print("Duplicate API routes detected:")
        for item in duplicates:
            print(f"{item['method']} {item['path']} count={item['count']}")
        raise SystemExit(1)

    operation_ids = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if route.operation_id:
            operation_ids.append(route.operation_id)

    duplicate_operation_ids = [
        {"operation_id": operation_id, "count": count}
        for operation_id, count in Counter(operation_ids).items()
        if count > 1
    ]

    if duplicate_operation_ids:
        print("Duplicate explicit operation IDs detected:")
        for item in duplicate_operation_ids:
            print(f"{item['operation_id']} count={item['count']}")
        raise SystemExit(1)

    print("OpenAPI/router uniqueness check passed.")


if __name__ == "__main__":
    main()
