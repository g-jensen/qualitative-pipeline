package internal

import (
	"io"
	"net/http"
	"process_document/m/v2/internal/extract"
)

type Handler struct {
	QuoteExtractor extract.QuoteExtractor
	QuoteProcessor QuoteProcessor
}

// maybe just remove this... it's pretty useless.
func (h *Handler) New(quoteExtractor extract.QuoteExtractor, quoteProcessor QuoteProcessor) *Handler {
	return &Handler{
		QuoteExtractor: quoteExtractor,
		QuoteProcessor: quoteProcessor,
	}
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	body_bytes, _ := io.ReadAll(r.Body)
	body := string(body_bytes)
	w.Write([]byte(body + "the"))
}
