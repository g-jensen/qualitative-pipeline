# qualitative-pipeline

## Usage

### Python

First, set up a virtual environment:
```
python3 -m venv .venv && source .venv/bin/activate
```

Then, install dependencies:
```
pip3 install -r requirements.txt
```

Maybe run tests
```
pytest src/
```

Generate examples:
```
python3 src/quote_extraction/generate_examples.py
```

Set your .env file
```
LANGEXTRACT_API_KEY=<any model api key>
```

Extract quotes:
```
set -a && source .env && set +a && python3 src/quote_extraction/main.py -m "claude-haiku-4-5" -id 210
```

Alternatively, you can use a local model by specifying it like `-m "gemma3:12b"` in which case you don't need `.env`

Visualize those extractions:
```
python3 src/quote_extraction/visualize.py
```

Then open `visualizations/generated_extraction.html` in your browser

### Node

First,
```
npm install
```

Maybe run tests
```
npm run test
```

You will probably have to add another line in your `.env` (TODO: fix this)
```
LANGEXTRACT_API_KEY=<provider key from before>
ANTHROPIC_API_KEY=<that same provder key>
```

Once you've generated an extraction from the Python script, you can run
```
set -a && source .env && set +a && npm run verb-framing -- -f extraction.jsonl -m "claude-haiku-4-5" -o output.xlsx
```

### Grafana

`src/verb_framing/` is already configured to point OpenTelemetry spans to Grafana (`grafana/`).

TODO - setup the same for `src/quote_extraction/`

#### Compile dashboards

Install jsonnet:
```bash
go install github.com/google/go-jsonnet/cmd/jsonnet@latest

go install github.com/jsonnet-bundler/jsonnet-bundler/cmd/jb@latest
```

Make sure `~/go/bin` is on your path:
```
export PATH=$PATH:~/go/bin
```

Inside `grafana/provisioning/`:
```
jb install github.com/grafana/grafonnet/gen/grafonnet-latest@main
```

Compile:
```
jsonnet -J vendor qualitative_pipeline.jsonnet > ../dashboards/qualitative_pipeline.json
```

## License

AGPLv3

