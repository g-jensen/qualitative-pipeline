package extract

import "process_document/m/v2/internal/quote"

type VerbExtractor interface {
	FromQuote(quote quote.Quote) (*string, error)
}
