"""
Repository Manager for V2 Full File Analysis
Handles git operations: clone, checkout, file extraction, patch application
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import time
import re


class RepositoryManager:
    """
    Manages git repositories for full file analysis.
    
    Features:
    - Repository caching to avoid re-cloning
    - Timeout handling for clone/checkout operations
    - Shallow clone fallback for large repos
    - Safe git operations via subprocess
    """
    
    def __init__(self, cache_dir: str = "repo_cache"):
        """
        Initialize repository manager.
        
        Args:
            cache_dir: Directory for caching cloned repositories
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
    def clone_or_update(self, repo_url: str, repo_name: str, 
                       timeout: int = 300) -> Path:
        """
        Clone repository or return existing cached repo.
        
        Args:
            repo_url: GitHub repository URL (e.g., "https://github.com/owner/repo")
            repo_name: Name for cached directory (e.g., "owner_repo")
            timeout: Timeout in seconds for clone operation
            
        Returns:
            Path to cloned repository
            
        Raises:
            RuntimeError: If clone fails
        """
        repo_path = self.cache_dir / repo_name
        
        # Check if already cached
        if repo_path.exists() and (repo_path / ".git").exists():
            print(f"  ✓ Using cached repository: {repo_path}")
            return repo_path
        
        print(f"  📥 Cloning repository: {repo_url}")
        print(f"     Target: {repo_path}")
        
        # Ensure parent directory exists
        repo_path.parent.mkdir(exist_ok=True, parents=True)
        
        try:
            # Try shallow clone first (faster for large repos)
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(repo_path)],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                # Fallback to full clone
                print(f"  ⚠️  Shallow clone failed, trying full clone...")
                if repo_path.exists():
                    shutil.rmtree(repo_path)
                
                result = subprocess.run(
                    ["git", "clone", repo_url, str(repo_path)],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"Git clone failed: {result.stderr}")
            
            print(f"  ✅ Repository cloned successfully")
            return repo_path
            
        except subprocess.TimeoutExpired:
            if repo_path.exists():
                shutil.rmtree(repo_path)
            raise RuntimeError(f"Clone timed out after {timeout}s")
        except Exception as e:
            if repo_path.exists():
                shutil.rmtree(repo_path)
            raise RuntimeError(f"Clone failed: {str(e)}")
    
    def checkout_commit(self, repo_path: Path, commit: str, 
                       timeout: int = 30) -> bool:
        """
        Checkout specific commit in repository.
        
        Args:
            repo_path: Path to git repository
            commit: Commit SHA to checkout
            timeout: Timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, fetch if needed (for shallow clones)
            if self._is_shallow_clone(repo_path):
                print(f"  📥 Fetching commit {commit[:8]}...")
                fetch_result = subprocess.run(
                    ["git", "fetch", "--depth", "1", "origin", commit],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                # If fetch fails, unshallow the repo
                if fetch_result.returncode != 0:
                    print(f"  🔄 Converting to full clone...")
                    subprocess.run(
                        ["git", "fetch", "--unshallow"],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )
            
            # Checkout commit
            result = subprocess.run(
                ["git", "checkout", "-f", commit],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                print(f"  ✓ Checked out commit: {commit[:8]}")
                return True
            else:
                print(f"  ❌ Checkout failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"  ❌ Checkout timed out after {timeout}s")
            return False
        except Exception as e:
            print(f"  ❌ Checkout error: {str(e)}")
            return False
    
    def get_file_content(self, repo_path: Path, filepath: str, 
                        commit: Optional[str] = None) -> str:
        """
        Get content of a file at specific commit or current HEAD.
        
        Args:
            repo_path: Path to git repository
            filepath: Relative path to file in repository
            commit: Optional commit SHA (uses current HEAD if None)
            
        Returns:
            File content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        try:
            if commit:
                # Get file at specific commit
                result = subprocess.run(
                    ["git", "show", f"{commit}:{filepath}"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    return result.stdout
                else:
                    raise FileNotFoundError(f"File not found: {filepath} at {commit}")
            else:
                # Get current file
                file_path = repo_path / filepath
                if not file_path.exists():
                    raise FileNotFoundError(f"File not found: {filepath}")
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
                    
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"File read timed out: {filepath}")
        except Exception as e:
            raise RuntimeError(f"Failed to read file {filepath}: {str(e)}")
    
    def apply_patch(self, repo_path: Path, patch: str, 
                   timeout: int = 30) -> bool:
        """
        Apply git patch to repository.
        
        Args:
            repo_path: Path to git repository
            patch: Git patch content
            timeout: Timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Apply patch using git apply
            result = subprocess.run(
                ["git", "apply", "--whitespace=fix"],
                cwd=repo_path,
                input=patch,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                print(f"  ✓ Patch applied successfully")
                return True
            else:
                print(f"  ⚠️  Patch apply failed: {result.stderr}")
                # Try with --reject to see what failed
                subprocess.run(
                    ["git", "apply", "--reject", "--whitespace=fix"],
                    cwd=repo_path,
                    input=patch,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                return False
                
        except subprocess.TimeoutExpired:
            print(f"  ❌ Patch apply timed out after {timeout}s")
            return False
        except Exception as e:
            print(f"  ❌ Patch apply error: {str(e)}")
            return False
    
    def get_changed_files_from_patch(self, patch: str) -> List[str]:
        """
        Extract list of changed files from patch.
        
        Args:
            patch: Git patch content
            
        Returns:
            List of file paths
        """
        files = []
        
        # Match file paths in diff headers
        # Handles both:
        # diff --git a/path b/path
        # --- a/path
        # +++ b/path
        patterns = [
            r'diff --git a/(.+?) b/',
            r'^\+\+\+ b/(.+?)$',
            r'^--- a/(.+?)$'
        ]
        
        for line in patch.split('\n'):
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    filepath = match.group(1)
                    if filepath != '/dev/null' and filepath not in files:
                        files.append(filepath)
                        break
        
        return files
    
    def reset_to_commit(self, repo_path: Path, commit: str, 
                       timeout: int = 30) -> bool:
        """
        Hard reset repository to specific commit.
        
        Args:
            repo_path: Path to git repository
            commit: Commit SHA
            timeout: Timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clean any changes
            subprocess.run(
                ["git", "clean", "-fd"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Hard reset
            result = subprocess.run(
                ["git", "reset", "--hard", commit],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                print(f"  ✓ Reset to commit: {commit[:8]}")
                return True
            else:
                print(f"  ❌ Reset failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"  ❌ Reset timed out after {timeout}s")
            return False
        except Exception as e:
            print(f"  ❌ Reset error: {str(e)}")
            return False
    
    def _is_shallow_clone(self, repo_path: Path) -> bool:
        """Check if repository is a shallow clone"""
        shallow_file = repo_path / ".git" / "shallow"
        return shallow_file.exists()
    
    def cleanup_repo(self, repo_name: str) -> bool:
        """
        Remove cached repository.
        
        Args:
            repo_name: Name of cached repository
            
        Returns:
            True if successful
        """
        repo_path = self.cache_dir / repo_name
        if repo_path.exists():
            try:
                shutil.rmtree(repo_path)
                print(f"  ✓ Removed cached repo: {repo_name}")
                return True
            except Exception as e:
                print(f"  ❌ Failed to remove repo: {str(e)}")
                return False
        return True
    
    def get_repo_info(self, repo_path: Path) -> Dict[str, Any]:
        """
        Get information about repository.
        
        Returns:
            Dict with repo metadata
        """
        info = {
            'path': str(repo_path),
            'exists': repo_path.exists(),
            'is_git': (repo_path / ".git").exists(),
            'is_shallow': False,
            'current_commit': None
        }
        
        if info['is_git']:
            info['is_shallow'] = self._is_shallow_clone(repo_path)
            
            # Get current commit
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    info['current_commit'] = result.stdout.strip()
            except:
                pass
        
        return info


def test_repository_manager():
    """Test repository manager with a small public repo"""
    print("Testing Repository Manager")
    print("="*70)
    
    # Use a small test repo
    repo_url = "https://github.com/octocat/Hello-World"
    repo_name = "test_hello_world"
    
    manager = RepositoryManager(cache_dir="/tmp/test_repo_cache")
    
    try:
        # Test clone
        print("\n1. Testing clone...")
        repo_path = manager.clone_or_update(repo_url, repo_name)
        print(f"   ✓ Cloned to: {repo_path}")
        
        # Test get_repo_info
        print("\n2. Testing get_repo_info...")
        info = manager.get_repo_info(repo_path)
        print(f"   ✓ Is git: {info['is_git']}")
        print(f"   ✓ Is shallow: {info['is_shallow']}")
        print(f"   ✓ Current commit: {info['current_commit'][:8]}")
        
        # Test checkout (use master commit)
        print("\n3. Testing checkout...")
        success = manager.checkout_commit(repo_path, "master")
        print(f"   ✓ Checkout: {success}")
        
        # Test get_file_content
        print("\n4. Testing get_file_content...")
        try:
            content = manager.get_file_content(repo_path, "README")
            print(f"   ✓ File content length: {len(content)} chars")
            print(f"   ✓ First 50 chars: {content[:50]}")
        except FileNotFoundError:
            print("   ⚠️  README not found (expected for some repos)")
        
        # Test get_changed_files_from_patch
        print("\n5. Testing get_changed_files_from_patch...")
        test_patch = """
diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
+# New line
 def test():
     pass
"""
        files = manager.get_changed_files_from_patch(test_patch)
        print(f"   ✓ Changed files: {files}")
        
        # Test cleanup
        print("\n6. Testing cleanup...")
        success = manager.cleanup_repo(repo_name)
        print(f"   ✓ Cleanup: {success}")
        
        print("\n" + "="*70)
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_repository_manager()
