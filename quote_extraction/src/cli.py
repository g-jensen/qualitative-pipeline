import typer
import api
import os

app = typer.Typer()


def should_reload():
    return (os.environ.get("RUN_MODE") != "production")


@app.command()
def serve(port: int = 8080):
    api.serve(1234)