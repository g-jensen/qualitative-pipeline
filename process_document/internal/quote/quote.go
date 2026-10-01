package quote

type QuoteInterval struct {
	Start int
	End   int
}

type Quote struct {
	Content  string
	Kind     string
	Interval *QuoteInterval
}
