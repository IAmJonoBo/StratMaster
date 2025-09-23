"""Load expert doctrines from configuration files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_doctrines(base_dir: Path | None = None) -> dict[str, Any]:
    """Load all expert doctrines from config files.
    
    Args:
        base_dir: Base directory containing doctrines. If None, uses project default.
        
    Returns:
        Dictionary mapping discipline names to their doctrine configurations.
    """
    if base_dir is None:
        # Go up to project root and find configs
        current = Path(__file__).resolve()
        project_root = current
        for _ in range(10):  # Safety limit
            if (project_root / "configs").exists():
                break
            project_root = project_root.parent
        base_dir = project_root / "configs" / "experts" / "doctrines"
    
    doctrines = {}
    
    if not base_dir.exists():
        logger.warning(f"Doctrines directory not found: {base_dir}")
        return doctrines
    
    # Load all YAML files in doctrines directory
    for file_path in base_dir.rglob("*.yaml"):
        try:
            with file_path.open("r", encoding="utf-8") as f:
                doctrine_data = yaml.safe_load(f)
            
            # Use the discipline name from the filename or the data
            discipline = file_path.stem
            if "discipline" in doctrine_data:
                discipline = doctrine_data["discipline"]
            
            doctrines[discipline] = doctrine_data
            logger.debug(f"Loaded doctrine for {discipline} from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load doctrine from {file_path}: {e}")
    
    logger.info(f"Loaded {len(doctrines)} expert doctrines")
    return doctrines


__all__ = ["load_doctrines"]