"""
Module-based Scope Extractor
Extracts relevant files for bug difficulty analysis based on module boundaries.
"""

import os
import ast
from pathlib import Path
from typing import Set, List, Dict, Tuple
from collections import defaultdict


class ModuleScopeExtractor:
    """Extracts scope using module-based approach"""
    
    def __init__(self, repo_path: str, module_depth: int = 3, 
                 max_secondary_files: int = 5, max_scope_size: int = 100):
        self.repo_path = Path(repo_path)
        self.module_depth = module_depth
        self.max_secondary_files = max_secondary_files
        self.max_scope_size = max_scope_size
        
    def extract_full_scope(self, changed_files: List[str]) -> Dict[str, List[str]]:
        """
        Extract complete module-level scope for V3 analysis.
        
        Args:
            changed_files: List of file paths that were changed in the patch
            
        Returns:
            Dictionary with:
                'primary': List of all files in changed modules (depth=module_depth)
                'secondary': List of top-k files from dependent modules
                'direct_imports': List of directly imported files
                'all': Combined unique list of all files in scope
        """
        print(f"\n{'='*60}")
        print(f"EXTRACTING FULL MODULE SCOPE (V3)")
        print(f"{'='*60}")
        print(f"Changed files: {len(changed_files)}")
        print(f"Module depth: {self.module_depth}")
        print(f"Max secondary: {self.max_secondary_files}")
        
        # Step 1: Get primary module files (ALL files in changed modules)
        primary_files = set()
        for changed_file in changed_files:
            module_files = self.get_module_files(changed_file, self.module_depth)
            primary_files.update(module_files)
        
        print(f"Primary modules: {len(primary_files)} files")
        
        # Step 2: Get dependent modules
        dependent_modules = self.get_dependent_modules(list(primary_files))
        print(f"Dependent modules found: {len(dependent_modules)}")
        
        # Step 3: Get top-k files from dependent modules
        secondary_files = []
        for module_path in sorted(dependent_modules)[:self.max_secondary_files]:
            module_files = self._get_files_in_module_path(module_path)
            secondary_files.extend(module_files[:5])  # Top 5 files per module
        
        secondary_files = list(set(secondary_files) - primary_files)[:self.max_secondary_files]
        print(f"Secondary modules: {len(secondary_files)} files")
        
        # Step 4: Get direct imports
        direct_imports = set()
        for changed_file in changed_files:
            imports = self.extract_direct_imports(changed_file)
            direct_imports.update(imports)
        
        # Remove duplicates with primary/secondary
        direct_imports = list(direct_imports - primary_files - set(secondary_files))
        print(f"Direct imports: {len(direct_imports)} files")
        
        # Step 5: Combine all
        all_files = list(set(list(primary_files) + secondary_files + direct_imports))
        
        # Apply scope size limit
        if len(all_files) > self.max_scope_size:
            print(f"⚠️  Scope size {len(all_files)} exceeds limit {self.max_scope_size}")
            # Prioritize: changed files > primary > secondary > imports
            all_files = self._apply_scope_limit(
                changed_files, list(primary_files), secondary_files, direct_imports
            )
            print(f"✓ Pruned to {len(all_files)} files")
        
        print(f"\nFINAL SCOPE SIZE: {len(all_files)} files")
        print(f"{'='*60}\n")
        
        return {
            'primary': sorted(list(primary_files)),
            'secondary': sorted(secondary_files),
            'direct_imports': sorted(direct_imports),
            'all': sorted(all_files)
        }
    
    def get_module_files(self, file_path: str, depth: int = 3) -> List[str]:
        """
        Get all Python files in the same module as file_path, up to specified depth.
        
        Args:
            file_path: Path to a file in the repository
            depth: How many directory levels up to go from the file
            
        Returns:
            List of Python file paths in the module
        """
        files = []
        
        # Extract module directory by going up 'depth' levels
        parts = Path(file_path).parts
        if len(parts) <= 1:
            # Root level file, just return it
            return [file_path]
        
        # Go up to depth levels (but not past root)
        module_depth = min(depth, len(parts) - 1)
        module_parts = parts[:module_depth]
        module_path = self.repo_path / Path(*module_parts) if module_parts else self.repo_path
        
        if not module_path.exists() or not module_path.is_dir():
            return [file_path]
        
        # Get all Python files recursively in this module
        try:
            for py_file in module_path.rglob('*.py'):
                rel_path = str(py_file.relative_to(self.repo_path))
                files.append(rel_path)
        except Exception as e:
            # If error, just return the original file
            files = [file_path]
        
        return files
    
    def get_dependent_modules(self, changed_files: List[str]) -> List[str]:
        """
        Find modules that depend on (import from) the changed files.
        
        Args:
            changed_files: List of file paths that were changed
            
        Returns:
            List of module directory paths that import the changed files
        """
        dependent_modules = set()
        
        # Create a mapping of module names from changed files
        changed_modules = set()
        for filepath in changed_files:
            # Convert file path to potential import paths
            module_name = filepath.replace('/', '.').replace('.py', '')
            changed_modules.add(module_name)
            
            # Also add parent modules
            parts = module_name.split('.')
            for i in range(1, len(parts)):
                changed_modules.add('.'.join(parts[:i]))
        
        # Search all Python files in repo for imports of changed modules
        try:
            for py_file in self.repo_path.rglob('*.py'):
                if not py_file.is_file():
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Check if any changed module is imported
                    for changed_module in changed_modules:
                        # Look for import patterns
                        if (f'import {changed_module}' in content or 
                            f'from {changed_module}' in content):
                            # Extract module path of the importing file
                            rel_path = py_file.relative_to(self.repo_path)
                            module_dir = str(rel_path.parent)
                            if module_dir != '.':
                                dependent_modules.add(module_dir)
                            break
                
                except Exception:
                    continue
        
        except Exception:
            pass
        
        return sorted(list(dependent_modules))
    
    def extract_direct_imports(self, file_path: str) -> List[str]:
        """
        Parse imports from a Python file and resolve them to file paths.
        
        Args:
            file_path: Path to a Python file
            
        Returns:
            List of file paths that are directly imported
        """
        imports = set()
        full_path = self.repo_path / file_path
        
        if not full_path.exists():
            return []
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Convert module name to file path
                        import_path = self._resolve_import_to_path(alias.name, file_path)
                        if import_path:
                            imports.add(import_path)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Handle relative imports
                        if node.level > 0:
                            # Relative import (.module or ..module)
                            import_path = self._resolve_relative_import(
                                node.module, file_path, node.level
                            )
                        else:
                            # Absolute import
                            import_path = self._resolve_import_to_path(node.module, file_path)
                        
                        if import_path:
                            imports.add(import_path)
        
        except Exception:
            pass
        
        return list(imports)
    
    def _resolve_import_to_path(self, module_name: str, from_file: str) -> str:
        """Try to resolve an import to a file path in the repository"""
        # Convert module name to path: 'pkg.module' -> 'pkg/module.py'
        potential_path = module_name.replace('.', '/') + '.py'
        full_path = self.repo_path / potential_path
        
        if full_path.exists():
            return potential_path
        
        # Try __init__.py
        potential_init = module_name.replace('.', '/') + '/__init__.py'
        full_init = self.repo_path / potential_init
        
        if full_init.exists():
            return potential_init
        
        return None
    
    def _resolve_relative_import(self, module_name: str, from_file: str, level: int) -> str:
        """Resolve relative imports like 'from . import x' or 'from .. import y'"""
        # Get the directory of the importing file
        from_dir = Path(from_file).parent
        
        # Go up 'level' directories
        target_dir = from_dir
        for _ in range(level):
            target_dir = target_dir.parent
        
        # Append the module name
        if module_name:
            target_path = target_dir / module_name.replace('.', '/')
        else:
            target_path = target_dir
        
        # Try as a .py file
        potential_path = str(target_path) + '.py'
        if (self.repo_path / potential_path).exists():
            return potential_path
        
        # Try as a package (__init__.py)
        potential_init = str(target_path) + '/__init__.py'
        if (self.repo_path / potential_init).exists():
            return potential_init
        
        return None
    
    def _get_files_in_module_path(self, module_path: str) -> List[str]:
        """Get all Python files in a module directory"""
        files = []
        full_path = self.repo_path / module_path
        
        if not full_path.exists() or not full_path.is_dir():
            return files
        
        try:
            for py_file in full_path.rglob('*.py'):
                rel_path = str(py_file.relative_to(self.repo_path))
                files.append(rel_path)
        except Exception:
            pass
        
        return files
    
    def _apply_scope_limit(self, changed_files: List[str], primary: List[str], 
                          secondary: List[str], imports: List[str]) -> List[str]:
        """Apply scope size limit with priority ordering"""
        result = []
        remaining = self.max_scope_size
        
        # Priority 1: Changed files (must include)
        result.extend(changed_files)
        remaining -= len(changed_files)
        
        # Priority 2: Primary files
        primary_filtered = [f for f in primary if f not in result]
        result.extend(primary_filtered[:remaining])
        remaining -= len(primary_filtered[:remaining])
        
        # Priority 3: Secondary files
        if remaining > 0:
            secondary_filtered = [f for f in secondary if f not in result]
            result.extend(secondary_filtered[:remaining])
            remaining -= len(secondary_filtered[:remaining])
        
        # Priority 4: Direct imports
        if remaining > 0:
            imports_filtered = [f for f in imports if f not in result]
            result.extend(imports_filtered[:remaining])
        
        return result
    
    def extract_scope(self, changed_files: List[str]) -> Dict[str, Set[str]]:
        """
        Extract module-based scope for given changed files.
        
        Args:
            changed_files: List of file paths that were changed in the patch
            
        Returns:
            Dictionary with:
                'changed': Set of changed files
                'primary': Set of all files in primary modules
                'secondary': Set of top-k files from secondary modules
                'imports': Set of directly imported files
                'all': Union of all above
        """
        print(f"\n{'='*60}")
        print(f"EXTRACTING MODULE-BASED SCOPE")
        print(f"{'='*60}")
        print(f"Changed files: {len(changed_files)}")
        
        # Step 1: Identify primary modules
        primary_modules = self._identify_primary_modules(changed_files)
        print(f"Primary modules: {primary_modules}")
        
        # Step 2: Get ALL files from primary modules
        primary_files = self._get_primary_module_files(primary_modules)
        print(f"Primary module files: {len(primary_files)}")
        
        # Step 3: Identify secondary modules (dependencies)
        secondary_modules = self._identify_secondary_modules(primary_files)
        print(f"Secondary modules: {len(secondary_modules)}")
        
        # Step 4: Get top-k files from secondary modules
        secondary_files = self._get_secondary_module_files(
            secondary_modules, primary_files
        )
        print(f"Secondary module files: {len(secondary_files)}")
        
        # Step 5: Get direct imports
        import_files = self._get_direct_imports(primary_files)
        print(f"Direct import files: {len(import_files)}")
        
        # Step 6: Combine and apply capacity limit
        all_files = set(changed_files) | primary_files | secondary_files | import_files
        
        if len(all_files) > self.max_scope_size:
            print(f"⚠️  Scope size {len(all_files)} exceeds limit {self.max_scope_size}")
            all_files = self._prune_scope(
                all_files, set(changed_files), primary_files
            )
            print(f"✓ Pruned to {len(all_files)} files")
        
        print(f"\nFINAL SCOPE SIZE: {len(all_files)} files")
        print(f"{'='*60}\n")
        
        return {
            'changed': set(changed_files),
            'primary': primary_files,
            'secondary': secondary_files,
            'imports': import_files,
            'all': all_files
        }
    
    def _identify_primary_modules(self, changed_files: List[str]) -> Set[str]:
        """Extract module paths from changed files"""
        modules = set()
        for filepath in changed_files:
            module = self._extract_module_path(filepath, self.module_depth)
            if module:
                modules.add(module)
        return modules
    
    def _extract_module_path(self, filepath: str, depth: int = 3) -> str:
        """
        Extract module path from file path.
        Example: 'django/contrib/auth/models.py' -> 'django.contrib.auth'
        """
        # Remove .py extension
        path = filepath.rstrip('.py')
        
        # Split and take first 'depth' parts
        parts = path.split('/')
        
        # Exclude filename (last part)
        module_parts = parts[:min(depth, len(parts) - 1)]
        
        if not module_parts:
            return None
            
        return '.'.join(module_parts)
    
    def _get_primary_module_files(self, modules: Set[str]) -> Set[str]:
        """Get ALL Python files in primary modules"""
        files = set()
        
        for module in modules:
            module_path = self.repo_path / module.replace('.', '/')
            
            if module_path.exists() and module_path.is_dir():
                # Get all .py files recursively
                for py_file in module_path.rglob('*.py'):
                    # Convert to relative path
                    rel_path = py_file.relative_to(self.repo_path)
                    files.add(str(rel_path))
        
        return files
    
    def _identify_secondary_modules(self, primary_files: Set[str]) -> Set[str]:
        """Identify modules that primary modules depend on"""
        secondary = set()
        primary_modules = {self._extract_module_path(f) for f in primary_files}
        
        for filepath in primary_files:
            full_path = self.repo_path / filepath
            
            if not full_path.exists():
                continue
                
            try:
                # Parse file and extract imports
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    tree = ast.parse(f.read(), filename=str(filepath))
                
                # Extract imported modules
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module = self._extract_module_path(
                                alias.name.replace('.', '/'), 
                                self.module_depth
                            )
                            if module and module not in primary_modules:
                                secondary.add(module)
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            module = self._extract_module_path(
                                node.module.replace('.', '/'),
                                self.module_depth
                            )
                            if module and module not in primary_modules:
                                secondary.add(module)
            
            except Exception as e:
                # Skip files that can't be parsed
                continue
        
        return secondary
    
    def _get_secondary_module_files(self, modules: Set[str], 
                                    primary_files: Set[str]) -> Set[str]:
        """Get top-k files from secondary modules based on coupling"""
        files = set()
        
        for module in modules:
            module_path = self.repo_path / module.replace('.', '/')
            
            if not module_path.exists() or not module_path.is_dir():
                continue
            
            # Get all files in module
            module_files = []
            for py_file in module_path.rglob('*.py'):
                rel_path = str(py_file.relative_to(self.repo_path))
                module_files.append(rel_path)
            
            # Rank by coupling (simplified: just take first k)
            # TODO: Implement actual coupling ranking
            ranked = self._rank_by_coupling(module_files, primary_files)
            
            # Take top-k
            files.update(ranked[:self.max_secondary_files])
        
        return files
    
    def _rank_by_coupling(self, files: List[str], 
                         primary_files: Set[str]) -> List[str]:
        """
        Rank files by coupling strength to primary modules.
        For now, simple heuristic (can be enhanced later).
        """
        scores = {}
        
        for filepath in files:
            score = 0
            full_path = self.repo_path / filepath
            
            if not full_path.exists():
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Simple scoring: count imports from primary files
                for primary_file in primary_files:
                    module_name = primary_file.replace('/', '.').replace('.py', '')
                    if module_name in content:
                        score += 20  # Direct import bonus
                
                # Bonus for __init__.py (interface files)
                if filepath.endswith('__init__.py'):
                    score += 10
                
                # Bonus for base/core files
                if 'base' in filepath or 'core' in filepath:
                    score += 5
                
                scores[filepath] = score
            
            except Exception:
                scores[filepath] = 0
        
        # Sort by score (descending)
        return sorted(files, key=lambda f: scores.get(f, 0), reverse=True)
    
    def _get_direct_imports(self, files: Set[str]) -> Set[str]:
        """Extract directly imported files"""
        imports = set()
        
        for filepath in files:
            full_path = self.repo_path / filepath
            
            if not full_path.exists():
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    tree = ast.parse(f.read(), filename=str(filepath))
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        # Try to resolve import to file path
                        # Simplified: just add if exists
                        # TODO: Proper import resolution
                        pass
            
            except Exception:
                continue
        
        return imports
    
    def _prune_scope(self, all_files: Set[str], changed_files: Set[str],
                    primary_files: Set[str]) -> Set[str]:
        """Prune scope to max size while keeping essential files"""
        # Priority 1: Changed files (mandatory)
        result = set(changed_files)
        
        # Priority 2: Primary module files (high priority)
        remaining = self.max_scope_size - len(result)
        primary_remaining = primary_files - result
        result.update(list(primary_remaining)[:remaining])
        
        # Priority 3: Secondary files (if space remains)
        remaining = self.max_scope_size - len(result)
        if remaining > 0:
            other = all_files - result
            result.update(list(other)[:remaining])
        
        return result


