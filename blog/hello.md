Title: Dev Blog: Optimizing API Performance for Data-Intensive Applications
Date: February 1, 2025
# Dev Blog: Optimizing API Performance for Data-Intensive Applications


In today’s post, I want to walk you through the steps I took to optimize the performance of an API used to serve data-heavy charts for a React dashboard. Initially, the API’s response time was a bottleneck, especially when dealing with large datasets and complex aggregations. After a few iterations, I managed to reduce the response time by over 60%, and I’ll share the process and code snippets below.


## 1. Identifying the Bottleneck

The API was built with FastAPI and used a relational database as the backend. Here’s the initial version of one of the endpoints:


```python
@app.get("/data")
def get_data():
    data = db.execute("SELECT * FROM large_table WHERE condition = TRUE").fetchall()
    return {"data": data}
```

At first glance, the issue seemed to be the sheer size of the data being fetched. The table contained millions of rows, and the endpoint didn’t apply any filters or pagination.


## 2. Adding Pagination

The first optimization step was to introduce pagination. This allowed clients to request smaller chunks of data rather than loading the entire dataset at once.

```python
@app.get("/data")
def get_data(page: int = 1, page_size: int = 50):
    offset = (page - 1) * page_size
    query = f"SELECT * FROM large_table WHERE condition = TRUE LIMIT {page_size} OFFSET {offset}"
    data = db.execute(query).fetchall()
    return {"page": page, "page_size": page_size, "data": data}
```

This simple change drastically reduced the time required to fetch data while also lowering memory usage.


## 3. Implementing Caching

Even with pagination, some queries were being repeated multiple times. To address this, I implemented caching using `DiskCache`:

```python
from diskcache import Cache

cache = Cache("/tmp/my_cache")

@app.get("/data")
def get_data(page: int = 1, page_size: int = 50):
    cache_key = f"data-page-{page}-size-{page_size}"
    if cache_key in cache:
        return cache[cache_key]

    offset = (page - 1) * page_size
    query = f"SELECT * FROM large_table WHERE condition = TRUE LIMIT {page_size} OFFSET {offset}"
    data = db.execute(query).fetchall()

    cache[cache_key] = {"page": page, "page_size": page_size, "data": data}
    return cache[cache_key]
```

This reduced load times for frequently requested data significantly.


## 4. Leveraging Asynchronous Execution

Another issue was that the API was synchronous, leading to blocking behavior during database queries. I refactored the code to use asynchronous functions:

```python
from fastapi import FastAPI
from databases import Database

app = FastAPI()
database = Database("sqlite:///mydatabase.db")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/data")
async def get_data(page: int = 1, page_size: int = 50):
    offset = (page - 1) * page_size
    query = "SELECT * FROM large_table WHERE condition = TRUE LIMIT :limit OFFSET :offset"
    rows = await database.fetch_all(query=query, values={"limit": page_size, "offset": offset})
    return {"page": page, "page_size": page_size, "data": rows}
```


## 5. Optimizing Database Queries

The final step was to optimize the database queries themselves. Using indexed columns and only selecting necessary fields improved performance:

```sql
CREATE INDEX idx_condition ON large_table(condition);
```

And modifying the query:

```python
query = "SELECT id, name, value FROM large_table WHERE condition = TRUE LIMIT :limit OFFSET :offset"
```


## Final Results

After implementing these changes:

1. **Average Response Time**: Reduced from ~2.5 seconds to ~0.8 seconds.
2. **Server Load**: Reduced by approximately 40%.
3. **User Feedback**: The improved speed and pagination led to a much smoother user experience.


## Key Takeaways

- Always profile your application to identify bottlenecks.
- Introduce pagination for large datasets to avoid overwhelming the server and client.
- Implement caching for frequently accessed data.
- Asynchronous execution can significantly improve performance for I/O-bound tasks.
- Optimize database queries with indexes and by selecting only necessary fields.


That’s it for today’s post! If you’ve faced similar challenges or have additional tips, feel free to share them in the comments.

