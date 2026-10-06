# AI pipeline

`pipeline.py` validates an image/text request, extracts image features,
appends OCR text to the query, and delegates candidate retrieval and ranking
to the Week 03 search engine. Face and CLIP embeddings are kept separate and
are combined at the application ranking layer.

