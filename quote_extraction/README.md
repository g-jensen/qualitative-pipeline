# quote-extraction

Requires the `uv` Python package manager

## Quickstart

### Install all dependencies

```bash
uv sync --all-groups
```
And activate the environment:
```bash
source .venv/bin/activate
```

### Generate protobuf files

```bash
./scripts/generate_protos.sh
```

### Rename the app

```bash
./scripts/rename.sh new-name
```

Note that this will only work once.

### Setup environment

In `../.env` (`qualitative-pipeline/.env`) add your LLM api key:
```
LANGEXTRACT_API_KEY=<YOUR_LLM_API_KEY>
```

### Run the server with environment

```bash
set -a && source ../.env && set +a && uv run serve
```

### Unit tests

```bash
uv run test
```

### Component 'test'

You'll need [grpcurl](https://github.com/fullstorydev/grpcurl) to run this command. First, run the server, then run:

```bash
grpcurl -plaintext -proto idl/protos/extract.proto -d '{"topic": "Burgers", "document": "Interviewer: What foods do you like? Interviewee: I like chicken. I like burgers. But I have a general rule against eating peanuts.", "model": "claude-haiku-4-5"}' 127.0.0.1:8080 extract.Extract/Call
```

You should get an extracted quote like "But I have a general rule against eating peanuts."

### Adding a service

1. Create a new proto definition for your service in `idl/protos/my_service.proto`
2. Regenerate proto files: `./scripts/generate_protos.sh`
3. Run `python3 scripts/proto_boilerplate.py idl/protos/my_service.proto` to implement the boilerplate
    * Alternatively you can take inspiration from `src/servicers/extract/` to manually implement the boilerplate
4. Assert that boilerplate tests fail
    * Optionally you can implement your service logic now (before registration)
5. Register your service
    1. Add your service to the `stub_services_to_register` in `src/registrar_test.py`
    2. Assert that service registration tests fail
    3. Add your service to the `services_to_register` in `src/registrar.py`
    4. Assert that service registration tests now pass