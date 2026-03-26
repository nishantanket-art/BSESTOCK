import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

def test_import(module_path):
    print(f"Testing import of {module_path}...")
    try:
        __import__(module_path)
        print(f" [OK] {module_path} imported successfully")
    except SystemExit as se:
        print(f" [FATAL] {module_path} raised SystemExit: {se}")
    except Exception as e:
        print(f" [ERROR] {module_path} failed: {e}")

if __name__ == "__main__":
    test_import("backend.config")
    test_import("backend.database")
    test_import("backend.services.scheduler")
    test_import("backend.routers.auth")
    test_import("backend.routers.stocks")
    test_import("backend.routers.watchlist")
    test_import("backend.routers.alerts")
    test_import("backend.routers.scanner")
    print("\nImport tests complete.")
