import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple
from src.config.settings import settings
from src.utils.logging import logger

def get_directory_size_mb(path: Path) -> float:
    """Calculates total size in Megabytes of a directory tree."""
    if not path.exists():
        return 0.0
    total_bytes = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file() and not entry.is_symlink():
                try:
                    total_bytes += entry.stat().st_size
                except (OSError, FileNotFoundError):
                    pass
    except Exception as e:
        logger.warning(f"Error reading directory {path}: {e}")
    return total_bytes / (1024 * 1024)

def get_storage_breakdown() -> Dict[str, Any]:
    """Inspects the local project footprint breakdown."""
    base_dir = settings.BASE_DIR
    total_mb = get_directory_size_mb(base_dir)
    temp_mb = get_directory_size_mb(settings.TEMP_DIR)
    cache_mb = get_directory_size_mb(settings.CACHE_DIR)
    data_mb = get_directory_size_mb(settings.DATA_DIR)

    # Check top largest files
    largest_files: List[Tuple[str, float]] = []
    try:
        for file in base_dir.rglob("*"):
            if file.is_file() and not file.is_symlink():
                try:
                    size_mb = file.stat().st_size / (1024 * 1024)
                    rel_path = str(file.relative_to(base_dir))
                    largest_files.append((rel_path, size_mb))
                except (OSError, FileNotFoundError):
                    pass
        largest_files.sort(key=lambda x: x[1], reverse=True)
    except Exception:
        pass

    # System free disk space
    try:
        usage = shutil.disk_usage(base_dir)
        system_free_gb = usage.free / (1024 ** 3)
    except Exception:
        system_free_gb = -1.0

    return {
        "project_total_mb": round(total_mb, 2),
        "data_dir_mb": round(data_mb, 2),
        "temp_storage_mb": round(temp_mb, 2),
        "cache_storage_mb": round(cache_mb, 2),
        "system_free_gb": round(system_free_gb, 2),
        "largest_files": largest_files[:5]
    }

def clean_temp_directory() -> int:
    """Removes all files from the temporary directory."""
    cleaned_count = 0
    if settings.TEMP_DIR.exists():
        for item in settings.TEMP_DIR.iterdir():
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()
                    cleaned_count += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    cleaned_count += 1
            except Exception as e:
                logger.warning(f"Failed to remove temp file {item}: {e}")
    return cleaned_count

def enforce_storage_limits() -> bool:
    """
    Guarantees project footprint stays strictly below the configured hard ceiling.
    Returns True if within safe threshold, False if an emergency purge was triggered.
    """
    breakdown = get_storage_breakdown()
    current_mb = breakdown["project_total_mb"]
    
    if current_mb > settings.MAX_PROJECT_FOOTPRINT_MB:
        logger.error(
            f"STORAGE CEILING EXCEEDED! Project size is {current_mb:.1f} MB "
            f"(Hard limit: {settings.MAX_PROJECT_FOOTPRINT_MB} MB). Triggering emergency purge..."
        )
        clean_temp_directory()
        # Re-check after purge
        updated = get_storage_breakdown()["project_total_mb"]
        logger.info(f"Post-purge project size: {updated:.1f} MB")
        return False
        
    if breakdown["temp_storage_mb"] > settings.MAX_TEMP_STORAGE_MB:
        logger.info(f"Temp storage exceeded threshold ({breakdown['temp_storage_mb']:.1f} MB). Cleaning temp files.")
        clean_temp_directory()
        
    return True
