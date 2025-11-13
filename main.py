from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from pdf2image import convert_from_bytes
from deep_translator import GoogleTranslator
from PIL import Image
import pytesseract
import os

# Настройки путей
os.environ["PATH"] += os.pathsep + r"E:\poppler-25.07.0\Library\bin"
pytesseract.pytesseract.tesseract_cmd = r"E:\tell\tesseract.exe"

# Снимаем лимит на размер изображений
Image.MAX_IMAGE_PIXELS = None

app = FastAPI()
translator = GoogleTranslator(source="auto", target="ru")


def split_image(image, chunk_height=3000):
    """Разбивает длинную страницу на части для OCR"""
    width, height = image.size
    chunks = []
    for top in range(0, height, chunk_height):
        bottom = min(top + chunk_height, height)
        chunk = image.crop((0, top, width, bottom))
        chunks.append(chunk)
    return chunks


@app.post("/translate_pdf", response_class=HTMLResponse)
async def translate_pdf(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        # ↓ Снижаем DPI чтобы избежать больших изображений
        images = convert_from_bytes(pdf_bytes, dpi=100)

        html_content = "<h1>Перевод PDF</h1>"

        for i, image in enumerate(images, start=1):
            text = ""

            # Разбиваем длинные страницы на куски
            chunks = split_image(image)
            for chunk in chunks:
                text += pytesseract.image_to_string(chunk, lang="eng+rus")

            # Переводим весь текст страницы
            translated = translator.translate(text)
            html_content += f"<h2>Страница {i}</h2><p>{translated}</p><hr>"

        return HTMLResponse(content=html_content)

    except Exception as e:
        return HTMLResponse(content=f"<h1>Ошибка</h1><p>{e}</p>")

