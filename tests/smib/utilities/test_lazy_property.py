import pytest
from smib.utilities.lazy_property import lazy_property


class TestLazyProperty:

    def setup_method(self):
        """Setup a test class for lazy_property."""

        class TestClass:
            @lazy_property
            def lazy_value(self):
                return 42

        self.TestClass = TestClass
        self.obj = TestClass()

    def test_lazy_property_initial_computation(self):
        """Test that lazy_property computes the value lazily on first access."""
        assert 'lazy_value' not in self.obj.__dict__

        assert self.obj.lazy_value == 42
        assert 'lazy_value' in self.obj.__dict__

    def test_lazy_property_computation_once(self):
        """Test that the lazy_property is computed only once."""

        class TestClass:
            def __init__(self):
                self.call_counter = 0

            @lazy_property
            def computed_value(self):
                self.call_counter += 1  # Increment counter every time the function is called
                return 42

        obj = TestClass()
        assert obj.call_counter == 0  # Initially, the function isn't called

        # First access - computes value
        assert obj.computed_value == 42
        assert obj.call_counter == 1  # Called once

        # Second access - uses cached value
        assert obj.computed_value == 42
        assert obj.call_counter == 1  # No new computation after the first access

    def test_lazy_property_manual_override(self):
        """Test manually setting a lazy_property value."""
        assert self.obj.lazy_value == 42
        self.obj.lazy_value = 100
        assert self.obj.lazy_value == 100

    def test_descriptor_on_class(self):
        """Line 13: Accessing the lazy_property on the class should return the descriptor."""
        descriptor = self.TestClass.lazy_value
        assert isinstance(descriptor, lazy_property)

    def test_lazy_property_delete(self):
        """Lines 22-23: Test the __delete__ method functionality."""
        # Access the lazy property to set it
        assert self.obj.lazy_value == 42

        # Delete the property and confirm it's removed
        del self.obj.lazy_value
        assert 'lazy_value' not in self.obj.__dict__
