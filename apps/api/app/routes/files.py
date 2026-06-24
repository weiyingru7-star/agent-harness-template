import re

from fastapi import APIRouter, HTTPException, Request, status

from app.models.file import UploadedFile
from app.services.file_store import file_store


router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", response_model=UploadedFile, status_code=status.HTTP_201_CREATED)
async def upload_file(request: Request) -> UploadedFile:
    try:
        filename, content_type, content = await _read_single_file_upload(request)
        return file_store.save_file(
            filename=filename,
            content_type=content_type,
            content=content,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be valid UTF-8 text",
        ) from exc


@router.get("/{file_id}", response_model=UploadedFile)
def get_file(file_id: str) -> UploadedFile:
    uploaded_file = file_store.get_file(file_id)
    if uploaded_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return uploaded_file


async def _read_single_file_upload(request: Request) -> tuple[str, str, bytes]:
    content_type_header = request.headers.get("content-type", "")
    boundary_match = re.search(r"boundary=([^;]+)", content_type_header)
    if "multipart/form-data" not in content_type_header or boundary_match is None:
        raise ValueError("Expected multipart/form-data with a file field")

    boundary = boundary_match.group(1).strip('"')
    body = await request.body()
    delimiter = f"--{boundary}".encode("utf-8")

    for part in body.split(delimiter):
        part = part.strip(b"\r\n")
        if not part or part == b"--" or b"\r\n\r\n" not in part:
            continue

        raw_headers, content = part.split(b"\r\n\r\n", 1)
        content = content.removesuffix(b"\r\n--").removesuffix(b"\r\n")
        headers = raw_headers.decode("utf-8", errors="replace")
        if 'name="file"' not in headers:
            continue

        filename_match = re.search(r'filename="([^"]+)"', headers)
        if filename_match is None:
            raise ValueError("Uploaded file must include a filename")

        part_content_type = "text/plain"
        for header_line in headers.split("\r\n"):
            if header_line.lower().startswith("content-type:"):
                part_content_type = header_line.split(":", 1)[1].strip()
                break

        return filename_match.group(1), part_content_type, content

    raise ValueError("Missing file field")
