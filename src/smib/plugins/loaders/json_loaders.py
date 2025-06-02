"""
JSON metadata loaders.

This module provides loaders for JSON metadata files.
"""

from pathlib import Path
from typing import Dict, Optional

from smib.plugins.plugin import PluginMetadata


class JsonMetadataLoader:
    """Loader for JSON metadata files."""
    
    def load_metadata(self, path: Path) -> PluginMetadata:
        """Load metadata from a JSON file."""
        # This is a placeholder for future implementation
        raise NotImplementedError("JSON metadata loading is not yet implemented")
    
    def save_metadata(self, path: Path, metadata: PluginMetadata) -> None:
        """Save metadata to a JSON file."""
        # This is a placeholder for future implementation
        raise NotImplementedError("JSON metadata saving is not yet implemented")
    
    def load_config(self, path: Path) -> Dict:
        """Load configuration from a JSON file."""
        # This is a placeholder for future implementation
        raise NotImplementedError("JSON configuration loading is not yet implemented")
    
    def save_config(self, path: Path, config: Dict) -> None:
        """Save configuration to a JSON file."""
        # This is a placeholder for future implementation
        raise NotImplementedError("JSON configuration saving is not yet implemented")