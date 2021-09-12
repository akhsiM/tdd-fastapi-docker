from fastapi import FastAPI, Depends
from app.config import get_settings, Settings

app = FastAPI()


# @app.get('/ping')
# def pong():
#     return {
#         'ping': 'pong!'
#     }


@app.get('/ping')
async def pong(settings: Settings=Depends(get_settings)):
    return {
        'ping': 'pong!',
        'environment': settings.environment,
        'testing': settings.testing
    }