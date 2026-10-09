"""Record and execute the authorized unchanged TenderOS archive migration.

This imports inert files only. It never imports or executes application code,
opens a SQLite member, installs packages, runs tests, or contacts a network.
"""

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile


ROOT = Path('/workspace/tender/TenderOS')
ZIP = Path('/tmp/codex-remote-attachments/01a12138-29be-72ba-9771-158f618a304b/25b815ab-3db0-4592-a607-5c40b901100f/2-TenderOS_Codex_Work_Transfer_v1_2.zip')
PREFIX = 'TenderOS_Codex_Work_Transfer_v1_2/'
REPORT = ROOT / 'verification/IMPORT_REPORT.json'
TASK_ID = '/root/tenderos_source_import'


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def digest(data):
    return sha256(data).hexdigest()


def file_digest(path):
    h = sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def safe_destination(path):
    if not path.is_relative_to(ROOT):
        raise ValueError(f'Destination escapes root: {path}')
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError(f'Destination symlink: {component}')
    if path.exists() and not path.is_file():
        raise ValueError(f'Non-file destination: {path}')


def mapped_destination(relative):
    if relative.startswith('repo/data/'):
        return None
    if relative == 'repo/AGENTS.md':
        relative = 'verification/TRANSFER_REPO_AGENTS.md'
    elif relative == 'repo/README.md':
        relative = 'verification/MVP_README_ORIGINAL.md'
    elif relative.startswith('repo/'):
        relative = relative[len('repo/'):]
    elif relative != 'START_HERE.md' and not relative.startswith(
        ('project_knowledge/', 'agent_ops/', 'verification/')
    ):
        raise ValueError(f'Unexpected archive mapping: {relative}')
    if relative in {'AGENTS.md', 'README.md', 'IMPORT_EXISTING_SOURCES.md'}:
        raise ValueError(f'Protected current governance destination: {relative}')
    if relative.startswith('agent_ops/receipts/'):
        raise ValueError(f'Protected current receipt destination: {relative}')
    return ROOT / relative


started = utc_now()
safe_destination(REPORT)
if REPORT.exists():
    raise FileExistsError(f'Refusing to overwrite existing report: {REPORT}')

protected = [ROOT / name for name in ('AGENTS.md', 'README.md', 'IMPORT_EXISTING_SOURCES.md')]
protected.extend(sorted((ROOT / 'agent_ops/receipts').rglob('*')))
protected = [path for path in protected if path.is_file() or path.is_symlink()]
preserved_before = []
for path in protected:
    safe_destination(path)
    preserved_before.append({'path': str(path), 'before_sha256': file_digest(path)})

archive_sha256 = file_digest(ZIP)
if archive_sha256 != '7786d9785ebf6c8db21b547f174277f872f20a15a58219c36dc70642d9a33867':
    raise ValueError('ZIP hash changed after independent audit')

