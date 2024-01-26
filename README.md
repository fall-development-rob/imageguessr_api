The server will run on: http://localhost:8000

Swagger docs for the API can be found at: http://localhost:8000/docs

To start the python sever run:

``` 
pip3 install -r requirements.txt && python3 -m uvicorn api.index:app --reload

## TO DO:
- Move into a docker container
- Improve how the websockets are handled
