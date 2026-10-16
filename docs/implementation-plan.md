# Intelligent Form Agent Implementation Plan

## 1. Objectives and Scope Criteria

Extract information from form images and provide single-document QA, single-document summaries, and analysis across multiple documents. Implement the core pipeline first, validate its results against the actual source documents, and then connect a simple Streamlit UI.

- Requirements source: [Machine Learning Assignment.pdf](../assignment/Machine%20Learning%20Assignment.pdf), all 2 pages.
- Data review scope: 11 PNG files in [data/raw/project_data/](../data/raw/project_data/).
- `assignment/job-description.md` has not been read and is excluded from the requirements.
- This document records the plan and verified progress. Only Phase 1 is complete; later phases remain unimplemented.
- Comprehensive accuracy evaluation, failure analysis, before-and-after comparisons, cost dashboards, and additional infrastructure are deferred to future extensions.
- Validation against the actual source documents and recording processing time and API-reported token usage for each model call are included in the current scope.

## 2. Required Implementation Scope

### Assignment Requirements and Deliverables

- [ ] Extract structured and unstructured information from form images.
- [ ] Provide single-document QA.
- [ ] Provide single-document summaries.
- [ ] Provide answers and analysis synthesized across multiple documents.
- [ ] Include a README describing functionality, environment setup, step-by-step execution, example questions, and expected results.
- [ ] Include at least 1 required demo for each of single-document QA, single-document summarization, and a synthesized answer across multiple documents.
- [ ] Specify dependencies in `requirements.txt` or `environment.yml`.
- [ ] Organize the repository with logical separation of core source code, data, tests, and documentation.
- [ ] Deliver a repository or compressed folder that supports end-to-end execution with minimal setup.

The PDF presents `/src`, `/data`, `/notebooks`, `/tests`, and `/docs` as an example of logical organization. Add notebooks if experiments are needed; do not build separate model training or experimentation features for the current objective. Screenshots, logs, and short demonstration videos are optional.

### Streamlit UI Included at the User's Request

The PDF makes the UI optional, but it is included in the current implementation scope. Keep it separate from the core pipeline and document its execution separately in the README.

- [ ] Select a provided document or upload an image.
- [ ] View the original image and extraction results.
- [ ] Enter a question and display the answer with sources.
- [ ] View a single-document summary.
- [ ] Select multiple documents and ask a question across them.

The initial input scope is form images, including the provided PNG files. Specify supported upload image formats. Propose features such as multipage PDF uploads only after separately assessing their necessity.

## 3. Observed Data Characteristics and Limitations

- All 11 PNG files are 2480×3509, with distinct file UUIDs and content hashes.
- All use the same Texas prior authorization request form for health care services.
- They contain patient information, requesting and service provider information, urgency, service and diagnosis tables, and treatment types, session counts, and durations.
- Filenames contain `page_1` in 7 cases and `page_2` in 4 cases, but every image has `Page 2 of 2` printed on it.
- No other pages with the same UUID were provided. Treat each image as one supplied document for now. Do not arbitrarily combine files with different UUIDs or infer the contents of missing pages.
- Some issuer names are erased or damaged. Distinguish blank fields, unreadable content, check marks, and printing noise.
- Some service and diagnosis descriptions contain short or incomplete phrases. Do not use medical codes to invent completions that are absent from the source.
- Preserve free text and section text, but no long narrative clinical notes were found. Do not claim that this dataset validates extraction performance on long narratives or generalization across diverse forms.
- The reviewed folder contains no ground-truth labels or separate text files. Create a small set of manually verified expected values from the source documents.

The PDF and all 11 PNG files were opened and reviewed. Some damaged text in the images cannot be read with certainty. The contents of `data/project_data.zip` were not inspected separately.

## 4. Architecture

The processing flow is:

> Image input → Document identification → Information extraction → Shared document data → QA, summarization, and cross-document analysis → CLI or Streamlit UI

### Components and Responsibilities

- **Input and document management:** Preserve the original file, document ID, filename page number, and printed page information as distinct attributes. Uploaded inputs use the same processing path.
- **Extraction:** Extract structured fields, checkbox states, service table rows, free text, and evidence by section.
- **Shared data format:** Define serializable document, evidence, and answer formats independent of the UI. Distinguish extracted source text from normalized values.
- **QA:** Answer using the selected document's structured data and extracted source text. State explicitly when information is missing or unreadable.
- **Summarization:** Concisely describe the nature of the request, key services and diagnoses, providers, schedules and session counts, and important missing information.
- **Cross-document analysis:** Present similarities, differences, and counts by condition across selected documents, with supporting evidence. Calculate explicit counts and totals from extracted data in code, and use the model to explain them.
- **Shared model-call layer:** Handle model integration, per-call timing and usage, and failure and retry records.
- **CLI and UI:** Call the same core functions. Streamlit code focuses on input, state management, and displaying results.

