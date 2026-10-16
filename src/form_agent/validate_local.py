"""Check local review artifacts against file identity and contract invariants."""

import argparse
import json
from pathlib import Path

from .inventory import inventory
from .models import Answer, Document, DocumentIdentity, decode, require


def validate(root):
    root = Path(root)
    folder = root / 'data/validation'
    saved = [decode(DocumentIdentity, d) for d in json.loads((folder / 'inventory.json').read_text())]
    actual = inventory(root / 'data/raw/project_data', root,
                       {d.filename: d.printed_page for d in saved})
    require([d.to_dict() for d in saved] == [d.to_dict() for d in actual], 'Source inventory changed')
    require(len(actual) == 11, 'Expected 11 supplied images')
    require(len({d.supplied_uuid for d in actual}) == 11, 'Expected distinct supplied UUIDs')
    require(sum(d.filename_page == 1 for d in actual) == 7, 'Filename page distribution changed')
    require(sum(d.filename_page == 2 for d in actual) == 4, 'Filename page distribution changed')
    require(all((d.width, d.height) == (2480, 3509) for d in actual), 'Source dimensions changed')
    require(all(d.printed_page and (d.printed_page.number, d.printed_page.total) == (2, 2)
                for d in saved), 'Missing reviewed printed page')
    payload = json.loads((folder / 'expected-values.json').read_text())
    require(payload['schema_version'] == '1.0', 'Unsupported fixture version')
    require(payload['review']['method'] == 'direct_visual_source_review', 'Missing review provenance')
    documents = [decode(Document, d) for d in payload['documents']]
    identities = {d.document_id: d for d in saved}
    require(len({d.identity.document_id for d in documents}) == len(documents), 'Duplicate fixture document')
    evidence = {}
    states = set()
    for doc in documents:
        require(doc.identity == identities.get(doc.identity.document_id), 'Fixture source mismatch')
        require(Document.from_json(doc.to_json()) == doc, 'Document round-trip failed')
        for e in doc.evidence:
            require(e.evidence_id not in evidence, 'Duplicate fixture evidence')
            evidence[e.evidence_id] = e
        states.update(v.state for v in doc.fields.values())
    require({'readable', 'blank', 'unreadable', 'checked', 'unchecked'} <= states, 'Missing review cases')
    answers = [decode(Answer, q) for q in payload['questions']]
    require(bool(answers), 'Missing validation questions')
    for answer in answers:
        require(Answer.from_json(answer.to_json()) == answer, 'Answer round-trip failed')
        for e in answer.evidence:
            require(e == evidence.get(e.evidence_id), 'Question evidence differs from reviewed source')
    return {'inputs': len(saved), 'reviewed_documents': len(documents),
            'validation_questions': len(answers), 'evidence_items': len(evidence)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(validate(args.root), indent=2))


if __name__ == '__main__':
    main()
