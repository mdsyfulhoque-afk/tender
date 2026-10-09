# Independent transfer archive verification

Verifier: `/root/tenderos_independent_verification`. Execution UTC interval: 2026-10-09 15:36:26 to 15:38:41. Launcher: actual delegated agent resumed with `collaboration.followup_task`. Opaque run ID was not exposed.

| Archive | SHA-256 | Entries | Expanded bytes |
| --- | --- | --- | --- |
| TenderOS_Codex_Work_Transfer_v1_2.zip | 7786d9785ebf6c8db21b547f174277f872f20a15a58219c36dc70642d9a33867 | 31 | 327,473 |
| TenderOS_Agentic_Handoff_v1_1.zip | a9d85fd86664360f095e12dba5dc5adddbb23641ef6c120ecc23c6045e3449d1 | 10, including one directory | 48,683 |

No absolute/traversal paths, symlinks, duplicate names, encrypted members or excessive expansion were found. The largest member is 97,643 bytes, and the largest expansion ratio is 44.321. The embedded APES DOCX contains 19 safe internal entries, without VBA, ActiveX or embedded-object entries.

The database member `repo/data/tenderos.sqlite3` is 49,152 bytes. The verifier did not open its member content, decode it, hash its expanded bytes or check its CRC. Its claimed emptiness was not verified. The complete `repo/data/` tree must be excluded from import.

All 30 non-database transfer files and nine handoff regular files passed CRC checks when read. All 29 safe manifest-covered files match recorded sizes/SHA-256; the manifest itself has no self-entry. All ten preservation records match the supplied file bytes and their recorded baseline hashes. These are internal consistency checks, not independent verification of an earlier baseline.

All nine handoff documents equal corresponding transfer knowledge files byte for byte. No duplicate knowledge import is needed.

Path inspection found no credential, upload, cache, Git-internal or e-GP scan artifact besides the excluded database. This does not prove every document contains no confidential information.

Actual execution methods: `functions.exec`, `tools.exec_command`, `tools.clock__curr_time`, internal `collaboration.send_message`. Inspections used Python `pathlib`, `zipfile`, `hashlib`, JSON parsing, AST parsing and byte comparisons. Tool trace chunks: `09e67b`, `2cf38a`, `b14138`, `f829d3`, `8989c3`. No application execution, filesystem writes or external model API calls occurred in this archive-verification execution. This persisted report is a synopsis of the actual agent transcript, not a raw exported log.
