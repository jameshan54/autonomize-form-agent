"""Identify supplied PNG files without reading or inferring form content."""

import hashlib
import re
import struct
from pathlib import Path
from uuid import UUID

from .models import DocumentIdentity, require

NAME = re.compile(r"^(?P<uuid>[0-9a-fA-F-]{36})_TX_page_(?P<page>[1-9][0-9]*)\.png$")


def identify(path, root, printed_page=None):
    path, root = Path(path), Path(root)
    content = path.read_bytes()
    require(content[:8] == b"\x89PNG\r\n\x1a\n" and content[12:16] == b"IHDR"
            and len(content) >= 33, "Expected PNG with IHDR")
    width, height = struct.unpack(">II", content[16:24])
    digest = hashlib.sha256(content).hexdigest()
    match = NAME.fullmatch(path.name)
    return DocumentIdentity(
        document_id="sha256:" + digest,
        source_path=path.resolve().relative_to(root.resolve()).as_posix(),
        filename=path.name, sha256=digest, width=width, height=height,
        supplied_uuid=str(UUID(match["uuid"])) if match else None,
        filename_page=int(match["page"]) if match else None,
        printed_page=printed_page,
    )


def inventory(directory, root, printed_pages=None):
    """Keep each supplied file separate; reject duplicates instead of silently merging."""
    printed_pages = printed_pages or {}
    paths = sorted(Path(directory).glob("*.png"))
    require(bool(paths), "No PNG inputs")
    require(set(printed_pages) <= {p.name for p in paths}, "Unknown printed-page source")
    documents = [identify(p, root, printed_pages.get(p.name)) for p in paths]
    require(len({d.document_id for d in documents}) == len(documents), "Duplicate image content")
    return documents
