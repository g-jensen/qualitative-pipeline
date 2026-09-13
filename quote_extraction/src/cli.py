import typer
import uvicorn
import api # Technically not necessary, but I like it. See "api:app" in this file
import os

app = typer.Typer()


def should_reload():
    return (os.environ.get("RUN_MODE") != "production")


@app.command()
def serve(port: int = 8080):
    uvicorn.run("api:app", host="127.0.0.1", port=port, reload=should_reload())
