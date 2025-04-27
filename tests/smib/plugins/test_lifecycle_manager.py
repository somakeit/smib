import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import sys
import logging

from slack_bolt.app.async_app import AsyncApp
from smib.plugins.lifecycle_manager import PluginLifecycleManager
from smib.utilities.dynamic_caller import dynamic_caller


@pytest.fixture
def mock_bolt_app():
    """Fixture for a mocked AsyncApp."""
    return MagicMock(spec=AsyncApp)


@pytest.fixture
def lifecycle_manager(mock_bolt_app):
    """Fixture for a PluginLifecycleManager instance."""
    return PluginLifecycleManager(mock_bolt_app)


class TestPluginLifecycleManager:
    """Tests for the PluginLifecycleManager class."""

    def test_init(self, lifecycle_manager, mock_bolt_app):
        """Test initialization of PluginLifecycleManager."""
        assert lifecycle_manager.bolt_app == mock_bolt_app
        assert isinstance(lifecycle_manager.logger, logging.Logger)
        assert isinstance(lifecycle_manager.plugins_directory, Path)
        assert lifecycle_manager.plugins == []
        assert lifecycle_manager.plugin_map == []
        assert lifecycle_manager.plugin_unregister_callbacks == []
        assert lifecycle_manager.plugin_preregister_callbacks == []
        assert lifecycle_manager.plugin_postregister_callbacks == []
        assert lifecycle_manager.registration_parameters == {}

    @patch('smib.plugins.lifecycle_manager.import_all_from_directory')
    def test_load_plugins_directory_not_exists(self, mock_import_all, lifecycle_manager):
        """Test load_plugins when the plugins directory doesn't exist."""
        # Setup
        lifecycle_manager.plugins_directory = MagicMock(spec=Path)
        lifecycle_manager.plugins_directory.exists.return_value = False

        # Execute
        lifecycle_manager.load_plugins()

        # Verify
        lifecycle_manager.plugins_directory.exists.assert_called_once()
        mock_import_all.assert_not_called()

    @patch('smib.plugins.lifecycle_manager.import_all_from_directory')
    def test_load_plugins_directory_not_a_directory(self, mock_import_all, lifecycle_manager):
        """Test load_plugins when the plugins directory is not a directory."""
        # Setup
        lifecycle_manager.plugins_directory = MagicMock(spec=Path)
        lifecycle_manager.plugins_directory.exists.return_value = True
        lifecycle_manager.plugins_directory.is_dir.return_value = False

        # Execute
        lifecycle_manager.load_plugins()

        # Verify
        lifecycle_manager.plugins_directory.exists.assert_called_once()
        lifecycle_manager.plugins_directory.is_dir.assert_called_once()
        mock_import_all.assert_not_called()

    @patch('smib.plugins.lifecycle_manager.import_all_from_directory')
    @patch('smib.plugins.lifecycle_manager.sys.path')
    def test_load_plugins_success(self, mock_sys_path, mock_import_all, lifecycle_manager):
        """Test load_plugins when successful."""
        # Setup
        lifecycle_manager.plugins_directory = MagicMock(spec=Path)
        lifecycle_manager.plugins_directory.exists.return_value = True
        lifecycle_manager.plugins_directory.is_dir.return_value = True
        lifecycle_manager.plugins_directory.parent.resolve.return_value = '/path/to/parent'

        mock_module1 = MagicMock()
        mock_module2 = MagicMock()
        mock_import_all.return_value = [mock_module1, mock_module2]

        # Mock validate_plugin_modules and register_plugins
        with patch.object(lifecycle_manager, 'validate_plugin_modules') as mock_validate, \
             patch.object(lifecycle_manager, 'register_plugins') as mock_register:

            mock_validate.return_value = [mock_module1]  # Only one module is valid

            # Execute
            lifecycle_manager.load_plugins()

            # Verify
            lifecycle_manager.plugins_directory.exists.assert_called_once()
            lifecycle_manager.plugins_directory.is_dir.assert_called_once()
            mock_sys_path.insert.assert_called_once_with(0, str('/path/to/parent'))
            mock_import_all.assert_called_once_with(lifecycle_manager.plugins_directory)
            mock_validate.assert_called_once_with([mock_module1, mock_module2])
            mock_register.assert_called_once_with([mock_module1])

    def test_register_plugins(self, lifecycle_manager):
        """Test register_plugins method."""
        # Setup
        mock_module1 = MagicMock()
        mock_module1.__name__ = "module1"
        mock_module1.__file__ = "/path/to/module1.py"

        mock_module2 = MagicMock()
        mock_module2.__name__ = "module2"
        mock_module2.__file__ = "/path/to/module2.py"

        # Mock methods
        with patch.object(lifecycle_manager, 'preregister_plugin') as mock_preregister, \
             patch.object(lifecycle_manager, 'register_plugin') as mock_register, \
             patch.object(lifecycle_manager, 'postregister_plugin') as mock_postregister, \
             patch.object(lifecycle_manager, 'unregister_plugin') as mock_unregister, \
             patch.object(lifecycle_manager, 'get_relative_path') as mock_get_path:

            mock_get_path.return_value = "relative/path"

            # Make the second module raise an exception during registration
            mock_register.side_effect = [None, Exception("Registration error")]

            # Execute
            lifecycle_manager.register_plugins([mock_module1, mock_module2])

            # Verify
            assert mock_preregister.call_count == 2
            assert mock_register.call_count == 2
            assert mock_postregister.call_count == 1  # Only called for the first module
            assert mock_unregister.call_count == 1  # Called for the second module
            mock_unregister.assert_called_once_with(mock_module2)

    @patch('smib.plugins.lifecycle_manager.dynamic_caller')
    def test_register_plugin(self, mock_dynamic_caller, lifecycle_manager):
        """Test register_plugin method."""
        # Setup
        mock_module = MagicMock()
        mock_module.__name__ = "test_module"
        mock_module.__file__ = "/path/to/module.py"

        # Mock _add_to_map
        with patch.object(lifecycle_manager, '_add_to_map') as mock_add_to_map:

            # Execute
            lifecycle_manager.register_plugin(mock_module)

            # Verify
            mock_dynamic_caller.assert_called_once_with(mock_module.register, **{})
            assert mock_module in lifecycle_manager.plugins
            mock_add_to_map.assert_called_once_with(mock_module)

    @patch('smib.plugins.lifecycle_manager.dynamic_caller')
    def test_register_plugin_with_parameters(self, mock_dynamic_caller, lifecycle_manager):
        """Test register_plugin method with registration parameters."""
        # Setup
        mock_module = MagicMock()
        mock_module.__name__ = "test_module"
        mock_module.__file__ = "/path/to/module.py"

        lifecycle_manager.registration_parameters = {"param1": "value1", "param2": "value2"}

        # Mock _add_to_map
        with patch.object(lifecycle_manager, '_add_to_map') as mock_add_to_map:

            # Execute
            lifecycle_manager.register_plugin(mock_module)

            # Verify
            mock_dynamic_caller.assert_called_once_with(
                mock_module.register, 
                **{"param1": "value1", "param2": "value2"}
            )
            assert mock_module in lifecycle_manager.plugins
            mock_add_to_map.assert_called_once_with(mock_module)

    @patch('smib.plugins.lifecycle_manager.dynamic_caller')
    def test_register_plugin_exception(self, mock_dynamic_caller, lifecycle_manager):
        """Test register_plugin method when an exception is raised."""
        # Setup
        mock_module = MagicMock()
        mock_module.__name__ = "test_module"
        mock_module.__file__ = "/path/to/module.py"

        mock_dynamic_caller.side_effect = Exception("Registration error")

        # Mock _add_to_map
        with patch.object(lifecycle_manager, '_add_to_map') as mock_add_to_map:

            # Execute and verify exception is raised
            with pytest.raises(Exception, match="Registration error"):
                lifecycle_manager.register_plugin(mock_module)

            # Verify module is still added to plugins and map
            assert mock_module in lifecycle_manager.plugins
            mock_add_to_map.assert_called_once_with(mock_module)

    @patch('smib.plugins.lifecycle_manager.get_actual_module_name')
    def test_get_map_key(self, mock_get_actual_module_name, lifecycle_manager):
        """Test _get_map_key method."""
        # Setup
        mock_module = MagicMock()
        mock_module.__name__ = "test_module"
        mock_module.__file__ = "/path/to/module.py"

        mock_get_actual_module_name.return_value = "actual_module_name"

        # Execute
        result = lifecycle_manager._get_map_key(mock_module)

        # Verify
        assert result == {
            'name': "actual_module_name",
            'unique_name': "test_module",
            'path': Path("/path/to/module.py"),
            'module': mock_module,
        }
        mock_get_actual_module_name.assert_called_once_with(mock_module)

    def test_add_to_map(self, lifecycle_manager):
        """Test _add_to_map method."""
        # Setup
        mock_module = MagicMock()
        mock_map_key = {"key": "value"}

        # Mock _get_map_key
        with patch.object(lifecycle_manager, '_get_map_key') as mock_get_map_key:
            mock_get_map_key.return_value = mock_map_key

            # Execute
            lifecycle_manager._add_to_map(mock_module)

            # Verify
            assert mock_map_key in lifecycle_manager.plugin_map
            mock_get_map_key.assert_called_once_with(mock_module)

    def test_remove_from_map(self, lifecycle_manager):
        """Test _remove_from_map method."""
        # Setup
        mock_module = MagicMock()
        mock_map_key = {"key": "value"}
        lifecycle_manager.plugin_map = [mock_map_key]

        # Mock _get_map_key
        with patch.object(lifecycle_manager, '_get_map_key') as mock_get_map_key:
            mock_get_map_key.return_value = mock_map_key

            # Execute
            lifecycle_manager._remove_from_map(mock_module)

            # Verify
            assert mock_map_key not in lifecycle_manager.plugin_map
            mock_get_map_key.assert_called_once_with(mock_module)

    def test_unregister_plugin(self, lifecycle_manager):
        """Test unregister_plugin method."""
        # Setup
        mock_module = MagicMock()
        lifecycle_manager.plugins = [mock_module]

        mock_callback1 = MagicMock()
        mock_callback2 = MagicMock()
        lifecycle_manager.plugin_unregister_callbacks = [mock_callback1, mock_callback2]

        # Mock _remove_from_map
        with patch.object(lifecycle_manager, '_remove_from_map') as mock_remove_from_map:

            # Execute
            lifecycle_manager.unregister_plugin(mock_module)

            # Verify
            mock_callback1.assert_called_once_with(mock_module)
            mock_callback2.assert_called_once_with(mock_module)
            assert mock_module not in lifecycle_manager.plugins
            mock_remove_from_map.assert_called_once_with(mock_module)

    def test_preregister_plugin(self, lifecycle_manager):
        """Test preregister_plugin method."""
        # Setup
        mock_module = MagicMock()

        mock_callback1 = MagicMock()
        mock_callback2 = MagicMock()
        lifecycle_manager.plugin_preregister_callbacks = [mock_callback1, mock_callback2]

        # Execute
        lifecycle_manager.preregister_plugin(mock_module)

        # Verify
        mock_callback1.assert_called_once_with(mock_module)
        mock_callback2.assert_called_once_with(mock_module)

    def test_postregister_plugin(self, lifecycle_manager):
        """Test postregister_plugin method."""
        # Setup
        mock_module = MagicMock()

        mock_callback1 = MagicMock()
        mock_callback2 = MagicMock()
        lifecycle_manager.plugin_postregister_callbacks = [mock_callback1, mock_callback2]

        # Execute
        lifecycle_manager.postregister_plugin(mock_module)

        # Verify
        mock_callback1.assert_called_once_with(mock_module)
        mock_callback2.assert_called_once_with(mock_module)

    def test_validate_plugin_modules(self, lifecycle_manager):
        """Test validate_plugin_modules method."""
        # Setup
        mock_module1 = MagicMock()
        mock_module1.__name__ = "module1"
        mock_module1.__file__ = "/path/to/module1.py"

        mock_module2 = MagicMock()
        mock_module2.__name__ = "module2"
        mock_module2.__file__ = "/path/to/module2.py"

        # Add modules to sys.modules
        sys.modules["module1"] = mock_module1
        sys.modules["module2"] = mock_module2

        try:
            # Mock validate_plugin_module
            with patch.object(lifecycle_manager, 'validate_plugin_module') as mock_validate, \
                 patch.object(lifecycle_manager, 'get_relative_path') as mock_get_path:

                mock_validate.side_effect = [True, False]  # First module valid, second invalid
                mock_get_path.return_value = "relative/path"

                # Execute
                result = lifecycle_manager.validate_plugin_modules([mock_module1, mock_module2])

                # Verify
                assert result == [mock_module1]
                assert mock_validate.call_count == 2
                assert "module2" not in sys.modules
        finally:
            # Clean up
            if "module1" in sys.modules:
                del sys.modules["module1"]
            if "module2" in sys.modules:
                del sys.modules["module2"]

    @patch('smib.plugins.lifecycle_manager.get_actual_module_name')
    def test_validate_plugin_module_valid(self, mock_get_actual_module_name, lifecycle_manager):
        """Test validate_plugin_module method with a valid module."""
        # Setup
        mock_module = MagicMock()
        mock_module.__name__ = "test_module"
        mock_module.register = MagicMock()  # Has register callable
        mock_module.__display_name__ = "Display Name"  # Has required attributes
        mock_module.__description__ = "Description"
        mock_module.__author__ = "Author"  # Has recommended attributes

        mock_get_actual_module_name.return_value = "actual_module_name"

        # Execute
        result = lifecycle_manager.validate_plugin_module(mock_module)

        # Verify
        assert result is True

    @patch('smib.plugins.lifecycle_manager.get_actual_module_name')
    @patch('smib.plugins.lifecycle_manager.getattr')
    def test_validate_plugin_module_no_register(self, mock_getattr, mock_get_actual_module_name, lifecycle_manager):
        """Test validate_plugin_module method with a module missing register callable."""
        # Setup
        mock_module = MagicMock()
        mock_module.__name__ = "test_module"
        mock_module.__display_name__ = "Display Name"
        mock_module.__description__ = "Description"

        # Mock getattr to return None for 'register'
        def mock_getattr_side_effect(obj, name, default=None):
            if name == 'register':
                return None
            return getattr(obj, name, default)

        mock_getattr.side_effect = mock_getattr_side_effect

        mock_get_actual_module_name.return_value = "actual_module_name"

        # Execute
        result = lifecycle_manager.validate_plugin_module(mock_module)

        # Verify
        assert result is False
        mock_getattr.assert_any_call(mock_module, 'register', None)

    @patch('smib.plugins.lifecycle_manager.get_actual_module_name')
    def test_validate_plugin_module_missing_required_attributes(self, mock_get_actual_module_name, lifecycle_manager):
        """Test validate_plugin_module method with a module missing required attributes."""
        # Setup
        mock_module = MagicMock()
        mock_module.__name__ = "test_module"
        mock_module.register = MagicMock()  # Has register callable
        # Missing __display_name__ and __description__

        mock_get_actual_module_name.return_value = "actual_module_name"

        # Execute
        result = lifecycle_manager.validate_plugin_module(mock_module)

        # Verify
        assert result is False

    @patch('smib.plugins.lifecycle_manager.get_actual_module_name')
    def test_validate_plugin_module_missing_recommended_attributes(self, mock_get_actual_module_name, lifecycle_manager):
        """Test validate_plugin_module method with a module missing recommended attributes."""
        # Setup
        mock_module = MagicMock()
        mock_module.__name__ = "test_module"
        mock_module.register = MagicMock()  # Has register callable
        mock_module.__display_name__ = "Display Name"  # Has required attributes
        mock_module.__description__ = "Description"
        # Missing __author__

        mock_get_actual_module_name.return_value = "actual_module_name"

        # Execute
        result = lifecycle_manager.validate_plugin_module(mock_module)

        # Verify
        assert result is True  # Still valid even without recommended attributes

    @patch('smib.plugins.lifecycle_manager.get_actual_module_name')
    def test_plugin_string(self, mock_get_actual_module_name, lifecycle_manager):
        """Test plugin_string property."""
        # Setup
        mock_module1 = MagicMock()
        mock_module2 = MagicMock()
        lifecycle_manager.plugins = [mock_module1, mock_module2]

        mock_get_actual_module_name.side_effect = ["module1", "module2"]

        # Execute
        result = lifecycle_manager.plugin_string

        # Verify
        assert result == "module1, module2"
        assert mock_get_actual_module_name.call_count == 2

    @patch('smib.plugins.lifecycle_manager.get_actual_module_name')
    def test_plugin_string_empty(self, mock_get_actual_module_name, lifecycle_manager):
        """Test plugin_string property when there are no plugins."""
        # Setup
        lifecycle_manager.plugins = []

        # Execute
        result = lifecycle_manager.plugin_string

        # Verify
        assert result == "None"
        mock_get_actual_module_name.assert_not_called()

    def test_register_plugin_unregister_callback(self, lifecycle_manager):
        """Test register_plugin_unregister_callback method."""
        # Setup
        mock_callback = MagicMock()

        # Execute
        lifecycle_manager.register_plugin_unregister_callback(mock_callback)

        # Verify
        assert mock_callback in lifecycle_manager.plugin_unregister_callbacks

    def test_register_plugin_preregister_callback(self, lifecycle_manager):
        """Test register_plugin_preregister_callback method."""
        # Setup
        mock_callback = MagicMock()

        # Execute
        lifecycle_manager.register_plugin_preregister_callback(mock_callback)

        # Verify
        assert mock_callback in lifecycle_manager.plugin_preregister_callbacks

    def test_register_plugin_postregister_callback(self, lifecycle_manager):
        """Test register_plugin_postregister_callback method."""
        # Setup
        mock_callback = MagicMock()

        # Execute
        lifecycle_manager.register_plugin_postregister_callback(mock_callback)

        # Verify
        assert mock_callback in lifecycle_manager.plugin_postregister_callbacks

    def test_register_parameter(self, lifecycle_manager):
        """Test register_parameter method."""
        # Setup
        parameter_name = "test_param"
        parameter_value = "test_value"

        # Execute
        lifecycle_manager.register_parameter(parameter_name, parameter_value)

        # Verify
        assert lifecycle_manager.registration_parameters[parameter_name] == parameter_value

    def test_get_relative_path(self, lifecycle_manager):
        """Test get_relative_path method."""
        # Setup
        lifecycle_manager.plugins_directory = Path("/path/to/plugins")
        plugin_path = "/path/to/plugins/test_plugin/module.py"

        # Mock Path.resolve and relative_to
        with patch('smib.plugins.lifecycle_manager.Path') as mock_path_class:
            mock_path_instance = MagicMock(spec=Path)
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.resolve.return_value = mock_path_instance
            mock_path_instance.relative_to.return_value = Path("test_plugin/module.py")

            # Execute
            result = lifecycle_manager.get_relative_path(plugin_path)

            # Verify
            assert result == Path("test_plugin/module.py")
            mock_path_instance.resolve.assert_called_once()
            mock_path_instance.relative_to.assert_called_once_with(lifecycle_manager.plugins_directory)
