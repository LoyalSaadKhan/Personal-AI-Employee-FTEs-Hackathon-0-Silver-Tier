#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Watcher - Abstract base class for all AI Employee watchers.

Watchers are lightweight Python scripts that run continuously in the background,
monitoring various inputs (Gmail, WhatsApp, filesystems, etc.) and creating
actionable .md files in the /Needs_Action folder for Claude Code to process.

All watchers follow this pattern:
1. Poll for new items at regular intervals
2. Create a .md file in /Needs_Action for each new item
3. Track processed items to avoid duplicates
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime


class BaseWatcher(ABC):
    """
    Abstract base class for all watcher implementations.
    
    Subclasses must implement:
    - check_for_updates(): Return list of new items to process
    - create_action_file(item): Create .md file in Needs_Action folder
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        
        # Ensure Needs_Action folder exists
        self.needs_action.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        # Handler for console output
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Track processed items to avoid duplicates
        self.processed_ids = set()
        
        self.logger.info(f'Initialized {self.__class__.__name__}')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {check_interval}s')
    
    @abstractmethod
    def check_for_updates(self) -> list:
        """
        Check for new items that need processing.
        
        Returns:
            list: List of new items (format depends on watcher type)
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item) -> Path:
        """
        Create a .md action file in the Needs_Action folder.
        
        Args:
            item: Item to create action file for
            
        Returns:
            Path: Path to the created file
        """
        pass
    
    def run(self):
        """
        Main run loop. Continuously checks for updates and creates action files.
        
        This method runs indefinitely until interrupted (Ctrl+C).
        """
        self.logger.info(f'Starting {self.__class__.__name__} main loop...')
        self.logger.info('Press Ctrl+C to stop')
        
        try:
            while True:
                try:
                    # Check for new items
                    items = self.check_for_updates()
                    
                    if items:
                        self.logger.info(f'Found {len(items)} new item(s)')
                        for item in items:
                            try:
                                filepath = self.create_action_file(item)
                                self.logger.info(f'Created action file: {filepath.name}')
                            except Exception as e:
                                self.logger.error(f'Error creating action file: {e}')
                    else:
                        self.logger.debug('No new items')
                    
                except Exception as e:
                    self.logger.error(f'Error in check cycle: {e}')
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info(f'{self.__class__.__name__} stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}')
            raise
        finally:
            self.logger.info(f'{self.__class__.__name__} shutting down')
    
    def get_timestamp(self) -> str:
        """Get current ISO format timestamp."""
        return datetime.now().isoformat()
    
    def sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string for use as a filename.
        
        Args:
            name: Original name
            
        Returns:
            str: Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|？*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()


# Example usage and testing
if __name__ == '__main__':
    # This is an abstract class - create a concrete implementation to test
    print("BaseWatcher is an abstract base class.")
    print("Subclass it and implement check_for_updates() and create_action_file()")