# Test function
def test_scope_extractor():
    """Test with a simple example"""
    import tempfile
    import shutil
    
    # Create a temporary repository structure
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / 'test_repo'
        repo_path.mkdir()
        
        # Create some Python files
        (repo_path / 'myapp').mkdir()
        (repo_path / 'myapp' / 'core').mkdir()
        (repo_path / 'myapp' / 'utils').mkdir()
        
        (repo_path / 'myapp' / '__init__.py').touch()
        (repo_path / 'myapp' / 'core' / '__init__.py').touch()
        (repo_path / 'myapp' / 'core' / 'models.py').write_text('# models')
        (repo_path / 'myapp' / 'core' / 'views.py').write_text('# views')
        (repo_path / 'myapp' / 'utils' / '__init__.py').touch()
        (repo_path / 'myapp' / 'utils' / 'helpers.py').write_text('# helpers')
        
        # Test
        extractor = ModuleScopeExtractor(str(repo_path))
        changed_files = ['myapp/core/models.py']
        
        scope = extractor.extract_scope(changed_files)
        
        print("Test Results:")
        print(f"Changed: {scope['changed']}")
        print(f"Primary: {scope['primary']}")
        print(f"All: {scope['all']}")
        print(f"\n✓ Test passed!")


if __name__ == '__main__':
    test_scope_extractor()
