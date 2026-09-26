import langextract as lx

BURGERS_DOCUMENT = lx.data.AnnotatedDocument(
    text="I like chicken. I like burgers.",
    extractions=[
        lx.data.Extraction(
            extraction_text="I like burgers.",
            extraction_class="personal rule",
            char_interval=lx.data.CharInterval(start_pos=16,end_pos=31)
        )
    ]
)

def stub_fn(_request):
    return BURGERS_DOCUMENT