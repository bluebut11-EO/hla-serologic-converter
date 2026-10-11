# Changelog

## 0.4.0
- **Fix:** allele fields with four digits (A*02:1000+, C*07:1000+, DPB1*1000+; 1,595 alleles
  in IPD-IMGT/HLA 3.65.0) are now read correctly. Earlier versions could read `A*02:1294`
  as `A*02:129`. Malformed names are now always shown as `unparseable`, never shortened.
- `hla-sero diff OLD NEW`: every 2-field group whose serological equivalent or status
  changed between two IMGT/HLA releases (e.g. 3.64.0 → 3.65.0: DQB1*02:273–276 moved
  from unambiguous to assumed DQ2).
- Weekly GitHub "IMGT/HLA watch": one issue per new release with the change report,
  a warning issue if hla-sero checks fail against it.
- An unsuffixed name finds a suffixed allele (`A*01:22` → `A*01:22N`).

## 0.3.0
- Standalone Windows `hla-sero.exe` built by GitHub Actions.
- Cross-check mode: compare the lab's current serology with the computed equivalent.

## 0.2.0
- Live IPD-IMGT/HLA WMDA data with md5-verified, versioned auto-update.
- Installable `hla-sero` command and copy-paste window.
