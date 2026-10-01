package extract

import "process_document/m/v2/internal/quote"

type QuoteExtractor interface {
	FromDocument(document string) ([]quote.Quote, error)
}
