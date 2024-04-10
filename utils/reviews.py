"""Utilities to manipulate reviews"""

from typing import List, Optional

import random
import uuid
import datetime

import langchain_core
from langchain_astradb.vectorstores import AstraDBVectorStore

import astrapy

from common_constants import (
    FEATURED_VOTE_THRESHOLD,
    MAX_NUM_REVIEWS_TO_COUNT,
    REVIEWS_COLLECTION_NAME,
    REVIEW_VECTOR_COLLECTION_NAME,
)
from utils.models import HotelReview, CappedCounter
from utils.ai import get_embeddings
from utils.db import get_astra_credentials, get_collection

# LangChain VectorStore abstraction to interact with the vector database
review_vectorstore = None


def get_review_vectorstore(
    embeddings: langchain_core.embeddings.Embeddings,
    api_endpoint: str,
    token: str,
    namespace: Optional[str],
) -> AstraDBVectorStore:
    global review_vectorstore
    if review_vectorstore is None:
        review_vectorstore = AstraDBVectorStore(
            embedding=embeddings,
            collection_name=REVIEW_VECTOR_COLLECTION_NAME,
            api_endpoint=api_endpoint,
            token=token,
            namespace=namespace,
        )
    return review_vectorstore


# ### SELECTING REVIEWS


# Entry point to select reviews for the general (base) hotel summary
def select_general_hotel_reviews(hotel_id: str) -> List[HotelReview]:
    review_col = get_collection(REVIEWS_COLLECTION_NAME)

    review_dict = {}

    _recent_review_docs = review_col.find(
        filter={
            "hotel_id": hotel_id,
        },
        sort={
            "date_added": -1,
        },
        projection={
            "_id": 1,
            "title": 1,
            "body": 1,
            "rating": 1,
            "date_added": 1,
        },
        limit=3,
    )
    recent_review_docs = list(_recent_review_docs)

    for recent_review_doc in recent_review_docs:
        review_dict[recent_review_doc["_id"]] = HotelReview(
            id=recent_review_doc["_id"],
            title=recent_review_doc["title"],
            body=recent_review_doc["body"],
            rating=recent_review_doc["rating"],
        )

    _featured_review_docs = review_col.find(
        filter={
            "hotel_id": hotel_id,
            "featured": 1,
        },
        sort={
            "date_added": -1,
        },
        projection={
            "_id": 1,
            "title": 1,
            "body": 1,
            "rating": 1,
            "date_added": 1,
        },
        limit=3,
    )
    featured_review_docs = list(_featured_review_docs)

    for featured_review_doc in featured_review_docs:
        review_dict[featured_review_doc["_id"]] = HotelReview(
            id=featured_review_doc["_id"],
            title=featured_review_doc["title"],
            body=featured_review_doc["body"],
            rating=featured_review_doc["rating"],
        )

    return list(review_dict.values())


def select_hotel_reviews_for_user(
    hotel_id: str, user_travel_profile_summary: str
) -> List[HotelReview]:
    astra_credentials = get_astra_credentials()
    review_store = get_review_vectorstore(
        embeddings=get_embeddings(),
        token=astra_credentials.token,
        api_endpoint=astra_credentials.api_endpoint,
        namespace=astra_credentials.namespace,
    )

    review_data = review_store.similarity_search_with_score_id(
        query=user_travel_profile_summary,
        k=3,
        filter={"hotel_id": hotel_id},
    )

    reviews = [
        HotelReview(
            title=review_doc.metadata["title"].strip(),
            body=extract_review_body_from_doc_text(
                review_doc.page_content, review_doc.metadata["title"]
            ),
            rating=int(review_doc.metadata["rating"]),
            id=review_id,
        )
        for review_doc, _, review_id in review_data
    ]

    return reviews


def select_review_count_by_hotel(hotel_id: str) -> CappedCounter:
    review_col = get_collection(REVIEWS_COLLECTION_NAME)

    try:
        num_reviews = review_col.count_documents(
            filter={
                "hotel_id": hotel_id,
            },
            upper_bound=MAX_NUM_REVIEWS_TO_COUNT,
        )
        count = CappedCounter(count=num_reviews)
    except astrapy.exceptions.TooManyDocumentsToCountException:
        count = CappedCounter(
            count=MAX_NUM_REVIEWS_TO_COUNT,
            at_ceiling=True,
        )
    return count


# Extracts the review body from the text found in the document,
# cutting out the title and colon and removing any leading / trailing spaces from title and body
def extract_review_body_from_doc_text(review_doc_text: str, review_title: str) -> str:
    end_title_index = len(review_title.strip()) + 1
    return review_doc_text[end_title_index:].strip()


# ### ADDING REVIEWS


# Entry point for when we want to add a review
# - Generates an id for the new review
# - Stores the review in the non-vectorised collection
# - Embeds the review and then stores it in the vectorised collection
def insert_review_for_hotel(
    hotel_id: str, review_title: str, review_body: str, review_rating: int
) -> None:
    review_id = generate_review_id()
    insert_into_reviews_collection(
        hotel_id, review_id, review_title, review_body, review_rating
    )
    insert_into_review_vector_collection(
        hotel_id, review_id, review_title, review_body, review_rating
    )


def generate_review_id() -> str:
    return uuid.uuid4().hex


def format_review_content_for_embedding(title: str, body: str) -> str:
    return f"{title}: {body}"


def choose_featured(num_upvotes: int) -> int:
    if num_upvotes > FEATURED_VOTE_THRESHOLD:
        return 1
    else:
        return 0


# Inserts a new review into the non-vectorised reviews collection
def insert_into_reviews_collection(
    hotel_id: str,
    review_id: str,
    review_title: str,
    review_body: str,
    review_rating: int,
) -> None:
    review_col = get_collection(REVIEWS_COLLECTION_NAME)

    date_added = datetime.datetime.now()
    featured = choose_featured(random.randint(1, 21))

    review_col.insert_one(
        {
            "_id": review_id,
            "hotel_id": hotel_id,
            "date_added": date_added,
            "title": review_title,
            "body": review_body,
            "rating": review_rating,
            "featured": featured,
        }
    )


# Inserts a new review into the vectorised reviews collection,
# using a VectorStore of type AstraDB from LangChain
# (class imported as 'LCAstraDB' to avoid collision with AstraPy's class)
def insert_into_review_vector_collection(
    hotel_id: str,
    review_id: str,
    review_title: str,
    review_body: str,
    review_rating: int,
) -> None:
    astra_credentials = get_astra_credentials()
    review_store = get_review_vectorstore(
        embeddings=get_embeddings(),
        token=astra_credentials.token,
        api_endpoint=astra_credentials.api_endpoint,
        namespace=astra_credentials.namespace,
    )

    review_metadata = {
        "hotel_id": hotel_id,
        "rating": review_rating,
        "title": review_title,
    }

    review_store.add_texts(
        texts=[format_review_content_for_embedding(review_title, review_body)],
        metadatas=[review_metadata],
        ids=[review_id],
    )
