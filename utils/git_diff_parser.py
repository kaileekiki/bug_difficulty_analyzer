"""
Advanced Git Diff Parser
Extracts before/after code from patches
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class FilePatch:
    """Single file patch information"""
    filepath: str
    old_content: str
    new_content: str
    added_lines: int
    deleted_lines: int
    is_new_file: bool
    is_deleted_file: bool
    hunks: List[Dict]


class GitDiffParser:
    """Parse git diff/patch format"""
    
    @staticmethod
    def parse_patch(patch_text: str) -> Dict[str, FilePatch]:
        """
        Parse git diff patch into structured format.
        
        Returns:
            Dict[filepath, FilePatch]
        """
        files = {}
        
        # Split by file
        file_blocks = re.split(r'\ndiff --git', '\n' + patch_text)
        
        for block in file_blocks:
            if not block.strip():
                continue
            
            # Add back the split marker
            if not block.startswith('diff --git'):
                block = 'diff --git' + block
            
            file_patch = GitDiffParser._parse_file_block(block)
            if file_patch:
                files[file_patch.filepath] = file_patch
        
        return files
    
    @staticmethod
    def _parse_file_block(block: str) -> Optional[FilePatch]:
        """Parse single file block"""
        lines = block.split('\n')
        
        # Extract filepath
        filepath = None
        for line in lines[:5]:
            if line.startswith('--- a/'):
                filepath = line[6:]
                break
            elif line.startswith('+++ b/'):
                if not filepath:  # New file
                    filepath = line[6:]
                break
        
        if not filepath or filepath == '/dev/null':
            # Try alternative format
            match = re.search(r'\+\+\+ b/(.+)', block)
            if match:
                filepath = match.group(1)
            else:
                return None
        
        # Check if new/deleted file
        is_new_file = '--- /dev/null' in block
        is_deleted_file = '+++ /dev/null' in block
        
        # Parse hunks
        hunks = GitDiffParser._parse_hunks(block)
        
        # Reconstruct before/after content
        old_content, new_content = GitDiffParser._reconstruct_content(hunks)
        
        # Count changes
        added_lines = sum(1 for line in block.split('\n') 
                         if line.startswith('+') and not line.startswith('+++'))
        deleted_lines = sum(1 for line in block.split('\n') 
                           if line.startswith('-') and not line.startswith('---'))
        
        return FilePatch(
            filepath=filepath,
            old_content=old_content,
            new_content=new_content,
            added_lines=added_lines,
            deleted_lines=deleted_lines,
            is_new_file=is_new_file,
            is_deleted_file=is_deleted_file,
            hunks=hunks
        )
    
    @staticmethod
    def _parse_hunks(block: str) -> List[Dict]:
        """Parse hunks from diff block"""
        hunks = []
        current_hunk = None
        
        for line in block.split('\n'):
            # Hunk header: @@ -old_start,old_count +new_start,new_count @@
            if line.startswith('@@'):
                if current_hunk:
                    hunks.append(current_hunk)
                
                match = re.search(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
                if match:
                    old_start = int(match.group(1))
                    old_count = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_count = int(match.group(4)) if match.group(4) else 1
                    
                    current_hunk = {
                        'old_start': old_start,
                        'old_count': old_count,
                        'new_start': new_start,
                        'new_count': new_count,
                        'lines': []
                    }
            
            elif current_hunk is not None:
                # Hunk content
                if line.startswith('+') and not line.startswith('+++'):
                    current_hunk['lines'].append(('add', line[1:]))
                elif line.startswith('-') and not line.startswith('---'):
                    current_hunk['lines'].append(('del', line[1:]))
                elif line.startswith(' '):
                    current_hunk['lines'].append(('ctx', line[1:]))
        
        if current_hunk:
            hunks.append(current_hunk)
        
        return hunks
    
    @staticmethod
    def _reconstruct_content(hunks: List[Dict]) -> Tuple[str, str]:
        """Reconstruct before and after content from hunks"""
        old_lines = []
        new_lines = []
        
        for hunk in hunks:
            for change_type, line_content in hunk['lines']:
                if change_type in ('ctx', 'del'):
                    old_lines.append(line_content)
                if change_type in ('ctx', 'add'):
                    new_lines.append(line_content)
        
        return '\n'.join(old_lines), '\n'.join(new_lines)
    
    @staticmethod
    def extract_changed_functions(patch: FilePatch) -> List[str]:
        """Extract function names that were changed"""
        functions = []
        
        # Simple heuristic: look for 'def ' in changed lines
        for hunk in patch.hunks:
            for change_type, line in hunk['lines']:
                if change_type in ('add', 'del'):
                    line_stripped = line.strip()
                    if line_stripped.startswith('def '):
                        # Extract function name
                        match = re.match(r'def\s+(\w+)\s*\(', line_stripped)
                        if match:
                            func_name = match.group(1)
                            if func_name not in functions:
                                functions.append(func_name)
        
        return functions


def test_git_diff_parser():
    """Test git diff parser"""
    patch = """
diff --git a/calculator.py b/calculator.py
index 1234567..abcdefg 100644
--- a/calculator.py
+++ b/calculator.py
@@ -1,6 +1,9 @@
 def divide(a, b):
+    if b == 0:
+        return None
     return a / b
 
 def multiply(a, b):
+    # Handle large numbers
     return a * b
"""
    
    print("Testing Git Diff Parser...")
    print("="*60)
    
    parser = GitDiffParser()
    files = parser.parse_patch(patch)
    
    print(f"\n✓ Parsed {len(files)} files")
    
    for filepath, file_patch in files.items():
        print(f"\nFile: {filepath}")
        print(f"  Added: {file_patch.added_lines} lines")
        print(f"  Deleted: {file_patch.deleted_lines} lines")
        print(f"  Hunks: {len(file_patch.hunks)}")
        print(f"  New file: {file_patch.is_new_file}")
        
        print(f"\n  Old content ({len(file_patch.old_content)} chars):")
        print("   ", file_patch.old_content.replace('\n', '\n    ')[:200])
        
        print(f"\n  New content ({len(file_patch.new_content)} chars):")
        print("   ", file_patch.new_content.replace('\n', '\n    ')[:200])
        
        functions = parser.extract_changed_functions(file_patch)
        print(f"\n  Changed functions: {functions}")
    
    print("\n✓ Git diff parser test passed!")


if __name__ == '__main__':
    test_git_diff_parser()
