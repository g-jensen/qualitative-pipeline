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
	Verb     string
	KeyPoint string
	Detail   string
}

func uppercaseFirst(s string) string {
	if len(s) == 0 {
		return ""
	}
	r, size := utf8.DecodeRuneInString(s)
	return string(unicode.ToUpper(r)) + s[size:]
}

func (processor QuoteProcessor) Process(in <-chan quote.Quote, out chan<- ProcessedQuote) {
	go func() {
		defer close(out)
		quote := <-in

		verb, _ := processor.VerbExtractor.FromQuote(quote)
		keypoint, _ := processor.KeypointExtractor.FromQuote(quote, verb)
		detail, _ := processor.DetailExtractor.FromQuote(quote, verb, keypoint)

		out <- ProcessedQuote{
			Verb:     uppercaseFirst(verb),
			KeyPoint: keypoint,
			Detail:   detail,
		}
	}()
}
