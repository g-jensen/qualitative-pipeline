import typer

app = typer.Typer()


@app.command()
def serve(port: int = 8080):
    print(f"Serving on port {port}")

if __name__ == "__main__":
    app()