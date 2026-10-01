package extract_test

import (
	"errors"
	"process_document/m/v2/internal/quote"
)

type TestVerbExtractor struct {
	ExtractionMap map[quote.Quote]string
}

func (extractor TestVerbExtractor) FromQuote(quote quote.Quote) (*string, error) {
	output, exists := extractor.ExtractionMap[quote]
	if exists {
		return &output, nil
	}
	return nil, errors.New("Can't extract verb from quote")
}
