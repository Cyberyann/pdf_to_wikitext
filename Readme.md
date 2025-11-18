**PDF_TO_WIKITEXT**
Application create a wikitext page on a Wikimedia, in output folder got a log and the source of the page.  

**Create an python environement**  
`python -m venv .venv`  

**Installation of libraries**  
`pip install -r requirements.txt`   

**Create .env file**  
Create a .env file from .env.example file and fill it with your values  

**Launch dev environement**  
`fastapi dev main.py`  

**Curl call sample**  
`curl -X POST "http://localhost:8000/pdf-to-wikitext/" -F "file=@D1.9.pdf" -F "footer=D1.9 Data Management Plan" -F "ignore_pages=0,2,3" -F "page_name=D1.9" `  
Where  
* file=file to manage
* footer= footer in file to calculate page number and remove it
* ignore_pages=page number separate by comma to ignore (first page is 0)
* page_name= use to create a wiki page with this name (not active for the moment)
