### Librairiedeparis scraper

It returns:

- `authors`: a list
- `card_type`: either "book", "cd", etc
- `data_source`: name of the website
- `date_publication`: as a string, to be parsed (`dateparser` lib for example) later on
- `details_url`: url of this product's own page, where are more details
- `img`: url to the cover
- `isbn`: string
- `price`: a float
- `publishers`: list
- `search_terms`
- `search_url`
- `summary`
- `title`

It needs one pass (it grabs the isbn and the price on the first pass).
