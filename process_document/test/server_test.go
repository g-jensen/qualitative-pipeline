package test

// don't run for now
// func _TestServer(t *testing.T) {
// 	testExtractor := extract_test.TestQuoteExtractor{
// 		Output: []quote.Quote{
// 			{
// 				Content: "I ate a burger in the morning",
// 				Kind:    "inner thinking",
// 				Interval: &quote.QuoteInterval{
// 					Start: 26,
// 					End:   55,
// 				},
// 			},
// 		},
// 	}
// 	handler := sut.NewHandler(testExtractor)
//
// 	documentContent := "I ate a salad last night. I ate a burger in the morning"
// 	body := strings.NewReader(documentContent)
// 	req := httptest.NewRequest(http.MethodPost, "/insights", body)
// 	rec := httptest.NewRecorder()
//
// 	handler.ServeHTTP(rec, req)
//
// 	assert.Equal(t, http.StatusOK, rec.Code)
// 	assert.Equal(t, "not greg", rec.Body.String())
// }
