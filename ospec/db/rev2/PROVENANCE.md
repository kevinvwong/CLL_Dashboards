# Rev2 source provenance

What this directory is, where it came from, and how to re-verify it.

## Source

| | |
|---|---|
| Package | `CLL_Strategy_Portfolio_Enterprise_Package_v1.0.zip` |
| Location | repository root; **gitignored**, never committed (see the change's design.md D8) |
| Archive SHA256 | `EB71B8BCA667420F78E3289C4D2AB4DD341482CDAA464E7E1050E30A1251E08E` |
| Package version | 1.0 |
| Architecture version | Revision 2 |
| Status | Governance Review Baseline |
| Baseline date | 2026-10-05 |
| Canonical strategy authority | `CLL-strategy-2035-presentation.pptx` |

## Contents

| File | Source in package | SHA256 of the transcribed source |
|---|---|---|
| `package_04_baseline.sql` | `04_Strategy_Portfolio_Schema_with_Constraints.sql` | recorded in the file's own header |
| `package_09_rev2_migration.sql` | `09_Strategy_Portfolio_Revision2_Migration.sql` | recorded in the file's own header |

Both files are transcribed **verbatim**. The package's PostgreSQL forms are left
unrewritten because ADR-021 designates them a reference implementation, and the
whole point of keeping them unmodified is to be able to measure the T-SQL port
against them. Each file carries a header with its provenance and the five
package contradictions; the package SQL itself follows byte-for-byte.

## Re-verification

The package self-checks, and this transcription can be re-checked against it.
`SHA256SUMS.txt` in the package lists 12 files with hashes; at intake all 12
matched. To re-verify:

```powershell
# 1. the archive is unaltered
Get-FileHash CLL_Strategy_Portfolio_Enterprise_Package_v1.0.zip -Algorithm SHA256
# expect EB71B8BCA667420F78E3289C4D2AB4DD341482CDAA464E7E1050E30A1251E08E

# 2. the transcription is faithful: the package SQL must be a byte-suffix of
#    each transcribed file, with only the provenance header prepended
python -c "import zipfile,os; z=zipfile.ZipFile('CLL_Strategy_Portfolio_Enterprise_Package_v1.0.zip'); \
  a=z.read('04_Strategy_Portfolio_Schema_with_Constraints.sql').decode(); \
  b=open('ospec/db/rev2/package_04_baseline.sql',encoding='utf-8').read(); \
  print('verbatim:', b.endswith(a))"

# 3. table counts
#    baseline 15 + migration 12 = 27
```

## What is not here

No extract of `03_Strategy_Portfolio_Data_Package.xlsx` or
`10_Business_Data_Validation_Register.xlsx` is present anywhere in the
repository. The package's business data is read in place and never written
into the tree; only the schema and the canonical-strategy vocabulary that the
schema itself depends on are carried forward.

## Scope note

Revision 2 is a **governance review baseline**, not an approved production
schema. Its own readiness table marks the Dean and D-1 initiative inventories,
ownership and stewardship assignments, and metric definitions as *Pending
business validation*, executive signoff as *Pending*, and production migration
as conditional. See `inventory-absent.md` in this directory.
