package test_process

import (
	sut "process_document/m/v2/internal/process"
	"process_document/m/v2/internal/quote"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestProcess_SingleQuote(t *testing.T) {
	burgerQuote := quote.Quote{
		Content: "I ate a burger in the morning",
		Kind:    "inner thinking",
		Interval: &quote.QuoteInterval{
			Start: 26,
			End:   55,
		},
	}

	maps := NewTestQuoteProcessorMaps()
	maps.Add(burgerQuote, "eats", "a burger", "in the morning")
	processor := TestQuoteProcessor(maps)

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
	waterQuote := quote.Quote{
		Content: "I drank a glass of water last night",
		Kind:    "inner thinking",
		Interval: &quote.QuoteInterval{
			Start: 0,
			End:   35,
		},
	}

	maps := NewTestQuoteProcessorMaps()
	maps.Add(waterQuote, "drinks", "a glass of water", "last night")
	processor := TestQuoteProcessor(maps)

	in := make(chan quote.Quote)
	out := make(chan sut.ProcessedQuote)
	processor.Process(in, out)
	in <- waterQuote
	close(in)

	result := <-out
	expectedResult := sut.ProcessedQuote{
		Verb:     "Drinks",
		KeyPoint: "a glass of water",
		Detail:   "last night",
	}
	assert.Equal(t, expectedResult, result)
}
