from fastapi import FastAPI, Request, APIRouter

app = FastAPI()

space = APIRouter()

@space.get("/")
async def root(req: Request):
    print(req.client.host)
    return {"message": "Hello World"}


app.include_router(space)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
