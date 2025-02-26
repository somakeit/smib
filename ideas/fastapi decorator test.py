from fastapi import FastAPI, Request
from typing import Callable, Any
import uvicorn

# Initialize the FastAPI app
app = FastAPI()


# Create a custom decorator
def custom_decorator(func: Callable) -> Callable:
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        print("[Decorator]: Before handling request")
        response = await func(*args, **kwargs)
        print("[Decorator]: After handling request")
        return response

    return wrapper


# Function to patch the specific method decorators
def patch_fastapi_app_methods(app: FastAPI) -> None:
    def patch_method(method_name: str):
        original_method = getattr(app, method_name)

        def patched_method(path: str, *args: Any, **kwargs: Any):
            def decorator(endpoint: Callable):
                decorated_endpoint = custom_decorator(endpoint)
                return original_method(path, *args, **kwargs)(decorated_endpoint)

            return decorator

        setattr(app, method_name, patched_method)

    for method in ['get', 'post', 'put', 'patch']:
        patch_method(method)


# Patch the app's HTTP method decorators before defining the routes
patch_fastapi_app_methods(app)


# Define some endpoints using different HTTP methods
@app.get('/hello')
async def hello(request: Request):
    print("[Endpoint]: Handling GET request")
    return {"message": "Hello, World!"}


@app.post('/hello')
async def post_hello(request: Request):
    print("[Endpoint]: Handling POST request")
    return {"message": "Hello, POST!"}


@app.put('/hello')
async def put_hello(request: Request):
    print("[Endpoint]: Handling PUT request")
    return {"message": "Hello, PUT!"}


@app.patch('/hello')
async def patch_hello(request: Request):
    print("[Endpoint]: Handling PATCH request")
    print(aaaaa)
    return {"message": "Hello, PATCH!"}


# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
