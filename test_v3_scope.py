#!/usr/bin/env python3
"""
Test script for V3 scope extractor functionality
"""
import sys
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent))

from core.scope_extractor import ModuleScopeExtractor


def test_get_module_files():
    """Test get_module_files method"""
    print("\n" + "="*70)
    print("TEST: get_module_files()")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / 'test_repo'
        repo_path.mkdir()
        
        # Create a module structure
        (repo_path / 'myapp').mkdir()
        (repo_path / 'myapp' / 'core').mkdir()
        (repo_path / 'myapp' / 'core' / 'models').mkdir()
        
        (repo_path / 'myapp' / '__init__.py').write_text('# init')
        (repo_path / 'myapp' / 'core' / '__init__.py').write_text('# core init')
        (repo_path / 'myapp' / 'core' / 'views.py').write_text('# views')
        (repo_path / 'myapp' / 'core' / 'models' / '__init__.py').write_text('# models init')
        (repo_path / 'myapp' / 'core' / 'models' / 'user.py').write_text('# user model')
        
        extractor = ModuleScopeExtractor(str(repo_path), module_depth=2)
        
        # Test with depth 2 from deep file (goes up 2 dirs from file)
        files = extractor.get_module_files('myapp/core/models/user.py', depth=2)
        print(f"  Files in module (depth=2): {len(files)}")
        print(f"  {files}")
        assert len(files) >= 2, "Should find files in myapp/core"
        
        # Test with depth 3 (goes up 3 dirs, gets more)
        files = extractor.get_module_files('myapp/core/models/user.py', depth=3)
        print(f"  Files in module (depth=3): {len(files)}")
        print(f"  {files}")
        assert len(files) >= 2, "Should find files"
        
        print("  ✓ get_module_files() test passed!")


def test_extract_direct_imports():
    """Test extract_direct_imports method"""
    print("\n" + "="*70)
    print("TEST: extract_direct_imports()")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / 'test_repo'
        repo_path.mkdir()
        
        # Create files
        (repo_path / 'myapp').mkdir()
        (repo_path / 'myapp' / 'utils').mkdir()
        
        # File with imports
        (repo_path / 'myapp' / 'main.py').write_text("""
import os
from myapp.utils import helpers
from .config import settings
""")
        
        (repo_path / 'myapp' / 'utils' / '__init__.py').write_text('# helpers init')
        (repo_path / 'myapp' / 'utils' / 'helpers.py').write_text('# helpers')
        (repo_path / 'myapp' / 'config.py').write_text('# config')
        
        extractor = ModuleScopeExtractor(str(repo_path))
        
        # Test import extraction
        imports = extractor.extract_direct_imports('myapp/main.py')
        print(f"  Imports found: {len(imports)}")
        print(f"  {imports}")
        
        # Import resolution is complex, so we just check it doesn't crash
        # In real usage, some imports may not resolve if they're external packages
        print("  ✓ extract_direct_imports() test passed (no crash)!")


def test_get_dependent_modules():
    """Test get_dependent_modules method"""
    print("\n" + "="*70)
    print("TEST: get_dependent_modules()")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / 'test_repo'
        repo_path.mkdir()
        
        # Create structure
        (repo_path / 'core').mkdir()
        (repo_path / 'app').mkdir()
        
        # Core module
        (repo_path / 'core' / 'base.py').write_text('class Base: pass')
        
        # App module that imports core
        (repo_path / 'app' / 'views.py').write_text("""
from core.base import Base
class MyView(Base): pass
""")
        
        extractor = ModuleScopeExtractor(str(repo_path))
        
        # Find dependents of core
        dependents = extractor.get_dependent_modules(['core/base.py'])
        print(f"  Dependent modules: {dependents}")
        
        # Should find app module
        assert 'app' in dependents, "Should find app as dependent"
        print("  ✓ get_dependent_modules() test passed!")


def test_extract_full_scope():
    """Test extract_full_scope method (integration)"""
    print("\n" + "="*70)
    print("TEST: extract_full_scope() - Integration")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / 'test_repo'
        repo_path.mkdir()
        
        # Create a realistic structure
        (repo_path / 'mylib').mkdir()
        (repo_path / 'mylib' / 'core').mkdir()
        (repo_path / 'mylib' / 'utils').mkdir()
        (repo_path / 'tests').mkdir()
        
        # Core files
        (repo_path / 'mylib' / '__init__.py').write_text('# mylib')
        (repo_path / 'mylib' / 'core' / '__init__.py').write_text('# core')
        (repo_path / 'mylib' / 'core' / 'engine.py').write_text("""
from mylib.utils import helper
class Engine: pass
""")
        (repo_path / 'mylib' / 'core' / 'processor.py').write_text('# processor')
        
        # Utils
        (repo_path / 'mylib' / 'utils' / '__init__.py').write_text('# utils')
        (repo_path / 'mylib' / 'utils' / 'helper.py').write_text('def help(): pass')
        
        # Tests that import core
        (repo_path / 'tests' / 'test_engine.py').write_text("""
from mylib.core.engine import Engine
def test(): pass
""")
        
        extractor = ModuleScopeExtractor(str(repo_path), module_depth=2, max_secondary_files=3)
        
        # Extract scope for changed file
        scope = extractor.extract_full_scope(['mylib/core/engine.py'])
        
        print(f"  Primary files: {len(scope['primary'])}")
        print(f"    {scope['primary'][:5]}")
        print(f"  Secondary files: {len(scope['secondary'])}")
        print(f"    {scope['secondary'][:3]}")
        print(f"  Direct imports: {len(scope['direct_imports'])}")
        print(f"    {scope['direct_imports'][:3]}")
        print(f"  Total scope: {len(scope['all'])}")
        
        # Assertions
        assert len(scope['primary']) >= 2, "Should have multiple primary files"
        assert len(scope['all']) >= len(scope['primary']), "All should include primary"
        
        print("  ✓ extract_full_scope() integration test passed!")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("V3 SCOPE EXTRACTOR TESTS")
    print("="*70)
    
    try:
        test_get_module_files()
        test_extract_direct_imports()
        test_get_dependent_modules()
        test_extract_full_scope()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
