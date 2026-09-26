import typer
from . import api


app = typer.Typer()


@app.command()
def serve(port: int=8080, max_workers: int=10):
    api.serve(port, max_workers)
