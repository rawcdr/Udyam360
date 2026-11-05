"""Environment and Hardware Verification Script for Udyam360.

Verifies Python version, package imports, pip version, OS, CPU, RAM,
and NVIDIA GPU information.
"""

import sys
import platform
import subprocess
import shutil

REQUIRED_IMPORTS = [
    ("google.genai", "google-genai"),
    ("dotenv", "python-dotenv"),
    ("fastapi", "fastapi"),
    ("pydantic", "pydantic"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("sklearn", "scikit-learn"),
    ("PIL", "pillow"),
    ("pytest", "pytest"),
    ("httpx", "httpx"),
    ("openpyxl", "openpyxl"),
]


def test_imports():
    results = {}
    for module_name, pkg_name in REQUIRED_IMPORTS:
        try:
            mod = __import__(module_name)
            ver = getattr(mod, "__version__", "installed")
            results[pkg_name] = {"status": "SUCCESS", "version": str(ver)}
        except Exception as e:
            results[pkg_name] = {"status": "FAILED", "error": str(e)}
    return results


def get_pip_version():
    try:
        out = subprocess.check_output([sys.executable, "-m", "pip", "--version"], text=True)
        return out.strip()
    except Exception as e:
        return f"Error: {e}"


def get_hardware_info():
    info = {
        "os": platform.platform(),
        "python": sys.version,
        "processor": platform.processor(),
        "architecture": platform.architecture()[0],
    }

    # GPU
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                text=True,
            )
            info["gpu"] = out.strip()
        except Exception as e:
            info["gpu"] = f"nvidia-smi failed: {e}"
    else:
        info["gpu"] = "Not available"

    return info


def main():
    print("=== UDYAM360 ENVIRONMENT VERIFICATION ===")
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    print(f"Pip: {get_pip_version()}")
    print(f"OS: {platform.platform()}")

    hw = get_hardware_info()
    print(f"Hardware - CPU: {hw['processor']}")
    print(f"Hardware - GPU: {hw['gpu']}")

    print("\n--- Package Verification ---")
    imports = test_imports()
    all_ok = True
    for pkg, res in imports.items():
        if res["status"] == "SUCCESS":
            print(f"  [OK] {pkg}: {res['version']}")
        else:
            print(f"  [FAIL] {pkg}: {res['error']}")
            all_ok = False

    if all_ok:
        print("\nAll required packages imported successfully!")
    else:
        print("\nSome packages failed to import.")


if __name__ == "__main__":
    main()

