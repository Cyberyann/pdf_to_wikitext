**PDF_TO_WIKITEXT**
Application create a wikitext page on a Mediawiki, in output folder got a log and the source of the page.  

**Create an python environement**  
`python -m venv .venv`  

**Installation of libraries**  
`pip install -r requirements.txt`   

**Create work folder**  
Project need 2 folder to work. They are defined in the .env file  
- images
- output  

You can create like this in the project folder (they are in the .gitignore) or use others folders  

**Create .env file**  
Create a .env file from .env.example file and fill it with your values  

**Launch dev environement**  
`fastapi dev main.py`  

**Curl call sample**  
*To transform PDF file to WIKITEXT file and create Mediawiki page*
`curl -X POST "http://localhost:8000/pdf-to-wikitext/" -F "file=@D1.9.pdf" -F "footer=D1.9 Data Management Plan" -F "ignore_pages=0,2,3" -F "page_name=D1.9" -F "generate_page=true"`  
Where  
* file=file to manage
* footer= footer in file to calculate page number and remove it
* ignore_pages=page number separate by comma to ignore (first page is 0)
* page_name= use to create a wiki page with this name (not active for the moment)
* generate_page= if "true", generate page on Mediawiki  

*To create a Mediawiki page from WIKITEXT file*
`curl -X POST "http://localhost:8000/create_mediawiki_page/" -F "file=@output/D1.9.txt" -F "page_name=D1.9"`  
Where  
* file=file to manage
* page_name= use to create a wiki page with this name (not active for the moment)
