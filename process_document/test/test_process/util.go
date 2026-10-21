package test_process

import (
	"process_document/m/v2/internal/process"
	"process_document/m/v2/internal/quote"
	"process_document/m/v2/test/test_extract"
)

type TestQuoteProcessorMaps struct {
	verbMap     map[quote.Quote]string
	keypointMap map[test_extract.TestKeypointInput]string
	detailMap   map[test_extract.TestDetailInputs]string
}

func NewTestQuoteProcessorMaps() TestQuoteProcessorMaps {
	return TestQuoteProcessorMaps{
		verbMap:     map[quote.Quote]string{},
		keypointMap: map[test_extract.TestKeypointInput]string{},
		detailMap:   map[test_extract.TestDetailInputs]string{},
	}
}

func (maps TestQuoteProcessorMaps) AddVerb(
	quote quote.Quote,
	verb string,
) {
	maps.verbMap[quote] = verb
}

func (maps TestQuoteProcessorMaps) AddKeypoint(
	quote quote.Quote,
	verb string,
	keypoint string,
) {
	maps.keypointMap[test_extract.TestKeypointInput{Quote: quote, Verb: verb}] = keypoint
}

func (maps TestQuoteProcessorMaps) AddDetail(
	quote quote.Quote,
	verb string,
	keypoint string,
	detail string,
) {
	maps.detailMap[test_extract.TestDetailInputs{Quote: quote, Verb: verb, Keypoint: keypoint}] = detail
}

func (maps TestQuoteProcessorMaps) Add(
	quote quote.Quote,
	verb string,
	keypoint string,
	detail string,
) {
	maps.AddVerb(quote, verb)
	maps.AddKeypoint(quote, verb, keypoint)
	maps.AddDetail(quote, verb, keypoint, detail)
}

func TestQuoteProcessor(maps TestQuoteProcessorMaps) process.QuoteProcessor {
	return process.QuoteProcessor{
		VerbExtractor: test_extract.TestVerbExtractor{
			ExtractionMap: maps.verbMap,
		},
		KeypointExtractor: test_extract.TestKeypointExtractor{
			ExtractionMap: maps.keypointMap,
		},
		DetailExtractor: test_extract.TestDetailExtractor{
			ExtractionMap: maps.detailMap,
		},
	}
}
