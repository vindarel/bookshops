### Librairiedeparis scraper

It returns:

- `authors`: a list
- `availability`: a string (new in v0.3)
- `card_type`: either "book", "cd", etc
- `data_source`: name of the website
- `date_publication`: as a string, to be parsed (`dateparser` lib for example) later on (since v0.3)
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

### Getting book reviews

We can search for book reviews on [lmda.net](http://www.lmda.net) (or
rather, we look for content on this site hoping that it is a review
about the book).

```
librairiedeparisScraper.review(card_dictionnary)
```

or

    livres 9782918059363 -r  # -r to get reviews