seen_names = set()
seen_destinations = set()
plans = []
exclusions = []
with zipfile.ZipFile(ZIP) as archive:
    infos = archive.infolist()
    for info in infos:
        name = info.filename
        path = PurePosixPath(name)
        mode = info.external_attr >> 16
        if (
            name in seen_names or path.is_absolute() or '\\' in name
            or any(component in ('', '.', '..') for component in name.split('/'))
            or not name.startswith(PREFIX) or stat.S_ISLNK(mode)
            or not stat.S_ISREG(mode)
        ):
            raise ValueError(f'Unsafe or duplicate ZIP entry: {name}')
        seen_names.add(name)
        relative = name[len(PREFIX):]
        destination = mapped_destination(relative)
        if destination is None:
            exclusions.append({
                'archive_path': name,
                'archive_relative_path': relative,
                'size_bytes_from_zip_metadata': info.file_size,
                'member_content_read': False,
                'member_extracted': False,
                'sha256_recomputed': False,
                'reason': 'All repo/data/ members excluded; no private/local database imported.',
            })
            continue
        if destination in seen_destinations:
            raise ValueError(f'Duplicate mapped destination: {destination}')
        seen_destinations.add(destination)
        safe_destination(destination)
        data = archive.read(info)
        existing = destination.exists()
        if existing and destination.read_bytes() != data:
            raise ValueError(f'Conflicting destination, no overwrite permitted: {destination}')
        plans.append({
            'archive_path': name,
            'archive_relative_path': relative,
            'destination_path': str(destination),
            'destination_relative_path': destination.relative_to(ROOT).as_posix(),
            'size_bytes': len(data),
            'source_sha256': digest(data),
            'action': 'preserved_existing_identical' if existing else 'created_byte_preserving_copy',
            '_data': data,
        })

    by_source = {plan['archive_relative_path']: plan for plan in plans}
    manifest = json.loads(by_source['verification/FILE_MANIFEST.json']['_data'])
    manifest_by_path = {row['path']: row for row in manifest['files']}
    if len(manifest_by_path) != len(manifest['files']):
        raise ValueError('Duplicate file manifest entry')
    manifest_matches = []
    for plan in plans:
        row = manifest_by_path.get(plan['archive_relative_path'])
        if row is None:
            if plan['archive_relative_path'] != 'verification/FILE_MANIFEST.json':
                raise ValueError('Missing source manifest coverage: ' + plan['archive_relative_path'])
            plan['file_manifest_match'] = None
            plan['file_manifest_match_reason'] = 'Original manifest does not list itself.'
            continue
        valid = row['sha256'] == plan['source_sha256'] and row['size_bytes'] == plan['size_bytes']
        if not valid:
            raise ValueError('Original manifest mismatch: ' + plan['archive_relative_path'])
        plan['file_manifest_match'] = True
        manifest_matches.append(plan['archive_relative_path'])

    preservation = json.loads(by_source['verification/PRESERVATION_CHECK.json']['_data'])
    preservation_matches = []
    for original_path, historical in preservation.items():
        plan = by_source['repo/' + original_path]
        match = (
            plan['source_sha256'] == historical['transfer_sha256']
            == historical['baseline_sha256'] and historical['identical'] is True
        )
        if not match:
            raise ValueError('Historical preservation hash mismatch: ' + original_path)
        preservation_matches.append({
            'original_repo_path': original_path,
            'destination_relative_path': plan['destination_relative_path'],
            'actual_zip_member_sha256': plan['source_sha256'],
            'historical_baseline_sha256': historical['baseline_sha256'],
            'historical_transfer_sha256': historical['transfer_sha256'],
            'matches': True,
            'historical_original_bytes_available': False,
        })

    # Every destination, manifest, and preservation entry is checked before writing.
    for plan in plans:
        destination = Path(plan['destination_path'])
        safe_destination(destination)
        if plan['action'] == 'created_byte_preserving_copy':
            destination.parent.mkdir(parents=True, exist_ok=True)
            safe_destination(destination)
            with destination.open('xb') as output:
                output.write(plan['_data'])
        actual = file_digest(destination)
        if actual != plan['source_sha256']:
            raise ValueError('Post-import byte mismatch: ' + str(destination))
        plan['destination_sha256'] = actual
        plan['byte_preserved'] = True
        del plan['_data']

for row in preserved_before:
    path = Path(row['path'])
    safe_destination(path)
    row['after_sha256'] = file_digest(path)
    row['unchanged'] = row['after_sha256'] == row['before_sha256']
    if not row['unchanged']:
        raise ValueError('Protected existing file changed: ' + row['path'])

