from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/admin/import")

UPLOAD_DIR = Path("/tmp/aici_imports")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_feed(file: UploadFile = File(...)):
    suffix = file.filename.split(".")[-1] if file.filename and "." in file.filename else "dat"
    file_id = str(uuid4())
    path = UPLOAD_DIR / f"{file_id}.{suffix}"

    with path.open("wb") as buffer:
        buffer.write(await file.read())

    return {"file_id": file_id, "stored_path": str(path), "status": "uploaded"}
