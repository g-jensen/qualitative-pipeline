package internal

import (
	"process_document/m/v2/internal/extract"
	"unicode"
	"unicode/utf8"
)

type DocumentProcessor struct {
	QuoteExtractor    extract.QuoteExtractor
	VerbExtractor     extract.VerbExtractor
	KeypointExtractor extract.KeypointExtractor
	DetailExtractor   extract.DetailExtractor
}

type ProcessResult struct {
	Verb     string
	KeyPoint string
	Detail   *string
}

func uppercaseFirst(s string) string {
	if len(s) == 0 {
		return ""
	}
	r, size := utf8.DecodeRuneInString(s)
	return string(unicode.ToUpper(r)) + s[size:]
}

func (processor DocumentProcessor) Process(document string) []ProcessResult {
	quotes, _ := processor.QuoteExtractor.FromDocument(document)
	quote := quotes[0]

	verb, _ := processor.VerbExtractor.FromQuote(quote)
	keypoint, _ := processor.KeypointExtractor.FromQuote(quote, *verb)
	detail, _ := processor.DetailExtractor.FromQuote(quote, *verb, *keypoint)

	return []ProcessResult{
		{
			Verb:     uppercaseFirst(*verb),
			KeyPoint: *keypoint,
			Detail:   detail,
		},
	}
}
