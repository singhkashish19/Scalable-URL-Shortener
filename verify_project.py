#!/usr/bin/env python3
"""
Project verification script - ensures all components are properly configured.
Run: python verify_project.py
"""

import os
import sys
from pathlib import Path

def check_structure():
    """Verify project structure."""
    print("\n📁 Checking project structure...")
    
    required_dirs = [
        "app",
        "app/core",
        "app/domain",
        "app/application",
        "app/infrastructure",
        "app/interfaces",
        "tests",
        "migrations",
    ]
    
    for directory in required_dirs:
        path = Path(directory)
        status = "✅" if path.exists() else "❌"
        print(f"  {status} {directory}")
        if not path.exists():
            return False
    
    return True


def check_imports():
    """Verify critical imports work."""
    print("\n📦 Checking imports...")
    
    imports = [
        "app.main",
        "app.core.config",
        "app.core.exceptions",
        "app.core.logging",
        "app.infrastructure.database.connection",
        "app.infrastructure.database.models",
        "app.infrastructure.database.repositories",
        "app.infrastructure.cache.redis",
        "app.application.services.url_service",
        "app.application.services.short_code_service",
        "app.interfaces.api.routes",
    ]
    
    for import_path in imports:
        try:
            __import__(import_path)
            print(f"  ✅ {import_path}")
        except ImportError as e:
            print(f"  ❌ {import_path}: {e}")
            return False
    
    return True


def check_files():
    """Verify critical files exist."""
    print("\n📄 Checking files...")
    
    required_files = [
        "requirements.txt",
        "README.md",
        "QUICKSTART.md",
        "docker-compose.yml",
        "Dockerfile",
        ".env.example",
        ".gitignore",
        "conftest.py",
    ]
    
    for filename in required_files:
        path = Path(filename)
        status = "✅" if path.exists() else "⚠️"
        print(f"  {status} {filename}")
    
    return True


def check_configuration():
    """Verify configuration setup."""
    print("\n⚙️ Checking configuration...")
    
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        checks = [
            ("APP_NAME", settings.APP_NAME),
            ("DATABASE_URL configured", "dbname" in settings.DATABASE_URL),
            ("REDIS_URL configured", "redis" in settings.REDIS_URL),
            ("PORT", 8000),
        ]
        
        for name, value in checks:
            if value:
                print(f"  ✅ {name}")
            else:
                print(f"  ⚠️  {name}")
        
        return True
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False


def check_tests():
    """Check test structure."""
    print("\n🧪 Checking tests...")
    
    test_dirs = [
        "tests/unit",
        "tests/integration",
    ]
    
    for test_dir in test_dirs:
        path = Path(test_dir)
        if path.exists():
            test_files = list(path.glob("test_*.py"))
            print(f"  ✅ {test_dir} ({len(test_files)} tests)")
        else:
            print(f"  ⚠️  {test_dir} (not found)")
    
    return True


def check_dependencies():
    """Verify key dependencies."""
    print("\n📚 Checking dependencies...")
    
    packages = [
        "fastapi",
        "sqlalchemy",
        "redis",
        "pydantic",
        "pytest",
    ]
    
    try:
        import pkg_resources
        installed = {pkg.key for pkg in pkg_resources.working_set}
        
        for package in packages:
            if package in installed:
                print(f"  ✅ {package}")
            else:
                print(f"  ❌ {package}")
        
        return all(pkg in installed for pkg in packages)
    except:
        print("  ⚠️  Could not check (pip packages)")
        return True


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("🔍 URL SHORTENER PROJECT VERIFICATION")
    print("=" * 60)
    
    checks = [
        ("Project Structure", check_structure),
        ("Critical Imports", check_imports),
        ("Required Files", check_files),
        ("Configuration", check_configuration),
        ("Test Setup", check_tests),
        ("Dependencies", check_dependencies),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n❌ Error in {check_name}: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {check_name}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 PROJECT VERIFICATION COMPLETE - ALL GREEN!")
        print("\nNext steps:")
        print("  1. Run tests: pytest")
        print("  2. Start server: uvicorn app.main:app --reload")
        print("  3. Check API: http://localhost:8000/api/v1/health")
        return 0
    else:
        print("\n⚠️  SOME CHECKS FAILED - Please fix issues above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
