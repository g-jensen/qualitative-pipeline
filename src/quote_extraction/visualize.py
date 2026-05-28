import argparse
from pathlib import Path
import langextract as lx

def add_paraphrase_attributes(result):
    for extraction in result.extractions:
        if extraction.char_interval is None:
            extraction.attributes = {"full_extraction": extraction.extraction_text}
        elif extraction.alignment_status != lx.data.AlignmentStatus.MATCH_EXACT:
            start_pos = extraction.char_interval.start_pos
            end_pos = extraction.char_interval.end_pos
            aligned_text = result.text[start_pos:end_pos]

            if aligned_text.strip() != extraction.extraction_text.strip():
                extraction.attributes = {"full_extraction": extraction.extraction_text}

def write_visualization(target, output):
    result = next(lx.io.load_annotated_documents_jsonl(Path(target)))
    add_paraphrase_attributes(result)
    lx.io.save_annotated_documents([result], output_name=".tmp.jsonl", output_dir=".")
    html = lx.visualize(".tmp.jsonl")
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        if hasattr(html, 'data'):
            f.write(html.data)
        else:
            f.write(html)
    print(f"Sucessfully wrote to {output}")

def main():
    parser = argparse.ArgumentParser(description="Visualize quotes")
    parser.add_argument("-f", "--target", type=str, default="extraction.jsonl", help="Extraction to visualize")
    parser.add_argument("-o", "--output", type=str, default="visualizations/generated_extraction.html", help="Where to output the visualization")
    args = parser.parse_args()

    write_visualization(args.target,args.output)

if __name__ == "__main__":
    main()