Allow future evaluation code to call extraction, QA, summarization, and cross-document analysis functions directly without the UI. Core logic must not depend on Streamlit sessions or screen state.

### Initial Extraction Approach Proposal

Because both image content and checkboxes must be read, the initial proposal is to use a model that supports image inputs for extraction. The provider and specific model have not been selected. Propose a separate OCR engine or retrieval infrastructure if actual results demonstrate a need; do not automatically add them to the scope.

Do not bind all document understanding to fixed coordinates merely because the current dataset uses the same form. Leave room in the shared data format to preserve additional fields specific to other forms and free text.

### Data and Source Attribution Principles

- Preserve document IDs, original files, supplied page information, and printed page information.
- Distinguish structured fields, repeating service and diagnosis rows, and free text by section.
- Preserve identifiers and medical codes as strings.
- Distinguish source text from normalized values.
- Represent blank, unreadable, and unchecked as separate states. Also distinguish the form's `Unknown` option from a reading failure.
- Link sources to at least the filename, page, section, field or table row, and supporting source text.
- Do not perform QA solely from summaries. Use extracted source text and structured data together.
- Do not fill in missing content or infer completed approval or treatment from a request form alone.

## 5. Phased Checklist and Validation Methods

### Phase 1: Establish Document Identification and Data Formats

- [x] Inventory the 11 inputs by document.
- [x] Define shared formats for documents, fields, tables, evidence, and answers.
- [x] Create a small set of manually verified expected values and validation questions from the sources.
- [x] Include cases covering readable values, blanks, damaged values, checkboxes, and service tables.

**Validation:** Check that different documents are not mixed and that filename page numbers are not confused with printed page numbers. Establish expected values by checking the original images, rather than copying model outputs.

**Verified on 2026-10-16:** The initial Git working tree was clean and contained
only the two plans and `.gitignore`; no existing implementation was duplicated.
Implemented `src/form_agent/{inventory,models,validate_local}.py`, synthetic tests,
and Phase 1 execution instructions in `README.md`. Standard-library-only setup
is recorded in `requirements.txt`.

All 11 original images were opened to review their printed footers. The local
inventory preserves 11 distinct UUIDs and hashes, dimensions, filenames,
filename pages (7 page-1 and 4 page-2 files), and independently reviewed printed
pages. No files are merged. Four source images supply 41 evidence items and
10 English validation questions, covering readable values, blanks, damaged
issuer text, checked/unchecked boxes, explicit Unknown, leading-zero codes,
and service/diagnosis row associations. Incomplete descriptions remain literal.

Validation passed: 12 synthetic unit tests; local source/hash and contract
validation for 11 inputs, 4 partial expected documents, and 10 questions;
JSON round trips; PNG SHA-256 comparison before/after; Git exclusion checks.
These checks validate Phase 1 artifacts, not extraction or QA accuracy.

GitHub candidates: source code, synthetic tests, README, requirements, ignore
rules, and both plans. Source-derived inventory, expectations, and prior demo
reference values remain under ignored `data/validation/`. Existing source data
was not changed. `assignment/job-description.md` was not read. No model API,
extraction pipeline, QA, summarization, UI, commit, or push was performed.
Remaining decisions: provider/model, additional upload formats, normalization
policies, and extraction prompts. Phase 2 onward is deferred.

### Phase 2: Implement and Validate the Extraction Pipeline

- [ ] Connect image input to shared document data generation using representative documents.
- [ ] Extract patient and provider fields, checkboxes, service and diagnosis tables, and free text.
- [ ] Preserve blank and unreadable states.
- [ ] Integrate output format validation and model-call logging.
- [ ] Process all 11 documents and compare results with their sources.

**Validation:** Compare key fields, table row associations, codes and dates, checkbox states, and free-text omissions side by side with the actual images. Check that erased issuer names or completions of incomplete descriptions are not invented. Valid JSON alone is not sufficient to pass. Keep a simple validation record of identified errors and the results of corrective actions.

### Phase 3: Implement and Validate Single-Document QA

- [ ] Answer using the selected document's extracted data and source evidence.
- [ ] Attach sources to answers.
- [ ] Explain missing information and unreadable content.
- [ ] Validate questions about individual fields, relationships between table entries, checkboxes, and information absent from the document.

**Validation:** Compare both answers and sources with the original document. For example, an urgent checkbox must not lead to an invented reason when the urgency reason field is blank. Information from other documents must not be mixed into the answer.

### Phase 4: Implement and Validate Single-Document Summarization

- [ ] Summarize the nature of the request, key services and diagnoses, providers, schedules and session counts, and important missing information.
- [ ] Make the evidence used in the summary traceable.
- [ ] Prevent adding facts absent from the document.

**Validation:** Compare each factual statement in the summary with the source and check for omissions of key information. Verify that request status is not changed into completed approval or treatment, and that incomplete diagnosis phrases are not arbitrarily expanded.

### Phase 5: Implement and Validate Cross-Document Analysis

