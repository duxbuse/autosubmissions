# autosubmissions

way to easily generate submissions

run local dev

```sh
docker build -f Dockerfile.dev -t dev .
docker run -it --rm -p 8000:8000 -p 5173:5173 -v backend:/app/backend -v /app/backend/.venv -v frontend:/app/frontend -v /app/frontend/node_modules dev
```


build prod container

```sh
docker build -t prod .
```

run prod container

```sh
docker run --rm -it -p 8080:8000 prod
```