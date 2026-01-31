#!/usr/bin/env python
"""Build script for Custom Autocorrect.

This script:
1. Cleans previous build artifacts
2. Runs tests to verify the codebase
3. Generates icon files if missing
4. Runs PyInstaller to create the executable
5. Reports the build output

Usage:
    python build.py           # Full build with tests
    python build.py --no-test # Skip tests (faster, for iteration)
    python build.py --clean   # Clean only, no build
"""

import shutil
import subprocess
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent


def clean_build(root: Path) -> None:
    """Remove previous build artifacts."""
    for folder in ['dist', 'build']:
        path = root / folder
        if path.exists():
            print(f"Cleaning {folder}/...")
            shutil.rmtree(path)

    # Also clean PyInstaller work files
    for pattern in ['*.pyc', '*.pyo', '__pycache__']:
        for match in root.rglob(pattern):
            if match.is_file():
                match.unlink()
            elif match.is_dir():
                shutil.rmtree(match)


def run_tests(root: Path) -> bool:
    """Run the test suite.

    Returns:
        True if tests pass, False otherwise.
    """
    print("\n" + "=" * 50)
    print("Running tests...")
    print("=" * 50 + "\n")

    result = subprocess.run(
        [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short'],
        cwd=root
    )

    return result.returncode == 0


def generate_icons(root: Path) -> bool:
    """Generate icon files if they don't exist.

    Returns:
        True if successful, False otherwise.
    """
    resources = root / 'resources'
    png_path = resources / 'icon.png'
    ico_path = resources / 'icon.ico'

    if png_path.exists() and ico_path.exists():
        print("Icons already exist, skipping generation")
        return True

    print("\n" + "=" * 50)
    print("Generating icons...")
    print("=" * 50 + "\n")

    result = subprocess.run(
        [sys.executable, str(resources / 'create_icon.py')],
        cwd=root
    )

    if result.returncode != 0:
        print("Warning: Icon generation failed")
        return False

    return True


def run_pyinstaller(root: Path) -> bool:
    """Run PyInstaller to create the executable.

    Returns:
        True if successful, False otherwise.
    """
    print("\n" + "=" * 50)
    print("Building executable with PyInstaller...")
    print("=" * 50 + "\n")

    spec_file = root / 'CustomAutocorrect.spec'
    if not spec_file.exists():
        print(f"Error: Spec file not found: {spec_file}")
        return False

    result = subprocess.run(
        [sys.executable, '-m', 'PyInstaller', '--clean', str(spec_file)],
        cwd=root
    )

    return result.returncode == 0


def verify_build(root: Path) -> bool:
    """Verify the build output exists and report details.

    Returns:
        True if exe exists, False otherwise.
    """
    exe_path = root / 'dist' / 'CustomAutocorrect.exe'

    print("\n" + "=" * 50)
    print("Build verification")
    print("=" * 50 + "\n")

    if not exe_path.exists():
        print(f"Error: Executable not found at {exe_path}")
        return False

    size_bytes = exe_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    print(f"SUCCESS: Build complete!")
    print(f"  Output: {exe_path}")
    print(f"  Size: {size_mb:.1f} MB ({size_bytes:,} bytes)")
    print()

    if size_mb > 50:
        print("Warning: Executable is larger than expected (>50 MB)")
        print("  Consider reviewing excluded packages in the spec file")

    return True


def main() -> int:
    """Main build process.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    root = get_project_root()

    # Parse arguments
    skip_tests = '--no-test' in sys.argv or '--no-tests' in sys.argv
    clean_only = '--clean' in sys.argv

    print("=" * 50)
    print("Custom Autocorrect Build Script")
    print("=" * 50)
    print(f"Project root: {root}")
    print()

    # Step 1: Clean
    clean_build(root)

    if clean_only:
        print("Clean complete.")
        return 0

    # Step 2: Run tests (unless skipped)
    if not skip_tests:
        if not run_tests(root):
            print("\n" + "!" * 50)
            print("BUILD ABORTED: Tests failed")
            print("!" * 50)
            print("\nFix failing tests or use --no-test to skip")
            return 1
    else:
        print("\nSkipping tests (--no-test)")

    # Step 3: Generate icons
    generate_icons(root)

    # Step 4: Run PyInstaller
    if not run_pyinstaller(root):
        print("\n" + "!" * 50)
        print("BUILD FAILED: PyInstaller error")
        print("!" * 50)
        return 1

    # Step 5: Verify
    if not verify_build(root):
        return 1

    print("\n" + "=" * 50)
    print("Build successful!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Test the executable: dist\\CustomAutocorrect.exe")
    print("2. Create GitHub release with the exe attached")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
