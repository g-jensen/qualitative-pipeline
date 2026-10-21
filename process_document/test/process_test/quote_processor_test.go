package test

import (
	sut "process_document/m/v2/internal/process"
	"process_document/m/v2/internal/quote"
	"process_document/m/v2/test/extract_test"
	"testing"

	"github.com/stretchr/testify/assert"
)

func identity[T any](value T) T {
	return value
}

func zipMapFn[I any, K comparable, O any](f func(I) K, inputs []I, outputs []O) map[K]O {
	outputMap := make(map[K]O)
	for i, input := range inputs {
		outputMap[f(input)] = outputs[i]
	}
	return outputMap
}

func zipMap[I comparable, O any](inputs []I, outputs []O) map[I]O {
	return zipMapFn(identity, inputs, outputs)
}

// func mockedDocumentProcessor(
// 	quoteExtractionMap map[string][]quote.Quote,
// ) sut.DocumentProcessor {
// 	return sut.DocumentProcessor{
// 		QuoteExtractor: extract_test.TestQuoteExtractor{
// 			ExtractionMap: quoteExtractionMap,
// 		},
// 		VerbExtractor: extract_test.TestVerbExtractor{
// 			ExtractionMap: verbExtractionMap,
// 		},
// 		KeypointExtractor: extract_test.TestKeypointExtractor{
// 			ExtractionMap: keypointExtractionMap,
// 		},
// 		DetailExtractor: extract_test.TestDetailExtractor{
// 			ExtractionMap: detailExtractionMap,
// 		},
// 	}
// }

func _mockedDocumentProcessor(
	testQuote quote.Quote,
	testVerb string,
	testKeypoint string,
	testDetail string,
) sut.QuoteProcessor {
	verbExtractionMap := map[quote.Quote]string{
		testQuote: testVerb,
	}

	keypointExtractionMap := map[extract_test.TestKeypointInput]string{
		{Quote: testQuote, Verb: testVerb}: testKeypoint,
	}

	detailExtractionMap := map[extract_test.TestDetailInputs]string{
		{Quote: testQuote, Verb: testVerb, Keypoint: testKeypoint}: testDetail,
	}
	return sut.QuoteProcessor{
		VerbExtractor: extract_test.TestVerbExtractor{
			ExtractionMap: verbExtractionMap,
		},
		KeypointExtractor: extract_test.TestKeypointExtractor{
			ExtractionMap: keypointExtractionMap,
		},
		DetailExtractor: extract_test.TestDetailExtractor{
			ExtractionMap: detailExtractionMap,
		},
	}
}

// func TestProcess_NoQuotes(t *testing.T) {
// 	testDocument := "I ate a salad last night. I ate a burger in the morning"
//
// }

func zipKeypointMap(
	quotes []quote.Quote,
	verbs []string,
	keypoints []string,
) map[extract_test.TestKeypointInput]string {
	outputMap := make(map[extract_test.TestKeypointInput]string)
	for i, quote := range quotes {
		input := extract_test.TestKeypointInput{Quote: quote, Verb: verbs[i]}
		outputMap[input] = keypoints[i]
	}
	return outputMap
}

func zipDetailMap(
	quotes []quote.Quote,
	verbs []string,
	keypoints []string,
	details []string,
) map[extract_test.TestDetailInputs]string {
	outputMap := make(map[extract_test.TestDetailInputs]string)
	for i, quote := range quotes {
		input := extract_test.TestDetailInputs{Quote: quote, Verb: verbs[i], Keypoint: keypoints[i]}
		outputMap[input] = details[i]
	}
	return outputMap
}

func TestProcess_SingleQuote(t *testing.T) {
	burgerQuote := quote.Quote{
		Content: "I ate a burger in the morning",
		Kind:    "inner thinking",
		Interval: &quote.QuoteInterval{
			Start: 26,
			End:   55,
		},
	}
	// foodQuotes := []quote.Quote{burgerQuote}
	// foodVerbs := []string{"eats"}
	// foodKeypoints := []string{"a burger"}
	// foodDetails := []string{"in the morning"}
	// quoteMap := zipMap([]string{foodDocument}, [][]quote.Quote{foodQuotes})
	// verbMap := zipMap(foodQuotes, foodVerbs)
	// keypointMap := zipKeypointMap(foodQuotes, foodVerbs, foodKeypoints)
	// detailMap := zipDetailMap(foodQuotes, foodVerbs, foodKeypoints, foodDetails)

	processor := _mockedDocumentProcessor(
		burgerQuote,
		"eats", "a burger", "in the morning",
	)

	in := make(chan quote.Quote)
	out := make(chan sut.ProcessedQuote)
	processor.Process(in, out)
	in <- burgerQuote
	close(in)

	result := <-out
	expectedResult := sut.ProcessedQuote{
		Verb:     "Eats",
		KeyPoint: "a burger",
		Detail:   "in the morning",
	}
	assert.Equal(t, expectedResult, result)
}

func TestProcess_Forcing_SingleQuote(t *testing.T) {
	q := quote.Quote{
		Content: "I drank a glass of water last night",
		Kind:    "inner thinking",
		Interval: &quote.QuoteInterval{
			Start: 0,
			End:   35,
		},
	}
	processor := _mockedDocumentProcessor(
		q,
		"drinks", "a glass of water", "last night",
	)

	in := make(chan quote.Quote)
	out := make(chan sut.ProcessedQuote)
	processor.Process(in, out)
	in <- q
	close(in)

	result := <-out
	expectedResult := sut.ProcessedQuote{
		Verb:     "Drinks",
		KeyPoint: "a glass of water",
		Detail:   "last night",
	}
	assert.Equal(t, expectedResult, result)
}
