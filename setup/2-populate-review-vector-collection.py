import os
import json
import argparse
import pandas as pd
from typing import Dict, List

from setup.embedding_dump import deflate_embeddings_map
from setup.setup_constants import EMBEDDING_FILE_NAME, HOTEL_REVIEW_FILE_NAME

from utils.db import get_astra_credentials
from utils.ai import EMBEDDING_DIMENSION
from utils.reviews import format_review_content_for_embedding, get_review_vectorstore


# We create an ad-hoc "Embeddings" class, sitting on the precalculated embeddings,
# to perform all these insertions idiomatically through the LangChain
# abstraction. This is to avoid having to work at the astrapy level
# while still taking advantage of the stored json with precalculated vectors.
from langchain_core.embeddings import Embeddings


class JustPreCalculatedEmbeddings(Embeddings):
    def __init__(self, precalc_dict: Dict[str, List[float]]) -> None:
        self.precalc_dict = precalc_dict

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(txt) for txt in texts]

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        if text in self.precalc_dict:
            return self.precalc_dict[text]
        else:
            # this happens from LangChain when creating the store:
            print(
                f"** [JustPreCalculatedEmbeddings] INFO: embed request for '{text}'. Returning moot results"
            )
            return [0.0] * EMBEDDING_DIMENSION

    async def aembed_query(self, text: str) -> List[float]:
        return self.embed_query(text)


this_dir = os.path.abspath(os.path.dirname(__file__))
DEFAULT_CONCURRENT_BATCHES = 50


if __name__ == "__main__":
    astra_credentials = get_astra_credentials()

    parser = argparse.ArgumentParser(
        description="Store reviews with embeddings to Astra DB vector collection"
    )
    parser.add_argument(
        "-c",
        metavar="CONCURRENT_BATCHES",
        type=int,
        help="Number of insertion batches running at once",
        default=DEFAULT_CONCURRENT_BATCHES,
    )
    args = parser.parse_args()

    embedding_file_path = os.path.join(this_dir, EMBEDDING_FILE_NAME)
    if os.path.isfile(embedding_file_path):
        # review_id -> vector, which was stored in a compressed format to shrink file size
        enrichment = deflate_embeddings_map(json.load(open(embedding_file_path)))
    else:
        enrichment = {}

    hotel_review_file_path = os.path.join(this_dir, HOTEL_REVIEW_FILE_NAME)
    hotel_review_data = pd.read_csv(hotel_review_file_path)

    # sadly the precalc map for this "embeddings" must be sentence -> vector,
    # so we need a 'join' (which amounts to a preprocess pass through the hotel reviews dataframe)
    precalc_text_to_vector_map = {
        format_review_content_for_embedding(
            title=row["title"], body=row["text"]
        ): enrichment[row["id"]]
        for _, row in hotel_review_data.iterrows()
        if row["id"] in enrichment
    }
    c_embeddings = JustPreCalculatedEmbeddings(precalc_dict=precalc_text_to_vector_map)

    review_vectorstore = get_review_vectorstore(
        embeddings=c_embeddings,
        api_endpoint=astra_credentials["api_endpoint"],
        token=astra_credentials["token"],
        namespace=astra_credentials["namespace"],
    )

    eligibles = [
        {
            "text": format_review_content_for_embedding(
                title=row["title"], body=row["text"]
            ),
            "metadata": {
                "hotel_id": row["hotel_id"],
                "rating": row["rating"],
                "title": row["title"],
            },
            "id": row["id"],
        }
        for _, row in hotel_review_data.iterrows()
        if row["id"] in enrichment
    ]

    texts, metadatas, ids = zip(
        *[(itm["text"], itm["metadata"], itm["id"]) for itm in eligibles]
    )

    inserted_ids = review_vectorstore.add_texts(
        texts=texts,
        metadatas=metadatas,
        ids=ids,
        batch_concurrency=args.c,
    )

    print(
        f"\n[2-populate-review-vector-collection.py] Finished. {len(inserted_ids)} rows written."
    )
