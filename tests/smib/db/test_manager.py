import pytest
from unittest.mock import patch, MagicMock, AsyncMock, call
from beanie import Document

from smib.db.manager import (
    DatabaseManager,
    get_all_subclasses,
    filter_not_beanie,
)
from smib.config import MONGO_DB_NAME


### Test: Helper Functions ###
def test_get_all_subclasses():
    """Test get_all_subclasses returns all subclasses of a class."""
    # Create a class hierarchy for testing
    class Parent:
        pass

    class Child1(Parent):
        pass

    class Child2(Parent):
        pass

    class GrandChild(Child1):
        pass

    # Get all subclasses
    subclasses = get_all_subclasses(Parent)

    # Verify results
    assert len(subclasses) == 3
    assert Child1 in subclasses
    assert Child2 in subclasses
    assert GrandChild in subclasses


def test_filter_not_beanie():
    """Test filter_not_beanie correctly filters out beanie modules."""
    # Create mock Document classes
    class BeanieDocument(Document):
        pass
    BeanieDocument.__module__ = "beanie.document"

    class UserDocument(Document):
        pass
    UserDocument.__module__ = "smib.models"

    # Test the filter
    assert filter_not_beanie(BeanieDocument) is False
    assert filter_not_beanie(UserDocument) is True


### Test: DatabaseManager ###
def test_init():
    """Test DatabaseManager initialization."""
    # Test with default db_name
    with patch("smib.db.manager.AsyncIOMotorClient") as mock_client:
        manager = DatabaseManager()
        assert manager.db_name == MONGO_DB_NAME
        assert manager.client == mock_client.return_value
        assert len(manager._document_filters) == 1
        assert manager._document_filters[0] == filter_not_beanie

    # Test with custom db_name
    with patch("smib.db.manager.AsyncIOMotorClient") as mock_client:
        custom_db = "custom_db"
        manager = DatabaseManager(db_name=custom_db)
        assert manager.db_name == custom_db


@patch("smib.db.manager.get_all_subclasses")
def test_get_all_document_models(mock_get_all_subclasses):
    """Test get_all_document_models returns filtered document models."""
    # Create mock Document classes
    class BeanieDocument(Document):
        pass
    BeanieDocument.__module__ = "beanie.document"

    class UserDocument(Document):
        pass
    UserDocument.__module__ = "smib.models"

    # Setup mock return value
    mock_get_all_subclasses.return_value = {BeanieDocument, UserDocument}

    # Create manager and test
    manager = DatabaseManager()
    documents = manager.get_all_document_models()

    # Verify results
    assert len(documents) == 1
    assert UserDocument in documents
    assert BeanieDocument not in documents
    mock_get_all_subclasses.assert_called_once_with(Document)


def test_register_document_filter():
    """Test register_document_filter adds a filter function."""
    manager = DatabaseManager()
    initial_filter_count = len(manager._document_filters)

    # Define a custom filter
    def custom_filter(model):
        return True

    # Register the filter
    manager.register_document_filter(custom_filter)

    # Verify the filter was added
    assert len(manager._document_filters) == initial_filter_count + 1
    assert manager._document_filters[-1] == custom_filter


@pytest.mark.asyncio
@patch("smib.db.manager.init_beanie")
async def test_initialise(mock_init_beanie):
    """Test initialise method initializes beanie with document models."""
    # Setup mock
    mock_init_beanie.return_value = None

    # Create manager with mocked get_all_document_models
    manager = DatabaseManager()
    manager.get_all_document_models = MagicMock(return_value=[Document])
    manager.logger = MagicMock()

    # Call initialise
    await manager.initialise()

    # Verify init_beanie was called with correct parameters
    mock_init_beanie.assert_called_once_with(
        database=manager.client[manager.db_name],
        document_models=[Document]
    )
    # Verify logging
    manager.logger.info.assert_has_calls([
        call(f"Initializing database '{manager.db_name}' with 1 document(s)"),
        call("Documents: Document")
    ])


@patch("smib.db.manager.get_module_from_name")
@patch("smib.db.manager.get_actual_module_name")
def test_find_model_by_name(mock_get_actual_module_name, mock_get_module_from_name):
    """Test find_model_by_name finds a model by name and optionally by plugin."""
    # Create mock Document classes
    class UserDocument(Document):
        pass
    UserDocument.__module__ = "plugins.user_plugin.models"

    class PostDocument(Document):
        pass
    PostDocument.__module__ = "plugins.post_plugin.models"

    # Setup manager with mocked get_all_document_models
    manager = DatabaseManager()
    manager.get_all_document_models = MagicMock(return_value=[UserDocument, PostDocument])

    # Setup mocks for module name resolution
    # When get_module_from_name is called with 'plugins', return a mock module
    mock_module_plugins = MagicMock(__name__="plugins")
    mock_get_module_from_name.return_value = mock_module_plugins

    # When get_actual_module_name is called with the mock module, return the plugin name
    mock_get_actual_module_name.side_effect = lambda module: "user_plugin" if module is mock_module_plugins else "post_plugin"

    # Test finding by name only
    model = manager.find_model_by_name("UserDocument")
    assert model == UserDocument

    # Test finding by name and plugin
    model = manager.find_model_by_name("UserDocument", plugin_name="user_plugin")
    assert model == UserDocument

    # Test finding by name with wrong plugin
    model = manager.find_model_by_name("UserDocument", plugin_name="wrong_plugin")
    assert model is None

    # Test finding non-existent model
    model = manager.find_model_by_name("NonExistentModel")
    assert model is None
