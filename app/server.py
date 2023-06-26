import logging
import warnings
import traceback
import os

from fastapi import Body, Depends, HTTPException, BackgroundTasks, Request, status
from fastapi.openapi.docs import (
    get_swagger_ui_html,
)
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import httpx
from starlette.middleware.cors import CORSMiddleware
from uuid import uuid4

from reasoner_pydantic import (
    AsyncQuery,
    AsyncQueryResponse,
    Response,
    Query
)

from .trapi import TRAPI
from .ordering_components import get_ordering_components

LOGGER = logging.getLogger(__name__)

openapi_args = dict(
    title="Answer Appraiser",
    version="0.1.0",
    terms_of_service="",
    translator_component="Utility",
    translator_teams=["Standards Reference Implementation Team"],
    infores="infores:answer-appraiser",
    contact={
        "name": "Abrar Mesbah",
        "email": "amesbah@covar.com",
        "x-id": "uhbrar",
        "x-role": "responsible developer",
    },
)

OPENAPI_SERVER_URL = os.getenv("OPENAPI_SERVER_URL")
OPENAPI_SERVER_MATURITY = os.getenv("OPENAPI_SERVER_MATURITY", "development")
OPENAPI_SERVER_LOCATION = os.getenv("OPENAPI_SERVER_LOCATION", "RENCI")
TRAPI_VERSION = os.getenv("TRAPI_VERSION", "1.4.0")

if OPENAPI_SERVER_URL:
    openapi_args["servers"] = [
        {
            "url": OPENAPI_SERVER_URL,
            "x-maturity": OPENAPI_SERVER_MATURITY,
            "x-location": OPENAPI_SERVER_LOCATION,
        },
    ]

openapi_args["trapi"] = TRAPI_VERSION

APP = TRAPI(**openapi_args)

APP.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AEXAMPLE = {
    "callback": "https://test",
    "message": {
        "query_graph": {
            "nodes": {
                "n0": {"ids": ["MONDO:0005148"], "categories": ["biolink:Disease"]},
                "n1": {"categories": ["biolink:PhenotypicFeature"]},
            },
            "edges": {
                "e01": {
                    "subject": "n0",
                    "object": "n1",
                    "predicates": ["biolink:has_phenotype"],
                }
            },
        }
    },
}

EXAMPLE = {
    "callback": "https://test",
    "message": {
        "query_graph": {
            "nodes": {
                "n0": {"ids": ["MONDO:0005148"], "categories": ["biolink:Disease"]},
                "n1": {"categories": ["biolink:PhenotypicFeature"]},
            },
            "edges": {
                "e01": {
                    "subject": "n0",
                    "object": "n1",
                    "predicates": ["biolink:has_phenotype"],
                }
            },
        }
    },
}

@APP.post("/get_appraisal", response_model=AsyncQueryResponse)
async def get_appraisal(
    background_tasks: BackgroundTasks,
    query: AsyncQuery = Body(..., example=AEXAMPLE)
):
    """Appraise Answers"""
    query_dict = query.dict()
    log_level = query_dict.get("log_level") or "INFO"
    LOGGER.setLevel(logging._nameToLevel[log_level])
    message = query_dict["message"]
    qid = str(uuid4())[:8]
    if not message.get("results"):
        return JSONResponse(content={"status": "Rejected",
                                     "description": "No Results.",
                                     "job_id": qid}, status_code=200)
    callback = query_dict["callback"]
    background_tasks.add_task(appraise, qid, message, callback)
    return JSONResponse(content={"status": "Accepted",
                                 "description": f"Appraising answers. Will send response to {callback}",
                                 "job_id": qid}, status_code=200)

@APP.post("/sync_get_appraisal", response_model=Response)
async def sync_get_appraisal(
    query: Query = Body(..., example=EXAMPLE)
):
    query_dict = query.dict()
    log_level = query_dict.get("log_level") or "INFO"
    LOGGER.setLevel(logging._nameToLevel[log_level])
    message = query_dict["message"]
    qid = str(uuid4())[:8]
    if not message.get("results"):
        return JSONResponse(content={"status": "Rejected",
                                     "description": "No Results.",
                                     "job_id": qid}, status_code=200)
    try:
        get_ordering_components(message)
    except Exception as e:
        LOGGER.error(f"Something went wrong while appraising {qid}")
    return Response(message=message, logs=LOGGER.handlers[0].store)


async def appraise(qid, message, callback):
    try:
        get_ordering_components(message)
    except Exception as e:
        LOGGER.error(f"Something went wrong while appraising {qid}")
    try:    
        LOGGER.info(f"[{qid}] Posting to callback {callback}")
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=600.0)) as client:
            res = await client.post(callback, json=message)
            LOGGER.info(f"[{qid}] Posted to {callback} with code {res.status_code}")
    except Exception as e:
        LOGGER.error(f"Unable to post to callback {callback}.")