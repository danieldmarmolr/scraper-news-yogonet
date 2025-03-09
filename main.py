from fastapi import FastAPI

import sys; sys.path.append('.')
from pipeline import main
app = FastAPI()


@app.get("/")
def read_root():
    main()
    return 'OK'