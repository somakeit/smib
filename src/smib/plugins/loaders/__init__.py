"""
Plugin loader interfaces and implementations.

This package provides various plugin loader implementations for different types of plugins.
"""

# Import the main plugin loader protocol and implementations
from .plugin_loaders import PluginLoader, PythonModulePluginLoader, PythonPackagePluginLoader

# Import the backward compatibility module loaders
from .module_loaders import ModulePluginLoader, PackagePluginLoader

# Import the JSON and shell script loaders
from .json_loaders import JsonMetadataLoader
from .shell_loaders import ShellScriptPluginLoader

# Import the composite loader and convenience function
from .composite_loader import CompositePluginLoader, create_default_plugin_loader

# For backward compatibility
from .module_loaders import PluginLoader as ModulePluginLoaderProtocol
from .plugin_loaders import PluginLoader as PluginLoaderProtocol

# Re-export the create_default_plugin_loader function for convenience
__all__ = [
    # Main plugin loader protocol
    'PluginLoader',

    # Python plugin loaders
    'PythonModulePluginLoader',
    'PythonPackagePluginLoader',

    # Backward compatibility module loaders
    'ModulePluginLoader',
    'PackagePluginLoader',

    # JSON and shell script loaders
    'JsonMetadataLoader',
    'ShellScriptPluginLoader',

    # Composite loader and convenience function
    'CompositePluginLoader',
    'create_default_plugin_loader',

    # Backward compatibility protocols
    'ModulePluginLoaderProtocol',
    'PluginLoaderProtocol',
]
