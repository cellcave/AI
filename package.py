"""Package source, built output, hidden deployment files and QA evidence."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parent
archive = root.parent / "SAVE-SUPPLIERS-CORRECTED-FULL-WEBSITE.zip"
with ZipFile(archive, 'w', ZIP_DEFLATED) as output:
    for file in sorted(root.rglob('*')):
        relative = file.relative_to(root)
        if any(part in ('__pycache__', '.git', 'node_modules', '.qa-dist') for part in relative.parts): continue
        if relative.parts[0] == 'qa':
            include_report = relative.as_posix() == 'qa/architecture/browser-report.json'
            include_production = len(relative.parts) >= 3 and relative.parts[1] == 'production'
            if not include_report and not include_production: continue
        if file.is_file(): output.write(file, relative.as_posix())
    # Ready-rendered pages at ZIP root: extract and upload the contents directly.
    for file in sorted((root / 'dist').rglob('*')):
        if file.is_file(): output.write(file, file.relative_to(root / 'dist').as_posix())
with ZipFile(archive) as output:
    assert output.testzip() is None, 'Corrupted ZIP'
    for required in ('index.html', 'assets/site.css', 'apps/index.html', 'dist/index.html', 'src/apps.json', '.github/workflows/deploy-pages.yml', '.nojekyll'):
        assert required in output.namelist(), required
    assert not any(name.startswith('.qa-dist/') for name in output.namelist())
    assert not any('all-document-reader' in name or 'vape-less' in name for name in output.namelist())
    print(f'ZIP verified: {len(output.namelist())} files, {archive.stat().st_size:,} bytes\n{archive}')
