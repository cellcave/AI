"""Package source, built output, hidden deployment files and QA evidence."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parent
archive = root.parent / "SAVE-SUPPLIERS-GITHUB-PAGES-READY.zip"
with ZipFile(archive, 'w', ZIP_DEFLATED) as output:
    for file in sorted(root.rglob('*')):
        if file.is_file() and not any(part in ('__pycache__', '.git', 'node_modules') for part in file.relative_to(root).parts):
            output.write(file, Path('save-suppliers') / file.relative_to(root))
with ZipFile(archive) as output:
    assert output.testzip() is None, 'Corrupted ZIP'
    for required in ('dist/index.html', 'src/apps.json', '.github/workflows/deploy-pages.yml', 'dist/.nojekyll'):
        assert 'save-suppliers/' + required in output.namelist(), required
    print(f'ZIP verified: {len(output.namelist())} files, {archive.stat().st_size:,} bytes\n{archive}')
