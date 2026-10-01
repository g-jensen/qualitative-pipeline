package extract

import "process_document/m/v2/internal/quote"

type KeypointExtractor interface {
	FromQuote(quote quote.Quote, verb string) (*string, error)
}
