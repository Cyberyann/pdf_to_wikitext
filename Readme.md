**Create an python environement**
`python -m venv .venv`

**Installation of libraries**
`pip install -r requirements.txt` 

**Launch dev environement**
`fastapi dev main.py`

**Curl call sample**
`curl -X POST "http://localhost:8000/pdf-to-wikitext/" -F "file=@D1.9.pdf" -F "footer=D1.9 Data Management Plan" -F "ignore_pages=0,2,3" -F "article_name=D1.9" -o ../D1.9.txt`

where
* file=file to manage
* footer= footer in file to calculate page number and remove it
* ignore_pages=page number separate by comma to ignore (first page is 0)
* article_name= use to create a wiki page with this name (not active for the moment)
