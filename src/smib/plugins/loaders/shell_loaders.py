"""
Shell script plugin loaders.

This module provides loaders for shell script plugins.
"""

from pathlib import Path
from typing import List, Optional

from smib.plugins.plugin import Plugin, ShellScriptPlugin


class ShellScriptPluginLoader:
    """Loader for shell script plugins."""
    
    def load_from_path(self, path: Path, name: Optional[str] = None) -> Plugin:
        """Load a plugin from a shell script file."""
        # This is a placeholder for future implementation
        raise NotImplementedError("Shell script plugin loading is not yet implemented")
    
    def load_all_from_directory(self, directory: Path) -> List[Plugin]:
        """Load all shell script files from a directory as plugins."""
        # This is a placeholder for future implementation
        return []
    
    def can_load(self, path: Path) -> bool:
        """Check if this loader can load the plugin at the given path."""
        # This is a placeholder for future implementation
        return False