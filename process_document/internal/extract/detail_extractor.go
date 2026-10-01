package extract

import "process_document/m/v2/internal/quote"

type DetailExtractor interface {
	FromQuote(quote quote.Quote, verb string, keypoint string) (*string, error)
}
