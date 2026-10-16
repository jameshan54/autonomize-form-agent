"""UI-independent, JSON-serializable contracts; no extraction or answer generation."""

import json
import re
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Dict, List, Literal, Optional, Union, get_args, get_origin, get_type_hints

SCHEMA_VERSION = "1.0"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decode(cls, value):
    """Strictly decode nested contracts without coercing identifiers or booleans."""
    origin, args = get_origin(cls), get_args(cls)
    if origin is Union:
        for option in args:
            try:
                return decode(option, value)
            except (ValueError, TypeError):
                pass
        raise ValueError("Value does not match union")
    if origin is Literal:
        require(value in args and type(value) is type(args[0]), "Invalid literal")
        return value
    if origin is list:
        require(type(value) is list, "Expected list")
        return [decode(args[0], item) for item in value]
    if origin is dict:
        require(type(value) is dict, "Expected object")
        return {decode(args[0], k): decode(args[1], v) for k, v in value.items()}
    if is_dataclass(cls):
        require(type(value) is dict, "Expected contract object")
        hints = get_type_hints(cls)
        require(not set(value) - set(hints), "Unknown contract keys")
        try:
            result = cls(**{k: decode(hints[k], v) for k, v in value.items()})
        except TypeError as exc:
            raise ValueError("Missing required contract keys") from exc
        return result
    require(type(value) is cls, "Incorrect scalar type")
    return value


class Contract:
    def to_dict(self):
        value = asdict(self)
        decode(type(self), value)
        return value

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False, allow_nan=False)

    @classmethod
    def from_json(cls, value):
        return decode(cls, json.loads(value))


@dataclass
class PrintedPage(Contract):
    text: str
    number: int
    total: int
    method: Literal["visual_source_review"] = "visual_source_review"

    def __post_init__(self):
        require(1 <= self.number <= self.total, "Invalid printed page")
        require(bool(self.text.strip()), "Printed page needs source text")


@dataclass
class DocumentIdentity(Contract):
    document_id: str
    source_path: str
    filename: str
    sha256: str
    width: int
    height: int
    supplied_uuid: Optional[str] = None
    filename_page: Optional[int] = None
    image_index: int = 1
    printed_page: Optional[PrintedPage] = None

    def __post_init__(self):
        require(bool(re.fullmatch(r"[0-9a-f]{64}", self.sha256)), "Invalid SHA-256")
        require(self.document_id == "sha256:" + self.sha256, "Identity/hash mismatch")
        require(self.width > 0 and self.height > 0, "Invalid dimensions")
        require(self.image_index == 1, "Only individual supplied images are supported")
        require(self.filename_page is None or self.filename_page > 0, "Invalid filename page")
        require(self.source_path.split("/")[-1] == self.filename, "Source filename mismatch")


@dataclass
class Evidence(Contract):
    evidence_id: str
    document_id: str
    filename: str
    image_index: int
    section: str
    field: str
    source_text: Optional[str]
    observation: str
    table: Optional[str] = None
    row: Optional[int] = None

    def __post_init__(self):
        require(all(x.strip() for x in (self.evidence_id, self.section, self.field, self.observation)),
                "Evidence needs a location and visual observation")
        require(self.image_index == 1, "Invalid image index")
        require((self.table is None) == (self.row is None), "Table and row must occur together")
        require(self.row is None or self.row > 0, "Rows are one-based")


@dataclass
class Value(Contract):
    state: Literal["readable", "blank", "unreadable", "checked", "unchecked", "not_present"]
    source_text: Optional[str]
    normalized: Optional[Union[str, int, float, bool]] = None
    evidence_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        require(bool(self.evidence_ids), "Values require evidence")
        if self.state == "blank":
            require(self.source_text == "" and self.normalized is None, "Blank value must be empty")
        if self.state in ("unreadable", "not_present"):
            require(self.normalized is None, "Missing/unreadable values cannot be normalized")
        if self.state in ("readable", "checked", "unchecked"):
            require(bool(self.source_text), "Readable values need source text")
        if self.state in ("checked", "unchecked"):
            require(self.normalized is (self.state == "checked"), "Checkbox state mismatch")


@dataclass
class TableRow(Contract):
    row: int
    cells: Dict[str, Value]

    def __post_init__(self):
        require(self.row > 0 and bool(self.cells), "Invalid table row")


@dataclass
class Table(Contract):
    table_id: str
    section: str
    rows: List[TableRow]

    def __post_init__(self):
        require(len({r.row for r in self.rows}) == len(self.rows), "Duplicate table row")


@dataclass
class Document(Contract):
    identity: DocumentIdentity
    evidence: List[Evidence]
    fields: Dict[str, Value] = field(default_factory=dict)
    tables: List[Table] = field(default_factory=list)
    section_text: Dict[str, Value] = field(default_factory=dict)
    schema_version: Literal["1.0"] = SCHEMA_VERSION

    def __post_init__(self):
        refs = {e.evidence_id: e for e in self.evidence}
        require(len(refs) == len(self.evidence), "Duplicate evidence ID")
        require(len({t.table_id for t in self.tables}) == len(self.tables), "Duplicate table ID")
        for e in self.evidence:
            require((e.document_id, e.filename, e.image_index) ==
                    (self.identity.document_id, self.identity.filename, self.identity.image_index),
                    "Evidence belongs to another document")
        for value in list(self.fields.values()) + list(self.section_text.values()):
            require(set(value.evidence_ids) <= refs.keys(), "Unresolved evidence")
        for table in self.tables:
            for row in table.rows:
                for key, value in row.cells.items():
                    require(set(value.evidence_ids) <= refs.keys(), "Unresolved cell evidence")
                    for ref in value.evidence_ids:
                        e = refs[ref]
                        require((e.table, e.row, e.field, e.section) ==
                                (table.table_id, row.row, key, table.section), "Cell evidence mismatch")


@dataclass
class Answer(Contract):
    """An answer envelope only; this class does not implement QA."""
    question: str
    text: str
    status: Literal["answered", "missing", "unreadable", "partial"]
    selected_document_ids: List[str]
    evidence: List[Evidence]
    schema_version: Literal["1.0"] = SCHEMA_VERSION

    def __post_init__(self):
        require(bool(self.selected_document_ids), "No selected documents")
        require(len(set(self.selected_document_ids)) == len(self.selected_document_ids), "Duplicate selection")
        require(bool(self.evidence), "Answer requires evidence")
        require(all(e.document_id in self.selected_document_ids for e in self.evidence),
                "Answer includes an unselected document")
