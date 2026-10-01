package extract_test

import (
	"errors"
	"process_document/m/v2/internal/quote"
)

type TestKeypointInput struct {
	Quote quote.Quote
	Verb  string
}

type TestKeypointExtractor struct {
	ExtractionMap map[TestKeypointInput]string
	Inputs        TestKeypointInput
	Output        string
}

func (extractor TestKeypointExtractor) FromQuote(quote quote.Quote, verb string) (*string, error) {
	output, exists := extractor.ExtractionMap[TestKeypointInput{quote, verb}]
	if exists {
		return &output, nil
	}
	return nil, errors.New("Can't extract keypoint from quote")
}
