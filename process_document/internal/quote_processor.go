package internal

import (
	"process_document/m/v2/internal/extract"
	"process_document/m/v2/internal/quote"
	"unicode"
	"unicode/utf8"
)

type QuoteProcessor struct {
	VerbExtractor     extract.VerbExtractor
	KeypointExtractor extract.KeypointExtractor
	DetailExtractor   extract.DetailExtractor
}

type ProcessedQuote struct {
	OriginalQuote *quote.Quote
	Verb          string
	KeyPoint      string
	Detail        string
}

func uppercaseFirst(s string) string {
	if len(s) == 0 {
		return ""
	}
	r, size := utf8.DecodeRuneInString(s)
	return string(unicode.ToUpper(r)) + s[size:]
}

func (processor QuoteProcessor) ProcessBatch(quotes []quote.Quote) []ProcessedQuote {
	quote := quotes[0]

	verb, _ := processor.VerbExtractor.FromQuote(quote)
	keypoint, _ := processor.KeypointExtractor.FromQuote(quote, verb)
	detail, _ := processor.DetailExtractor.FromQuote(quote, verb, keypoint)

	return []ProcessedQuote{
		{
			Verb:     uppercaseFirst(verb),
			KeyPoint: keypoint,
			Detail:   detail,
		},
	}
}
