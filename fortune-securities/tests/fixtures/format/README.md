# Hand-written FORMAT fixtures (not captured responses)

Every file here was written by hand to the documented or observed response
shape of a source (NSE, BSE, Yahoo, Google News RSS, a company IR page, an
XBRL results instance). They describe a **fictional company, EXAMPLECO**
(ISIN INEZ9E101010, BSE code 999001), and every value is invented.

They prove the parsers handle that shape. They do **not** prove the live
endpoint still returns it. That is what `python -m fortune_research health`
checks, and `health --capture DIR` saves real responses (with URL, retrieval
time and SHA-256) to use as real-source fixtures once network access is available.
