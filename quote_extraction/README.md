# quote_extraction

Requires the `uv` Python package manager

## Development

### Install all dependencies
```bash
uv sync --all-groups
```

### Generate Protobuf Files
```bash
./generate_protos.sh
```

### Run
```bash
uv run src/main.py
```

### Test
```bash
pytest .
```