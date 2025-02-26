from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
async def root(req: Request):

    print(req.client.host)
    return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)