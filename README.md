# Intelligent Form Agent — Phase 1

Only document identification, shared data contracts, and local source-review
fixtures are implemented. There are no model calls, extraction pipeline, QA,
summarization, cross-document analysis, or UI implementations.

Use Python 3.9 or later. Phase 1 has no third-party dependencies.
Run from the repository root:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m form_agent.validate_local
```

The first command uses synthetic inputs and works without assignment data.
The second requires the original PNGs in `data/raw/project_data/` and the local
review artifacts in `data/validation/`. It fails if they are missing or changed;
it does not recreate manually reviewed expectations or evaluate model accuracy.

## Contracts and identity

- `src/form_agent/inventory.py`: inventory PNG metadata and SHA-256 content IDs.
  Renaming identical content preserves its ID. Duplicate content is rejected,
  never silently merged. The filename UUID is retained separately. No pages are
  grouped by UUID. PNG header inspection is not a complete image integrity check.
- `src/form_agent/models.py`: document identity, printed page observations,
  field values, repeating tables, section text, evidence, and answer envelopes.
  `to_json()` and `from_json()` strictly validate nested types and references.
  Direct dataclass construction checks semantic invariants; serialization is the
  strict type-validation boundary. No answer generation is implemented.
- `src/form_agent/validate_local.py`: check reviewed fixture structure, identity,
  source hashes, question references, and serialization without network access.

Each image is one supplied document with `image_index=1`. `filename_page` is
parsed only from recognized filenames. `printed_page` remains null unless a
visual review observation is explicitly supplied; it is never inferred from the
filename. Evidence points to document ID, filename, image index, section, field,
and optional one-based table row. Printed page metadata is resolved through the
document identity.

Fields and table cells keep `source_text` separate from `normalized`. Identifiers
and medical codes must remain strings, including leading zeros. `blank` means a
visibly empty field; `unreadable` means a reading failure; `not_present` means the
field is absent. `checked` and `unchecked` are separate states. The form label
`Unknown` is ordinary source text with a checkbox state, not a reading failure.
Unreadable values cannot have inferred normalized content. Evidence observations
are reviewer descriptions, not fabricated quotations. Optional normalized values
are scalar; repeated data belongs in tables. Arbitrary field keys and section
text allow additional form-specific content without fixed coordinates.

## Local data and GitHub boundary

Upload candidates are source code, synthetic tests, `requirements.txt`, this
README, `.gitignore`, and the two implementation plans. No commit or push has
been performed.

The existing `/data/` ignore rule excludes all originals and these derived files:

- `data/validation/inventory.json`: 11 source identities and reviewed footers.
- `data/validation/expected-values.json`: partial source-derived fields, tables,
  observations, and English validation questions and expected answers.
- `data/validation/prior-demo-expectations.md`: previously recorded demo
  expectations moved out of the uploadable plans; not execution results.

Do not force-add these files. Local fixtures must be transferred separately if
needed; a GitHub checkout alone can run only the synthetic tests. The small
review set is not a comprehensive ground-truth dataset or an accuracy measure.
Expected answers are reference material for future work, not QA outputs.

## Remaining decisions

The model provider, model, upload formats beyond supplied PNGs, normalization
rules beyond these contracts, and future extraction prompts remain undecided.
Phase 2 and later require separate implementation. Refer to the English and
Korean plans in `docs/` for the broader roadmap.
