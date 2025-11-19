from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from md_to_wikitext import md_to_wikitext
from mediawiki_api import MediaWikiApi
from logger import init_logger, log, log_step
from pathlib import Path
import pymupdf4llm
import tempfile
import os
import shutil

load_dotenv()


app = FastAPI(title="PDF Text Extractor to wikitext page API")


@app.post("/pdf-to-wikitext/")
async def extract_text_from_pdf(
    file: UploadFile = File(...),
    footer: str = Form(...),
    ignore_pages: str = Form(...),
    page_name: str = Form(...),
    generate_page: str = Form(...),
):
    """
    Endpoint to transform a pdf file in a wikitext and generate a Mediawiki page

    Args:
        file: PDF file
        footer: Reference footer
        ignore_pages: ignore pages number separate by ,
        page_name: Page reference name
        generate_page: if true, generate page on Mediawiki

    Generate:
        Log file and wikipage file

    Env:
        MEDIAWIKI_URL: Url of Mediawiki to generate images and page
        MEDIAWIKI_USER: User for Mediawiki connexion
        MEDIAWIKI_MDP: Password for Mediawiki connexion
        OUTPUT_FOLDER: Output folder for log and Mediawiki page file

    Returns:
        Nothing
    """
    if not page_name:
        raise HTTPException(status_code=400, detail="page_name must be fill")

    page_name_final = page_name.lower().replace(" ", "_")

    init_logger(
        f"{page_name_final}_pdf_to_wikitext", os.getenv("OUTPUT_FOLDER") or "./output"
    )

    log_step("Init application")
    txt_output_filename = f"{os.getenv("OUTPUT_FOLDER")}/{page_name_final}.txt"
    md_output_filename = f"{os.getenv("OUTPUT_FOLDER")}/{page_name_final}.md"
    if os.path.exists(txt_output_filename):
        os.unlink(txt_output_filename)
    if os.path.exists(md_output_filename):
        os.unlink(md_output_filename)
    image_path = f"{os.getenv("IMAGES_FOLDER")}/{file.filename[:-4]}/"  # type: ignore

    log_step("Create temporary file")
    temp_file = Path(f"{os.getenv("OUTPUT_FOLDER")}/{page_name_final}.pdf")
    with temp_file.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    log_step("Transform Pdf content to md text and store image")
    try:
        md_text = pymupdf4llm.to_markdown(
            temp_file, write_images=True, image_path=image_path
        )
    except Exception as e:
        log(f"Error in PDF to MD transformation: {str(e)}")
        return

    log_step("Remove temporary file")
    os.unlink(temp_file)

    log_step("Create md file")
    with open(md_output_filename, "w", encoding="utf-8") as fichier:
        fichier.write(md_text)

    log_step("Transform MD to wikitext and create image on Mediawiki")
    try:
        wikitext = md_to_wikitext(
            md_text, footer, ignore_pages, page_name_final, image_path
        )
    except Exception as e:
        log(f"Error in MD to WIKITEXT transformation: {str(e)}")
        return

    log_step("Remove image folder")
    shutil.rmtree(image_path)

    log_step("Create wikitext file")
    with open(txt_output_filename, "w", encoding="utf-8") as fichier:
        fichier.write(wikitext)

    log_step("Annotate wikitext with ontology")
    # TODO

    if generate_page == "true":
        log_step("Create Mediawiki page")
        mediawiki_api = MediaWikiApi()
        if not mediawiki_api.login():
            log("Cant connect to mediawiki")
        else:
            return_page_url = mediawiki_api.create_page(page_name_final, wikitext)
            log(f"Page generation result: {return_page_url}")


@app.post("/get_wikitext_file/")
async def get_wikitext_file(
    page_name: str = Form(...),
):
    """
    Endpoint to get wikitext file for a page_name

    Args:
        page_name: Page reference name

    Env:
        OUTPUT_FOLDER: Output folder for log and Mediawiki page file

    Returns:
        wikitext file content
    """
    if not page_name:
        raise HTTPException(status_code=400, detail="page_name must be fill")

    page_name_final = page_name.lower().replace(" ", "_")

    file_path = f"{os.getenv("OUTPUT_FOLDER")}/{page_name_final}.txt"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File '{file_path}' not found")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content


@app.post("/get_last_log/")
async def get_last_log(
    page_name: str = Form(...),
):
    """
    Endpoint to get last log for a page_name

    Args:
        page_name: Page reference name

    Env:
        OUTPUT_FOLDER: Output folder for log and Mediawiki page file

    Returns:
        Last log file content
    """
    if not page_name:
        raise HTTPException(status_code=400, detail="page_name must be fill")

    page_name_final = page_name.lower().replace(" ", "_")

    dir_path = Path(os.getenv("OUTPUT_FOLDER") or ".")

    pattern = f"{page_name_final}*.log"
    log_files = list(dir_path.glob(pattern))
    if not log_files:
        return "Log not found"

    latest_file = max(log_files, key=lambda f: f.stat().st_mtime)

    with open(latest_file, "r", encoding="utf-8") as f:
        content = f.read()
    return content


@app.post("/create_mediawiki_page/")
async def create_mediawiki_page(
    file: UploadFile = File(...),
    page_name: str = Form(...),
):
    """
    Endpoint to create a Mediawiki page

    Args:
        file: TXT file with wikitext data
        page_name: Page reference name

    Generate:
        Log file and wikipage file

    Env:
        MEDIAWIKI_URL: Url of Mediawiki to generate images and page
        MEDIAWIKI_USER: User for Mediawiki connexion
        MEDIAWIKI_MDP: Password for Mediawiki connexion
        OUTPUT_FOLDER: Output folder for log and Mediawiki page file

    Returns:
        page_url
    """
    if not page_name:
        raise HTTPException(status_code=400, detail="page_name must be fill")

    page_name_final = page_name.lower().replace(" ", "_")
    return_page_url = ""

    init_logger(
        f"{page_name_final}_create_mediawiki_page",
        os.getenv("OUTPUT_FOLDER") or "./output",
    )

    log_step("Get file content")
    content = await file.read()
    text_content = content.decode("utf-8")

    log_step("Create Mediawiki page")
    mediawiki_api = MediaWikiApi()
    if not mediawiki_api.login():
        log("Cant connect to mediawiki")
    else:
        return_page_url = mediawiki_api.create_page(page_name_final, text_content)

    return return_page_url
