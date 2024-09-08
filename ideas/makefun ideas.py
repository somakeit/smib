import inspect

import makefun
from fastapi import FastAPI

app = FastAPI()


# Define a base function signature to guide makefun
def base_func(path: str, *args, **kwargs):
    pass


# Create a function copying the signature/argspec from base_func
@makefun.with_signature(inspect.signature(base_func))
def smib_http(*args, **kwargs):
    return app.get(*args, **kwargs)



# Example usage
@smib_http("/example")
async def example_get():
    return {"message": "This is an example"}

# If you need to run the FastAPI app, uncomment below
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)
