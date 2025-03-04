import markdown
import re
from cachetools import TTLCache, cached
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.gzip import GZipMiddleware
from pathlib import Path
from os import listdir, path
from datetime import datetime, timedelta
ignored_files = ["about.md"]

app = FastAPI()

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

cache = TTLCache(maxsize=10, ttl=timedelta(hours=12), timer=datetime.now)


# Path to the blogs directory
BLOGS_DIR = Path("blog")

@cached(cache=cache)
def get_blog_content(file_name: str):
    file_path = BLOGS_DIR / file_name
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()
        md = markdown.Markdown(extensions=["fenced_code", "nl2br", "meta"])
        content = md.convert(markdown_content)
        excerpt = content[:300]

        if len(content) > 300:
            last_space = excerpt.rfind(" ")
            if last_space != -1:
                excerpt = excerpt[:last_space] + "..."
            else:
                excerpt += "..."

        excerpt = re.sub(r"<h[1-6]>.*?</h[1-6]>", "", excerpt, flags=re.DOTALL)
        metadata = md.Meta
        return {
            "excerpt": excerpt,
            "metadata": metadata,
            "path": file_name[:-3],
        }
    except Exception as e:
        print(f"Error in parsing {e}")


@app.get("/blog", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
@cached(cache=cache)
def blog_list(request: Request):
    content = []
    for file_path in listdir(BLOGS_DIR):
        if path.isfile(path.join(BLOGS_DIR, file_path)):
            if file_path not in ignored_files:
                content.append(get_blog_content(file_path))

    return templates.TemplateResponse(
        "blog.html",
        {
            "request": request,
            "posts": content,
        },
    )


@app.get("/blog/{filename}", response_class=HTMLResponse)
@cached(cache=cache)
def get_blog(request: Request, filename: str):
    try:
        filename = filename + ".md"
        file_path = BLOGS_DIR / filename
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()
            md = markdown.Markdown(extensions=["meta", "fenced_code", "nl2br"])
            html_content = md.convert(markdown_content)
            meta = md.Meta

        else:
            html_content = "<p>No blog content found</p>"

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "content": html_content,
                "title": meta.get("title", "TITLE"),
            },
        )
    except Exception as e:
        print("failed in parsing markdown content: ", e)
        html_content = "<p>No blog content found</p>"
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "content": html_content, "title": "No blog found"},
        )


@app.get("/about", response_class=HTMLResponse)
@cached(cache=cache)
async def about_page(request: Request):
    markdown_file = BLOGS_DIR / "about.md"
    if markdown_file.exists():
        with open(markdown_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()
        html_content = markdown.markdown(
            markdown_content, extensions=["fenced_code", "nl2br"]
        )
    else:
        html_content = "<p>No blog content found.</p>"
    return templates.TemplateResponse(
        "about.html", {"request": request, "content": html_content}
    )
