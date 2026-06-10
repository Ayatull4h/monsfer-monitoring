import ast
import logging
from pathlib import Path

# Konfigurasi
APP_FILE = 'app.py'
REQUIREMENTS_TXT = 'requirements.txt'
REQUIREMENTS_WITH_VERSIONS_TXT = 'requirements_with_versions.txt'

# Daftar modul standar Python (tidak perlu diinstal)
STDLIB_MODULES = {
    'os', 'sys', 'json', 'csv', 'datetime', 'random', 're', 'platform',
    'logging', 'argparse', 'subprocess', 'time', 'pathlib', 'getopt',
    'inspect', 'functools', 'itertools', 'collections', 'math', 'heapq',
    '__future__', 'abc', 'warnings', 'types', 'errno', 'fnmatch', 'io',
    'tempfile', 'glob', 'shutil', 'stat', 'traceback', 'signal', 'atexit'
}

# Mapping manual dari modul ke package pip
MODULE_TO_PACKAGE_MAP = {
    'flask_sqlalchemy': 'Flask-SQLAlchemy',
    'flask_cors': 'flask-cors',
    'flask_wtf': 'Flask-WTF',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'psutil': 'psutil',
    'werkzeug': 'Werkzeug',
    'click': 'Click',
    'jinja2': 'Jinja2',
    'itsdangerous': 'itsdangerous',
    'pkg_resources': 'setuptools',
    'distutils': 'setuptools',
    'email': 'email',
    'http': 'http',
    'ssl': 'pyOpenSSL',
    'uuid': 'pywin32'  # Hanya untuk Windows
}

def extract_imports_from_file(file_path):
    """Ekstrak semua modul yang diimpor dari file Python."""
    imports = set()
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            node = ast.parse(f.read(), filename=file_path)

        for n in ast.walk(node):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                for name in n.names:
                    module_name = name.name.split('.')[0]  # Ambil root modul
                    if module_name not in STDLIB_MODULES:
                        imports.add(module_name)
    except Exception as e:
        logging.warning(f"Gagal membaca file {file_path}: {e}")
    return imports

def resolve_package_names(import_set):
    """Cocokkan nama modul dengan package pip."""
    resolved = set()
    for imp in import_set:
        resolved.add(MODULE_TO_PACKAGE_MAP.get(imp, imp))
    return sorted(resolved)

def get_installed_versions(package_list):
    """Dapatkan versi terinstall dari setiap package."""
    import importlib.metadata
    versions = {}
    for package in package_list:
        try:
            dist = importlib.metadata.distribution(package)
            versions[package] = dist.version
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions

def write_requirements(requirements_list, output_file, include_versions=False):
    """Tulis requirements ke file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for req in requirements_list:
            if include_versions:
                version = req[1]
                line = f"{req[0]}=={version}" if version else req[0]
            else:
                line = req
            f.write(line + "\n")
    print(f"[+] File berhasil dibuat: {output_file}")

def main():
    print("[*] Memulai pemindaian dependensi dari app.py...")
    project_dir = Path(APP_FILE).parent.resolve()

    # Ekstrak semua import dari app.py
    all_imports = extract_imports_from_file(APP_FILE)

    print(f"[+] Menemukan {len(all_imports)} modul yang digunakan:")
    for imp in sorted(all_imports):
        print(f"   - {imp}")

    # Resolusi ke nama package pip
    dependencies = resolve_package_names(all_imports)

    # Simpan ke requirements.txt (hanya nama modul)
    write_requirements(dependencies, REQUIREMENTS_TXT)

    # Dapatkan versi terinstall
    dependency_versions = get_installed_versions(dependencies)

    # Buat list (nama, versi) untuk file versi lengkap
    dep_with_versions = [(name, dependency_versions[name]) for name in dependencies]

    # Simpan ke requirements_with_versions.txt
    write_requirements(dep_with_versions, REQUIREMENTS_WITH_VERSIONS_TXT, include_versions=True)

if __name__ == "__main__":
    main()