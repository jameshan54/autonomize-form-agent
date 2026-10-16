"""Synthetic checks only: no source-derived values belong in this file."""

import copy
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from form_agent.inventory import identify, inventory
from form_agent.models import Answer, Document, Evidence, PrintedPage, Table, TableRow, Value


def png(pixel=b'\x01\x02\x03'):
    def chunk(kind, value):
        return struct.pack('>I', len(value)) + kind + value + struct.pack('>I', zlib.crc32(kind + value))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(b'\x00' + pixel)) + chunk(b'IEND', b''))


class PhaseOneTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / '12345678-1234-4234-8234-123456789abc_TX_page_1.png'
        self.path.write_bytes(png())
        self.identity = identify(self.path, self.root, PrintedPage('Page 3 of 5', 3, 5))
        self.evidence = Evidence('e1', self.identity.document_id, self.path.name, 1,
                                 'Synthetic section', 'code', '0012X', 'Visible synthetic text.')
        self.value = Value('readable', '0012X', '0012X', ['e1'])

    def test_identity_keeps_page_systems_separate(self):
        self.assertEqual(self.identity.filename_page, 1)
        self.assertEqual(self.identity.image_index, 1)
        self.assertEqual(self.identity.printed_page.number, 3)
        self.assertIsNone(identify(self.path, self.root).printed_page)

    def test_content_identity_survives_rename(self):
        other = self.root / 'upload.png'
        self.path.rename(other)
        result = identify(other, self.root)
        self.assertEqual(result.document_id, self.identity.document_id)
        self.assertIsNone(result.filename_page)
        self.assertIsNone(result.supplied_uuid)

    def test_duplicate_content_is_rejected(self):
        (self.root / 'duplicate.png').write_bytes(png())
        with self.assertRaisesRegex(ValueError, 'Duplicate image'):
            inventory(self.root, self.root)

    def test_different_images_are_not_merged(self):
        (self.root / 'other.png').write_bytes(png(b'\x04\x05\x06'))
        self.assertEqual(len(inventory(self.root, self.root)), 2)

    def test_invalid_input_is_rejected(self):
        self.path.write_bytes(b'not an image')
        with self.assertRaises(ValueError):
            identify(self.path, self.root)

    def test_json_round_trip_preserves_codes_and_free_text(self):
        document = Document(self.identity, [self.evidence], {'code': self.value},
                            section_text={'Synthetic section': self.value})
        result = Document.from_json(document.to_json())
        self.assertEqual(document, result)
        self.assertEqual(result.fields['code'].source_text, '0012X')

    def test_blank_unreadable_and_unknown_are_distinct(self):
        values = [Value('blank', '', None, ['e1']), Value('unreadable', None, None, ['e1']),
                  Value('checked', 'Unknown', True, ['e1']), Value('unchecked', 'Other', False, ['e1'])]
        for value in values:
            self.assertEqual(value, Value.from_json(value.to_json()))
        with self.assertRaises(ValueError):
            Value('unreadable', None, 'Invented text', ['e1'])
        with self.assertRaises(ValueError):
            Value('unchecked', 'Other', True, ['e1'])

    def test_cross_document_evidence_is_rejected(self):
        other = copy.deepcopy(self.evidence)
        other.document_id = 'sha256:' + 'f' * 64
        with self.assertRaisesRegex(ValueError, 'another document'):
            Document(self.identity, [other], {'code': self.value})

    def test_unresolved_and_duplicate_evidence_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unresolved'):
            Document(self.identity, [], {'code': self.value})
        with self.assertRaisesRegex(ValueError, 'Duplicate evidence'):
            Document(self.identity, [self.evidence, self.evidence])

    def test_table_row_association_is_enforced(self):
        self.evidence.table, self.evidence.row = 'services', 1
        table = Table('services', 'Synthetic section', [TableRow(1, {'code': self.value})])
        document = Document(self.identity, [self.evidence], tables=[table])
        self.assertEqual(Document.from_json(document.to_json()), document)
        table.rows[0].row = 2
        with self.assertRaisesRegex(ValueError, 'Cell evidence mismatch'):
            document.to_json()

    def test_answer_selection_is_enforced(self):
        answer = Answer('What code is shown?', '0012X', 'answered',
                        [self.identity.document_id], [self.evidence])
        self.assertEqual(Answer.from_json(answer.to_json()), answer)
        with self.assertRaisesRegex(ValueError, 'unselected'):
            Answer('What code is shown?', '0012X', 'answered', ['other'], [self.evidence])

    def test_strict_json_rejects_unknown_keys_types_and_versions(self):
        document = Document(self.identity, [self.evidence], {'code': self.value})
        import json
        for mutate in [lambda d: d.update(schema_version='99'),
                       lambda d: d.update(extra=True),
                       lambda d: d['fields']['code'].update(source_text=12),
                       lambda d: d['identity'].update(width=True),
                       lambda d: d['fields']['code'].update(state='unknown')]:
            payload = document.to_dict()
            mutate(payload)
            with self.assertRaises(ValueError):
                Document.from_json(json.dumps(payload))


if __name__ == '__main__':
    unittest.main()
