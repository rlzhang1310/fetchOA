# Fetch OA 
written in Python with Dockerized Flask 

## Build & Run Docker

build:

    docker build -t fetch-oa .
   
run:

    docker run -p 5000:5000 fetch-oa

The application will be accessible at http://localhost:5000.

## Testing
   
to run locally:

    pip install -r requirements.txt

    python -m unittest test.py

to run on docker:

    docker run fetch-oa python -m unittest test.py
