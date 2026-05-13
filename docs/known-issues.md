# Known Issues

## Resolved as of 2026-05-13

### Module metadata not retroactively backfilled for the 112,021 vectors ingested on 2026-05-13

**Status:** Fix deployed in `src/ingestion/loader.py` — applies to all *future* ingests (webhook-driven incremental updates and any subsequent full re-ingest). Existing vectors keep their incorrect `module` values until the next full re-ingest.

**Original bug**

`_detect_module()` in `src/ingestion/loader.py` used the regex:

```python
_MODULE_PATTERN = re.compile(r"(?:[Mm]odule|[Mm]od|模組|模塊)[\s_\-]*0*(\d+)")
```

Two problems:

1. **Over-greedy digit capture.** `(\d+)` matched arbitrarily long digit runs, so filenames like `…作業中心模組-20260422.xlsx` (an `xlsx` model-data export tagged with a date) were parsed as `module=20260422`.
2. **No Chinese numeral support.** The AVM Drive folder uses Chinese numerals for module folders (`模組一`, `模組二`, `模組三`, …). These never matched.

Sample distribution from the 2026-05-13 ingest (100 random vectors):

| module value      | count | meaning                              |
| ----------------- | ----- | ------------------------------------ |
| 0                 | 90    | no match (expected for non-module files) OR Chinese-numeral module folder (missed) |
| 20260422          | 4     | wrong — captured a date              |
| 20250307          | 3     | wrong — captured a date              |
| 20250401          | 3     | wrong — captured a date              |

**Impact**

- Module-scoped retrieval (`module_filter=N` in `retrieve_chunks`) returns empty/wrong results for the 2026-05-13 vectors.
- Source attribution, file-name citations, and general Q&A are unaffected (those use `source_file` and `file_name`, which are correctly populated).

**Remediation paths**

- **No action (current):** module filter silently underperforms for these vectors. Future webhook updates that re-ingest individual files will write correct module values for those files.
- **Full re-ingest:** ~3 hours runtime + Voyage embedding credits. Should be bundled with any other ingestion-pipeline change to amortize cost.

---

## Open

### Skipped files during 2026-05-13 ingest

- **403 `cannotDownloadFile`** (~4 files): service account has read but not download permission on those Drive files. Owners need to relax sharing settings (uncheck "Viewers and commenters can see the option to download, print, and copy").
- **404 `File not found`** (~6 files): Drive shortcuts pointing to deleted targets. Safe to clean up the broken shortcuts in Drive.

Both classes were logged and skipped — they didn't fail the ingest. List of IDs is in `/tmp/ingest.log` on the VPS.
