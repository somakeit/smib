import pytest
from smib.utilities.dynamic_caller import dynamic_caller


def test_dynamic_caller_with_exact_arguments():
    """Test if dynamic_caller works when exact matching arguments are provided."""

    def test_func(arg1, arg2):
        return arg1 + arg2

    result = dynamic_caller(test_func, arg1=5, arg2=10)
    assert result == 15


def test_dynamic_caller_with_extra_arguments():
    """Test if dynamic_caller ignores extra arguments not in the function's signature."""

    def test_func(arg1, arg2):
        return arg1 * arg2

    result = dynamic_caller(test_func, arg1=3, arg2=4, arg3="extra")
    assert result == 12  # `arg3` should be ignored


def test_dynamic_caller_with_missing_required_arguments():
    """Test if dynamic_caller raises an exception when required arguments are missing."""

    def test_func(arg1, arg2):
        return arg1 - arg2

    with pytest.raises(ValueError) as exc_info:
        dynamic_caller(test_func, arg1=7)  # `arg2` is missing

    assert "Invalid required parameter" in str(exc_info.value)
    assert "arg2" in str(exc_info.value)


def test_dynamic_caller_with_optional_arguments():
    """Test if dynamic_caller correctly handles functions with optional arguments."""

    def test_func(arg1, arg2=10):
        return arg1 + arg2

    result_with_default = dynamic_caller(test_func, arg1=5)  # arg2 should use the default value (10)
    assert result_with_default == 15

    result_with_provided = dynamic_caller(test_func, arg1=5, arg2=20)  # arg2 is explicitly provided
    assert result_with_provided == 25


def test_dynamic_caller_with_no_arguments():
    """Test if dynamic_caller works for functions with no arguments."""

    def test_func():
        return "no arguments"

    result = dynamic_caller(test_func, some_random_arg="ignored")
    assert result == "no arguments"


@pytest.mark.asyncio
async def test_dynamic_caller_with_async_function():
    """Test dynamic_caller with an asynchronous function."""

    async def async_func(arg1, arg2):
        return arg1 + arg2

    result = await dynamic_caller(async_func, arg1=5, arg2=10)
    assert result == 15


@pytest.mark.asyncio
async def test_dynamic_caller_async_with_extra_arguments():
    """Test dynamic_caller with async function and extra arguments."""

    async def async_func(arg1, arg2=10):
        return arg1 * arg2

    result = await dynamic_caller(async_func, arg1=3, arg2=5, extra_arg="ignored")
    assert result == 15  # `extra_arg` should be ignored


@pytest.mark.asyncio
async def test_dynamic_caller_async_missing_arguments():
    """Test dynamic_caller raises error when async function is missing required arguments."""

    async def async_func(arg1, arg2, arg3):
        return arg1 + arg2 + arg3

    with pytest.raises(ValueError) as exc_info:
        await dynamic_caller(async_func, arg1=1, arg2=2)  # Missing arg3

    assert "Invalid required parameter" in str(exc_info.value)
    assert "arg3" in str(exc_info.value)


@pytest.mark.asyncio
async def test_dynamic_caller_async_with_optional_argument():
    """Test dynamic_caller with async function and optional arguments."""

    async def async_func(arg1, arg2=10):
        return arg1 + arg2

    result_with_default = await dynamic_caller(async_func, arg1=5)  # arg2 uses default value (10)
    assert result_with_default == 15

    result_with_explicit = await dynamic_caller(async_func, arg1=5, arg2=20)  # arg2 explicitly provided
    assert result_with_explicit == 25


@pytest.mark.asyncio
async def test_dynamic_caller_async_no_args_function():
    """Test dynamic_caller with async function that takes no arguments."""

    async def async_func():
        return "async no arguments"

    result = await dynamic_caller(async_func, random_arg="ignored")
    assert result == "async no arguments"
