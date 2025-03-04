import markdown
import re
from functools import lru_cache
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.gzip import GZipMiddleware
from pathlib import Path
from os import listdir, path
import time
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor

# Constants
BLOGS_DIR = Path("blog")
IGNORED_FILES = ["about.md"]
CACHE_DURATION = 60 * 60 * 5
MAX_WORKERS = 2

# Initialize FastAPI
app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=500)
app.mount("/static", StaticFiles(directory="static", check_dir=True), name="static")
templates = Jinja2Templates(directory="templates")

# Create thread pool for CPU-bound tasks
thread_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Cache structures
blog_content_cache = {}
blog_list_cache = {"content": None, "timestamp": 0}
blog_page_cache = {}
about_page_cache = {"content": None, "timestamp": 0}

# File modification tracking
file_mtimes = {}


def is_cache_valid(cache_entry):
    """Check if a cache entry is still valid"""
    return cache_entry and time.time() - cache_entry["timestamp"] < CACHE_DURATION


def parse_markdown(content, extensions=None):
    """Parse markdown content in a separate thread to avoid blocking"""
    if extensions is None:
        extensions = ["fenced_code", "nl2br", "meta"]
    md = markdown.Markdown(extensions=extensions)
    html = md.convert(content)
    meta = getattr(md, 'Meta', {}) if hasattr(md, 'Meta') else {}
    return html, meta


async def get_blog_content(file_name: str, force_refresh=False):
    """Get blog content with caching"""
    file_path = BLOGS_DIR / file_name

    if not file_path.exists():
        return None

    mtime = path.getmtime(file_path)

    if not force_refresh and file_name in blog_content_cache:
        cache_entry = blog_content_cache[file_name]
        if cache_entry["mtime"] == mtime:
            return cache_entry["data"]

    try:
        # Read file asynchronously
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            markdown_content = await f.read()

        # Process markdown in thread pool to avoid blocking the event loop
        html_content, meta = await asyncio.get_event_loop().run_in_executor(
            thread_pool, parse_markdown, markdown_content
        )

        # Create excerpt
        excerpt = html_content[:300]
        if len(html_content) > 300:
            last_space = excerpt.rfind(" ")
            if last_space != -1:
                excerpt = excerpt[:last_space] + "..."
            else:
                excerpt += "..."

        # Remove headings from excerpt
        excerpt = re.sub(r"<h[1-6]>.*?</h[1-6]>", "", excerpt, flags=re.DOTALL)

        # Prepare result
        result = {
            "excerpt": excerpt,
            "metadata": meta,
            "path": file_name[:-3],
            "html_content": html_content,  # Store full HTML for reuse
        }

        # Update cache
        blog_content_cache[file_name] = {
            "data": result,
            "mtime": mtime,
            "timestamp": time.time()
        }

        return result
    except Exception as e:
        print(f"Error processing {file_name}: {e}")
        return None


async def get_all_blogs(force_refresh=False):
    """Get all blog posts with caching"""
    current_time = time.time()

    # Check if we need to refresh the cache
    refresh_needed = force_refresh or not is_cache_valid(blog_list_cache)

    if not refresh_needed:
        # Check if any files have been modified
        for file_path in listdir(BLOGS_DIR):
            full_path = path.join(BLOGS_DIR, file_path)
            if path.isfile(full_path) and file_path not in IGNORED_FILES:
                mtime = path.getmtime(full_path)
                if file_path not in file_mtimes or file_mtimes[file_path] != mtime:
                    refresh_needed = True
                    break

    if refresh_needed:
        # Get list of blog files
        blog_files = [
            file_path for file_path in listdir(BLOGS_DIR)
            if path.isfile(path.join(BLOGS_DIR, file_path)) and file_path not in IGNORED_FILES
        ]

        # Process all blogs concurrently
        tasks = [get_blog_content(file_name) for file_name in blog_files]
        results = await asyncio.gather(*tasks)

        # Filter out None results and update cache
        content = [result for result in results if result]
        blog_list_cache["content"] = content
        blog_list_cache["timestamp"] = current_time

        # Update file modification times
        for file_path in blog_files:
            file_mtimes[file_path] = path.getmtime(path.join(BLOGS_DIR, file_path))

    return blog_list_cache["content"]


@app.on_event("startup")
async def startup_event():
    """Preload blog content on startup"""
    await get_all_blogs(force_refresh=True)
    await about_page(None, preload=True)


@app.get("/blog", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
async def blog_list(request: Request):
    """Serve blog list page"""
    posts = await get_all_blogs()

    response = templates.TemplateResponse(
        "blog.html",
        {
            "request": request,
            "posts": posts,
        },
    )

    # Add cache control headers
    response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes browser caching

    return response


@app.get("/blog/{filename}", response_class=HTMLResponse)
async def get_blog(request: Request, filename: str):
    """Serve individual blog page"""
    cache_key = f"blog_{filename}"

    # Check cache
    if cache_key in blog_page_cache and is_cache_valid(blog_page_cache[cache_key]):
        cached_response = blog_page_cache[cache_key]["data"]
        # Replace request in cached template
        cached_response.context["request"] = request
        return cached_response

    try:
        # Get blog content
        blog_data = await get_blog_content(f"{filename}.md")

        if blog_data:
            html_content = blog_data["html_content"]
            meta = blog_data["metadata"]
            title = meta.get("title", ["TITLE"])[0] if isinstance(meta.get("title", ["TITLE"]), list) else meta.get("title", "TITLE")
        else:
            html_content = "<p>No blog content found</p>"
            title = "No blog found"

        # Create response
        response = templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "content": html_content,
                "title": title,
            },
        )

        response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour browser caching

        blog_page_cache[cache_key] = {
            "data": response,
            "timestamp": time.time()
        }

        return response
    except Exception as e:
        print(f"Failed in parsing markdown content: {e}")
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "content": "<p>No blog content found</p>", "title": "No blog found"},
        )


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request, preload=False):
    """Serve about page"""
    # For preloading during startup
    if preload:
        markdown_file = BLOGS_DIR / "about.md"
        if markdown_file.exists():
            mtime = path.getmtime(markdown_file)
            async with aiofiles.open(markdown_file, "r", encoding="utf-8") as f:
                markdown_content = await f.read()

            html_content, _ = await asyncio.get_event_loop().run_in_executor(
                thread_pool, parse_markdown, markdown_content
            )

            about_page_cache["content"] = html_content
            about_page_cache["timestamp"] = time.time()
            about_page_cache["mtime"] = mtime
        return None

    # Check if we need to refresh the cache
    refresh_needed = True
    markdown_file = BLOGS_DIR / "about.md"

    if is_cache_valid(about_page_cache) and markdown_file.exists():
        mtime = path.getmtime(markdown_file)
        if mtime == about_page_cache.get("mtime", 0):
            refresh_needed = False

    if refresh_needed and markdown_file.exists():
        mtime = path.getmtime(markdown_file)
        async with aiofiles.open(markdown_file, "r", encoding="utf-8") as f:
            markdown_content = await f.read()

        html_content, _ = await asyncio.get_event_loop().run_in_executor(
            thread_pool, parse_markdown, markdown_content
            )

        about_page_cache["content"] = html_content
        about_page_cache["timestamp"] = time.time()
        about_page_cache["mtime"] = mtime

    html_content = about_page_cache.get("content", "<p>No content found.</p>")

    response = templates.TemplateResponse(
        "about.html", {"request": request, "content": html_content}
    )

    # Add cache control headers
    response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour browser caching

    return response


# Serve favicon directly
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('static/favicon.ico')

