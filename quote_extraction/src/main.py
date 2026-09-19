from .cli import app
from . import log


def main():
    log.init()
    app()


if __name__ == "__main__":
    main()