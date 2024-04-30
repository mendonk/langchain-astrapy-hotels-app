import os

import langchain_core
from dotenv import find_dotenv, load_dotenv
from langchain.globals import set_llm_cache
from langchain_astradb.cache import AstraDBCache
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai.llms import OpenAI

from utils.db import get_astra_credentials

LLM_PROVIDER = "OpenAI"

dotenv_file = find_dotenv(".env")
load_dotenv(dotenv_file)

EMBEDDING_DIMENSION = 1536

llm = None
embeddings = None


def get_llm() -> langchain_core.language_models.llms.BaseLLM:
    global llm
    if llm is None:
        llm = OpenAI()
    #
    return llm


def get_embeddings() -> langchain_core.embeddings.Embeddings:
    global embeddings
    if embeddings is None:
        embeddings = OpenAIEmbeddings()
    #
    return embeddings


def enable_llm_cache() -> None:
    astra_credentials = get_astra_credentials()
    set_llm_cache(
        AstraDBCache(
            api_endpoint=astra_credentials.api_endpoint,
            token=astra_credentials.token,
            namespace=astra_credentials.namespace,
        )
    )
