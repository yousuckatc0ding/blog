from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import markdown
from pathlib import Path

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Path to the blogs directory
BLOGS_DIR = Path("blog")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    markdown_file = BLOGS_DIR / "hello.md"

    if markdown_file.exists():
        with open(markdown_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()
        html_content = markdown.markdown(markdown_content, extensions=["fenced_code", "nl2br"])
    else:
        html_content = "<p>No blog content found.</p>"

    # Pass the rendered HTML to the template
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "content": html_content,  # Inject the HTML content
            "title": "Hello!"
        },
    )

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    markdown_file = BLOGS_DIR / "about.md"
    if markdown_file.exists():
        with open(markdown_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()
        html_content = markdown.markdown(markdown_content, extensions=["fenced_code", "nl2br"])
    else:
        html_content = "<p>No blog content found.</p>"
    return templates.TemplateResponse(
        "about.html",
            {
                "request": request,
                "content": html_content
            }
        )
