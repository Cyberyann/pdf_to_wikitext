from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import Response
from md_to_wikitext import md_to_wikitext
from logger import init_logger, log, log_step
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
):
    """
    Endpoint to transform a pdf file in a wikitext and generate a wikimedia page

    Args:
        file: PDF file
        footer: Reference footer
        ignore_pages: ignore pages number separate by ,
        page_name: Page reference name

    Generate:
        Log file and wikipage file

    Env:
        MEDIAWIKI_URL: Url of wikimedia to generate images and page
        MEDIAWIKI_USER: User for wikimedia connexion
        MEDIAWIKI_MDP: Password for wikimedia connexion
        OUTPUT_FOLDER: Output folder for log and wikimedia page file

    Returns:
        Nothing
    """
    if not page_name:
        raise HTTPException(status_code=400, detail="page_name must be fill")

    init_logger(page_name, os.getenv("OUTPUT_FOLDER") or "./output")

    log_step("Init application")
    output_filename = f"{os.getenv("OUTPUT_FOLDER")}/{page_name}.txt"
    if os.path.exists(output_filename):
        os.unlink(output_filename)
    image_path = f"./images/{file.filename[:-4]}/"  # type: ignore

    log_step("Create temporary file")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    log_step("Transform Pdf content to md text and store image")
    try:
        md_text = pymupdf4llm.to_markdown(
            temp_file, write_images=True, image_path=image_path
        )
    except Exception as e:
        log(f"Error in PDF to MD transformation: {str(e)}")
        return

    log_step("Remove temporary file")
    os.unlink(temp_file_path)

    log_step("Transform MD to wikitext and create image on wikimedia")
    try:
        wikitext = md_to_wikitext(md_text, footer, ignore_pages, page_name, image_path)
    except Exception as e:
        log(f"Error in MD to WIKITEXT transformation: {str(e)}")
        return

    log_step("Remove image folder")
    shutil.rmtree(image_path)

    log_step("Create wikitext file")
    with open(output_filename, "w", encoding="utf-8") as fichier:
        fichier.write(wikitext)

    # Next steps
