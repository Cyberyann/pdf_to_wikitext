from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import Response
from md_to_wikitext import md_to_wikitext
import pymupdf4llm
import tempfile
import os
import shutil

app = FastAPI(title="PDF Text Extractor API")


@app.post("/pdf-to-wikitext/")
async def extract_text_from_pdf(
    file: UploadFile = File(...),
    footer: str = Form(...),
    ignore_pages: str = Form(...),
    article_name: str = Form(...),
):
    """
    Endpoint to transform a pdf file in a wikitext

    Args:
        file: PDF file
        footer: Reference footer
        ignore_pages: ignore pages number separate by ,
        article_name: Article reference name

    Returns:
        wikitext from PDF text
    """

    if not article_name:
        raise HTTPException(status_code=400, detail="article_name must be fill")

    image_path = f"./images/{file.filename[:-4]}/"

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    # Transform Pdf content to md text and store image
    try:
        md_text = pymupdf4llm.to_markdown(
            temp_file, write_images=True, image_path=image_path
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in PDF to MD transformation: {str(e)}"
        )

    # Remove temporary file
    os.unlink(temp_file_path)

    # Transform MD to wikitext
    try:
        wikitext = md_to_wikitext(
            md_text, footer, ignore_pages, article_name, image_path
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in MD to WIKITEXT transformation: {str(e)}"
        )

    # Supprimer un répertoire et tout son contenu
    shutil.rmtree(image_path)

    # Return wikitext
    return Response(content=wikitext, media_type="text/plain")
