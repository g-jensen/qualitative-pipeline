import argparse
import extraction as ex

DEFAULT_QUESTION = "How do people orient, decide, and react as they notice, choose, and make meaning from their own choices that recently surprised them?"

def parse_args():
    parser = argparse.ArgumentParser(description="Extract quotes from a document")
    parser.add_argument("-f",  "--file", type=str, default="synthesized_documents/210_Adopting_the_older_dog.docx", help="Document to read")
    parser.add_argument("-id",  "--document_id", type=str, required=True, help="ID of document")
    parser.add_argument("-o",  "--output", type=str, default="extraction.jsonl", help="Where to output the extraction")
    parser.add_argument("-ex", "--examples_file", type=str, default="examples.json", help="File to read examples from")
    parser.add_argument("-n",  "--minimum_example_count", type=int, default=5, help="Guarantees at least N examples of each type")
    parser.add_argument("-q",  "--question", type=str, default=DEFAULT_QUESTION, help="Question that the extractions should be relevant to")
    parser.add_argument("-m",  "--model", type=str, required=True, help="Name of the LLM used in processing (e.g. \"claude-haiku-4-5\")")
    parser.add_argument("--model_url", type=str, default="http://localhost:11434", help="Url of LLM (e.g. if it is locally hosted)")
    return parser.parse_args()

def main():
    ex.extract_and_save(parse_args())

if __name__ == "__main__":
    main()

# TODO - integration tests