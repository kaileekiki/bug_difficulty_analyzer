#!/usr/bin/env python3
"""
Dataset loader for benchmark datasets from Hugging Face.

Datasets are registered in benchmarks.json. To add a new benchmark,
add an entry there — no changes to this file are needed.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

# Registry file lives next to this script
_REGISTRY_PATH = Path(__file__).parent / "benchmarks.json"


def load_registry() -> Dict[str, Any]:
    """Load benchmark registry from benchmarks.json."""
    if not _REGISTRY_PATH.exists():
        raise FileNotFoundError(
            f"benchmarks.json not found at {_REGISTRY_PATH}\n"
            "This file defines available datasets."
        )
    with open(_REGISTRY_PATH, encoding="utf-8") as f:
        data = json.load(f)
    # Strip meta keys starting with '_'
    return {k: v for k, v in data.items() if not k.startswith("_")}


# Module-level registry — loaded once at import time
REGISTRY: Dict[str, Any] = load_registry()


class SWEBenchLoader:
    """
    Loader for benchmark datasets from Hugging Face.

    Available datasets are defined in benchmarks.json.
    Add a new entry there to support additional benchmarks
    without modifying any Python code.

    Features:
    - Auto-downloads dataset on first use
    - Caches dataset locally as JSON
    - Reuses cache on subsequent runs

    Usage:
        loader = SWEBenchLoader(dataset_type="verified")
        dataset = loader.load_dataset()

        loader = SWEBenchLoader(dataset_type="pro")
        dataset = loader.load_dataset()
    """

    def __init__(
        self,
        cache_dir: str = "datasets",
        dataset_dir: str = None,
        dataset_type: str = "verified",
    ):
        """
        Args:
            cache_dir:    Directory for cached JSON files (default: "datasets")
            dataset_dir:  Legacy alias for cache_dir (backward compatibility)
            dataset_type: Dataset alias as defined in benchmarks.json (default: "verified")
        """
        if dataset_dir is not None:
            cache_dir = dataset_dir

        if dataset_type not in REGISTRY:
            available = ", ".join(f"'{k}'" for k in REGISTRY)
            raise ValueError(
                f"Unknown dataset_type '{dataset_type}'. "
                f"Available: {available}\n"
                f"To add a new dataset, edit benchmarks.json."
            )

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.dataset_type = dataset_type

        info = REGISTRY[dataset_type]
        self.display_name     = info["name"]
        self.hf_dataset_name  = info["hf_dataset"]
        self.split            = info["hf_split"]
        self.cache_file       = self.cache_dir / info["cache_file"]

    def download_dataset(self, force: bool = False) -> Path:
        """Download dataset from Hugging Face and cache locally."""
        if self.cache_file.exists() and not force:
            print(f"Dataset already cached: {self.cache_file}")
            return self.cache_file

        print("=" * 70)
        print(f"Downloading {self.display_name} from Hugging Face...")
        print(f"   This may take 2-5 minutes on first run")
        print(f"   Cache location: {self.cache_file}")
        print("=" * 70)

        try:
            import sys as _sys, os as _os

            # Temporarily remove project dir from sys.path so the local
            # datasets/ folder doesn't shadow the HuggingFace 'datasets' package
            _proj_dir = _os.path.abspath(str(Path(__file__).parent))
            _orig_path = _sys.path[:]
            _sys.path = [p for p in _sys.path if p and _os.path.abspath(p) != _proj_dir]
            try:
                from datasets import load_dataset
            finally:
                _sys.path = _orig_path

            print(f"Fetching from {self.hf_dataset_name} (split={self.split})...")
            dataset = load_dataset(self.hf_dataset_name, split=self.split)
            print(f"Downloaded {len(dataset)} instances")

            print("Converting to JSON format...")
            data = [dict(item) for item in dataset]

            print(f"Saving to cache: {self.cache_file}")
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            file_size_mb = self.cache_file.stat().st_size / 1024 / 1024
            print(f"Saved ({file_size_mb:.2f} MB)")
            print("=" * 70)
            return self.cache_file

        except ImportError:
            print("ERROR: 'datasets' library not installed")
            print("   Install with: pip install datasets")
            raise
        except Exception as e:
            print(f"Download failed: {e}")
            print(f"   Manual download: https://huggingface.co/datasets/{self.hf_dataset_name}")
            raise

    def load_dataset(self) -> List[Dict[str, Any]]:
        """Load dataset from cache, auto-downloading if not yet cached."""
        if not self.cache_file.exists():
            print(f"{self.display_name} cache not found, downloading automatically...")
            self.download_dataset()

        print(f"Loading {self.display_name} from: {self.cache_file}")
        with open(self.cache_file, encoding="utf-8") as f:
            data = json.load(f)

        print(f"Loaded {len(data)} instances from {self.display_name}")
        return data

    def get_cache_path(self) -> Path:
        """Return path to the local cache file."""
        return self.cache_file

    def is_cached(self) -> bool:
        """Return True if the dataset has already been downloaded."""
        return self.cache_file.exists()

    def get_dataset_type(self) -> str:
        """Return the dataset alias (e.g. 'verified', 'full', 'pro')."""
        return self.dataset_type

    def create_mock_dataset(self, n: int = 10) -> List[Dict[str, Any]]:
        """Create a small mock dataset for local testing (no download needed)."""
        mock_instances = []
        for i in range(n):
            mock_instances.append({
                "instance_id": f"mock-{i+1:03d}",
                "repo": "https://github.com/octocat/Hello-World",
                "base_commit": "master",
                "patch": (
                    f"diff --git a/test_{i}.py b/test_{i}.py\n"
                    f"index 1234567..abcdefg 100644\n"
                    f"--- a/test_{i}.py\n"
                    f"+++ b/test_{i}.py\n"
                    f"@@ -1,3 +1,4 @@\n"
                    f"+# Modified line {i}\n"
                    f" def test_{i}():\n"
                    f"     pass\n"
                ),
                "problem_statement": f"Mock problem statement {i}",
            })
        return mock_instances