report = {
    'schema_version': 1,
    'purpose': 'Authorized unchanged-source migration only; no application defect implementation.',
    'status': 'SOURCE_IMPORT_BYTE_PRESERVATION_VERIFIED',
    'started_at_utc': started,
    'finished_at_utc': utc_now(),
    'agent': {
        'task_id': TASK_ID,
        'canonical_agent_id': TASK_ID,
        'delegation_tool': 'collaboration.spawn_agent',
        'agent_runtime': 'Real separately delegated Codex sub-agent with tool execution.',
        'opaque_run_id': None,
        'opaque_run_id_status': 'No separate opaque run ID exposed by available runtime tools.',
    },
    'branch': 'tenderos/import-v1.2',
    'source_archive': {'path': str(ZIP), 'sha256': archive_sha256, 'file_entries': len(infos)},
    'destination_root': str(ROOT),
    'path_validation': {
        'regular_files_only': True,
        'absolute_paths_traversal_backslashes_and_symlinks_refused': True,
        'duplicate_archive_and_destination_paths_refused': True,
        'existing_destination_symlinks_refused': True,
        'all_destination_conflicts_checked_before_any_archive_copy': True,
        'exclusive_creation_used_for_new_files': True,
        'conflicts': [],
    },
    'counts': {
        'archive_files': len(infos),
        'mapped_files': len(plans),
        'new_archive_files_created': sum(plan['action'] == 'created_byte_preserving_copy' for plan in plans),
        'existing_identical_archive_files_preserved': sum(plan['action'] == 'preserved_existing_identical' for plan in plans),
        'excluded_files': len(exclusions),
        'safe_manifest_members_verified': len(manifest_matches),
        'preservation_record_entries_verified': len(preservation_matches),
        'protected_preexisting_files_verified': len(preserved_before),
        'new_verification_artifacts': 2,
    },
    'source_destination_map': plans,
    'exact_exclusions': exclusions,
    'excluded_archive_prefix': PREFIX + 'repo/data/',
    'preserved_current_governance_and_receipts': preserved_before,
    'original_governance_preservation': {
        'repo/AGENTS.md': 'verification/TRANSFER_REPO_AGENTS.md',
        'repo/README.md': 'verification/MVP_README_ORIGINAL.md',
        'current_AGENTS_README_IMPORT_EXISTING_SOURCES': 'Preserved unchanged.',
    },
    'preservation_record_comparisons': preservation_matches,
    'independent_handoff_equivalence': {
        'evidence_source': 'Current delegated-agent final response relayed by root; independently reported, not recomputed by this import agent.',
        'verifier_task_id': '/root/tenderos_independent_verification',
        'started_at_utc': '2026-10-09T15:36:26Z',
        'finished_at_utc': '2026-10-09T15:38:41Z',
        'transfer_sha256': archive_sha256,
        'handoff_sha256': 'a9d85fd86664360f095e12dba5dc5adddbb23641ef6c120ecc23c6045e3449d1',
        'matching_regular_document_count': 9,
        'all_matching_project_knowledge_documents_byte_identical': True,
        'tool_trace_chunk_ids': ['09e67b', '2cf38a', 'b14138', 'f829d3', '8989c3'],
        'root_planned_evidence_path': 'verification/CURRENT_ARCHIVE_AUDIT.md',
        'opaque_run_id': None,
    },
    'historical_claims': {
        'artifacts_preserved_without_rewriting': [
            'START_HERE.md', 'verification/STATUS.md', 'verification/BASELINE_TEST_RESULTS.txt',
            'verification/PRESERVATION_CHECK.json', 'agent_ops/NOT_LAUNCHED_AGENT_RECEIPT.json',
        ],
        'incorrect_database_omission_claims': ['START_HERE.md', 'verification/STATUS.md'],
        'correction': 'Transfer ZIP actually contains repo/data/tenderos.sqlite3 (49,152 bytes). This migration skipped it without opening the member. No claim that the database is empty has been verified.',
        'historic_test_output_is_current_test_evidence': False,
        'historic_unlaunched_agent_receipt_is_current_execution_evidence': False,
    },
    'command_trace': [
        {'tool': 'tools.exec_command', 'chunk_id': '00a0f6', 'action': 'Read current AGENTS.md, IMPORT_EXISTING_SOURCES.md and separately supplied START_HERE.md.'},
        {'tool': 'tools.exec_command', 'chunk_id': 'bad499', 'action': 'Compute complete ZIP SHA256 and list entry metadata without opening database member.'},
        {'tool': 'tools.exec_command', 'chunk_id': 'd52cbc', 'action': 'Read git status and enumerate existing TenderOS files.'},
        {'tool': 'tools.exec_command', 'chunk_id': '4ab31a', 'action': 'Read archive FILE_MANIFEST, PRESERVATION_CHECK and STATUS inert metadata documents.'},
        {'tool': 'tools.exec_command', 'chunk_id': '0e3ece', 'action': 'Perform read-only path, type, source hash, map and destination conflict preflight.'},
        {'tool': 'tools.exec_command', 'chunk_id': '793e9d', 'command': 'git branch --show-current', 'observed_output': 'tenderos/import-v1.2'},
        {'tool': 'tools.apply_patch', 'action': 'Create verification/IMPORT_COMMAND.py, the persistent exact import command source.'},
        {'tool': 'tools.exec_command', 'command': 'python /workspace/tender/TenderOS/verification/IMPORT_COMMAND.py', 'command_source_path': str(Path(__file__).resolve()), 'command_source_sha256': file_digest(Path(__file__)), 'chunk_id': None, 'chunk_id_status': 'Execution tool result ID becomes available after report creation; root tool transcript preserves it.'},
    ],
    'limits': {
        'tests_run': False,
        'dependencies_installed': False,
        'application_executed': False,
        'application_logic_modified': False,
        'database_member_content_read': False,
        'network_used': False,
        'model_api_used': False,
        'commit_push_merge_or_deploy_performed': False,
        'data_egress': 'None from this task.',
        'known_defect_status': 'DEF-001 remains unresolved; source imported without byte edits.',
        'strict_runtime_identity_gate': 'Separate opaque run IDs unavailable; report does not claim the implementation gate passed.',
    },
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
safe_destination(REPORT)
with REPORT.open('x', encoding='utf-8') as output:
    json.dump(report, output, indent=2, ensure_ascii=False)
    output.write('\n')
print(json.dumps({
    'status': report['status'], 'counts': report['counts'],
    'import_report': str(REPORT), 'import_report_sha256': file_digest(REPORT),
    'started_at_utc': report['started_at_utc'], 'finished_at_utc': report['finished_at_utc'],
    'all_mapped_bytes_preserved': all(plan['byte_preserved'] for plan in plans),
    'all_protected_files_unchanged': all(row['unchanged'] for row in preserved_before),
}, indent=2))