- [ ] Include only selected documents in the analysis.
- [ ] Answer questions about similarities, differences, and counts by condition.
- [ ] Calculate explicit values requiring aggregation in code.
- [ ] Reflect document-specific evidence and missing values in the answer.

**Validation:** Compare results with manual counts and calculations. Check denominators, missing-value handling, double counting, and sources. Answers must not include information from unselected documents. Also verify that the output provides a synthesized conclusion relevant to the question, rather than merely listing individual summaries.

### Core Pipeline Validation Completion Criteria

- [ ] Extraction results for all 11 documents have been compared with the sources.
- [ ] QA, summarization, and cross-document analysis can run without the UI.
- [ ] Answers and sources have been checked for representative validation cases.
- [ ] Known errors have been corrected, affected cases have been revalidated, and remaining reading limitations have been documented.
- [ ] Per-call timing and token records are available.

Connect the UI after these criteria are met. Do not present this small validation set as a measure of overall accuracy or generalization performance.

### Phase 6: Connect and Validate the Streamlit UI

- [ ] Connect document selection and image uploads.
- [ ] Display original images and extraction results.
- [ ] Support question input and display answers with sources.
- [ ] Display summaries.
- [ ] Connect multiple-document selection and cross-document questions.
- [ ] Manage document-specific state and reuse existing results.

**Validation:** Check that the CLI and UI use the same core functions. Answers from the previous document must not remain when the selected document changes. Simple UI reruns must not trigger unnecessary model calls. Verify that selecting a provided file and uploading the same image use the same processing path.

### Phase 7: Validate the README, Demos, and Deliverables

- [ ] Document functionality, implementation scope, and known limitations in the README.
- [ ] Explain dependency installation, API configuration, and core pipeline execution.
- [ ] Explain UI execution separately.
- [ ] Record inputs, questions or tasks, expected results, and actual execution results for the 3 required demos.
- [ ] Verify end-to-end execution in a minimal fresh environment by following the README in order.
- [ ] Check the submission structure as a repository or compressed folder.

**Validation:** Record example results only after actual execution and comparison with source documents. Check for missing manual steps from environment setup through demo and UI execution. Place meaningful core validation needed for the implementation in `/tests`; do not build a separate evaluation dashboard.

## 6. Required Demos (Planned)

Single-document QA, single-document summarization, and a synthesized answer
across multiple documents remain required future demos. None has been executed.
Previously recorded source-specific demo expectations now reside only in
`data/validation/prior-demo-expectations.md` (Git-ignored). The Phase 1 reviewed
questions and expected answers are in `data/validation/expected-values.json`.
These local reference files are not model outputs or GitHub upload candidates.

## 7. Per-Call Timing and Token Logging

Use the shared model-call layer for extraction, QA, summarization, and cross-document analysis, with simple local JSONL records.

- Run ID and call ID.
- Task type and related document IDs.
- Model name, prompt version, and schema version.
- Start time and call duration. Measure duration with a monotonic clock.
- Success or failure status, error type, and retry number.
- API-reported input, output, and total tokens, along with any additional usage fields.

Leave usage that the API does not provide as `null`; do not fill it with estimates. Record retries as separate calls. Distinguish cached result reuse from actual API calls. Do not present per-call duration as the same metric as total document processing time. Avoid unnecessarily duplicating source document text or complete questions and answers in execution metadata logs.

Do not convert tokens into monetary amounts or label them as actual billed costs in the current scope. Estimated costs can be calculated later using model-specific rates and a reference date. Do not introduce a separate logging server or monitoring infrastructure.

## 8. Proposed Future Extensions

The following items are outside the current required implementation scope. Explain their necessity and expected benefits, propose them, and then decide whether to expand the scope.

- **Ground-truth datasets and accuracy evaluation:** Once enough validation documents and questions are available, repeatedly measure extracted fields, QA answers, source attribution accuracy, and summary omissions.
- **Failure classification:** Analyze the causes of recurring failures such as checkbox misreads, confusion between table rows, unreadable content, and unsupported answers.
- **Before-and-after comparisons:** Compare the effects of model, prompt, and schema changes using the same inputs and expected values. Reuse the version records and independent core logic established in this implementation.
- **Processing time and cost analysis:** Once call logs accumulate, analyze latency and token usage by task, then add cost estimates using reference rates.
- **Supplementary OCR or image preprocessing:** Consider these when actual extraction errors demonstrate a need for separate OCR, enlargement, or region splitting.
- **Retrieval and vector databases:** Consider these when document volume or context length makes directly processing all selected documents difficult.
- **Validation for diverse forms, long text, and multiple pages:** Validate input types not covered by the current dataset when additional data becomes available.
- **Evaluation dashboards and additional infrastructure:** Consider these when repeated evaluation and operational requirements arise.

For now, focus on completing the required functionality and simple UI while preserving source comparison results, call records, and core logic independent of the UI.
