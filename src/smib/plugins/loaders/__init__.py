"""
Plugin loader interfaces and implementations.

This package provides various plugin loader implementations for different types of plugins.
"""

# Import the main plugin loader protocol and implementations
from .plugin_loaders import PluginLoader, PythonModulePluginLoader, PythonPackagePluginLoader

# Import the composite loader and convenience function
from .composite_loader import CompositePluginLoader, create_default_plugin_loader
from .plugin_loaders import PluginLoader as PluginLoaderProtocol

# Re-export the create_default_plugin_loader function for convenience
__all__ = [
    # Main plugin loader protocol
    'PluginLoader',
    # Python plugin loaders
    'PythonModulePluginLoader',
    'PythonPackagePluginLoader',
    # Composite loader and convenience function
    'CompositePluginLoader',
    'create_default_plugin_loader',
    'PluginLoaderProtocol',
]
