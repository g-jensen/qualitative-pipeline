package test_extract

import (
	"errors"
	"process_document/m/v2/internal/quote"
)

type TestDetailInputs struct {
	Quote    quote.Quote
	Verb     string
	Keypoint string
}

type TestDetailExtractor struct {
	ExtractionMap map[TestDetailInputs]string
}

func (extractor TestDetailExtractor) FromQuote(quote quote.Quote, verb string, keypoint string) (string, error) {
	output, exists := extractor.ExtractionMap[TestDetailInputs{quote, verb, keypoint}]
	if exists {
		return output, nil
	}
	return "", errors.New("Can't extract detail from quote")
}
