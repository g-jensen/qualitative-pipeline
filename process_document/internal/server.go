package internal

import (
	"io"
	"net/http"
	"process_document/m/v2/internal/extract"
)

type Handler struct {
	QuoteExtractor extract.QuoteExtractor
}

func NewHandler(quoteExtractor extract.QuoteExtractor) *Handler {
	return &Handler{
		QuoteExtractor: quoteExtractor,
	}
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	body_bytes, _ := io.ReadAll(r.Body)
	body := string(body_bytes)
	w.Write([]byte(body + "the"))
}
