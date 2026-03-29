#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File System Watcher - Monitors a drop folder for new files.

This is the simplest watcher implementation, perfect for the Bronze tier.
Users can drag-and-drop files into the watch folder, and the watcher
creates corresponding action files in /Needs_Action for Claude Code to process.

Usage:
    python filesystem_watcher.py /path/to/vault /path/to/watch/folder

Example:
    python filesystem_watcher.py ./AI_Employee_Vault ./AI_Employee_Vault/Inbox
"""

import os
import sys
import hashlib
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher


class FilesystemWatcher(BaseWatcher):
    """
    Watches a folder for new files and creates action files in Needs_Action.
    
    When a new file is detected:
    1. Copy the file to Needs_Action folder
    2. Create a metadata .md file with file info
    3. Track file hash to avoid processing duplicates
    """
    
    def __init__(self, vault_path: str, watch_folder: str = None, check_interval: int = 30):
        """
        Initialize the filesystem watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            watch_folder: Folder to monitor (default: vault_path/Inbox)
            check_interval: Seconds between checks (default: 30)
        """
        super().__init__(vault_path, check_interval)
        
        # Set watch folder
        if watch_folder:
            self.watch_folder = Path(watch_folder)
        else:
            self.watch_folder = self.vault_path / 'Inbox'
        
        # Ensure watch folder exists
        self.watch_folder.mkdir(parents=True, exist_ok=True)
        
        # Load previously processed files
        self.processed_hashes = self._load_processed_hashes()
        
        self.logger.info(f'Watch folder: {self.watch_folder}')
    
    def _load_processed_hashes(self) -> set:
        """Load hashes of previously processed files."""
        hash_file = self.vault_path / '.processed_files.txt'
        if hash_file.exists():
            try:
                content = hash_file.read_text()
                return set(content.strip().split('\n'))
            except Exception as e:
                self.logger.warning(f'Could not load processed files: {e}')
        return set()
    
    def _save_processed_hashes(self):
        """Save hashes of processed files to disk."""
        hash_file = self.vault_path / '.processed_files.txt'
        try:
            hash_file.write_text('\n'.join(self.processed_hashes))
        except Exception as e:
            self.logger.error(f'Could not save processed files: {e}')
    
    def _get_file_hash(self, filepath: Path) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def check_for_updates(self) -> list:
        """
        Check watch folder for new files.
        
        Returns:
            list: List of new file paths
        """
        new_files = []
        
        try:
            for filepath in self.watch_folder.iterdir():
                if filepath.is_file() and not filepath.name.startswith('.'):
                    # Calculate hash
                    file_hash = self._get_file_hash(filepath)
                    
                    # Check if already processed
                    if file_hash not in self.processed_hashes:
                        new_files.append({
                            'path': filepath,
                            'hash': file_hash
                        })
                        self.logger.debug(f'New file detected: {filepath.name}')
        
        except Exception as e:
            self.logger.error(f'Error scanning watch folder: {e}')
        
        return new_files
    
    def create_action_file(self, item: dict) -> Path:
        """
        Create an action file for the new file.
        
        Args:
            item: Dict with 'path' and 'hash' keys
            
        Returns:
            Path: Path to the created metadata file
        """
        source_path = item['path']
        file_hash = item['hash']
        
        # Get file info
        stat = source_path.stat()
        file_size = stat.st_size
        modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        # Create safe filename
        safe_name = self.sanitize_filename(source_path.stem)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Copy file to Needs_Action
        dest_path = self.needs_action / f'FILE_{safe_name}_{timestamp}{source_path.suffix}'
        shutil.copy2(source_path, dest_path)
        
        # Create metadata file
        meta_path = self.needs_action / f'FILE_{safe_name}_{timestamp}.md'
        content = f'''---
type: file_drop
original_name: {source_path.name}
size: {file_size}
received: {self.get_timestamp()}
modified: {modified_time}
status: pending
priority: normal
---

# File Dropped for Processing

**Original File:** `{source_path.name}`

**File Size:** {file_size:,} bytes

**Received:** {self.get_timestamp()}

---

## Suggested Actions

- [ ] Review file content
- [ ] Process or take action based on content
- [ ] Move to /Done when complete

---

## Notes

<!-- Add your notes here -->

'''
        meta_path.write_text(content)
        
        # Mark as processed
        self.processed_hashes.add(file_hash)
        self._save_processed_hashes()
        
        # Remove original from watch folder (optional - keeps inbox clean)
        try:
            source_path.unlink()
            self.logger.debug(f'Removed original file from watch folder: {source_path.name}')
        except Exception as e:
            self.logger.warning(f'Could not remove original file: {e}')
        
        return meta_path


def main():
    """Main entry point for running the watcher."""
    if len(sys.argv) < 2:
        print("Usage: python filesystem_watcher.py <vault_path> [watch_folder]")
        print("\nExample:")
        print("  python filesystem_watcher.py ./AI_Employee_Vault")
        print("  python filesystem_watcher.py ./AI_Employee_Vault ./AI_Employee_Vault/Inbox")
        sys.exit(1)
    
    vault_path = Path(sys.argv[1]).resolve()
    watch_folder = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
    
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)
    
    # Create and run watcher
    watcher = FilesystemWatcher(str(vault_path), str(watch_folder) if watch_folder else None)
    watcher.run()


if __name__ == '__main__':
    main()
