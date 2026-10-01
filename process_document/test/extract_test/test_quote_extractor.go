package extract_test

import (
	"errors"
	"process_document/m/v2/internal/quote"
)

type TestQuoteExtractor struct {
	ExtractionMap map[string][]quote.Quote
}

func (extractor TestQuoteExtractor) FromDocument(document string) ([]quote.Quote, error) {
	output, exists := extractor.ExtractionMap[document]
	if exists {
		return output, nil
	}
	return nil, errors.New("Can't extract quotes from document")
}
