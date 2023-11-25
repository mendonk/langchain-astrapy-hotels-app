import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import datetime

from common_constants import REVIEWS_COLLECTION_NAME
from setup.setup_constants import HOTEL_REVIEW_FILE_NAME, INSERTION_BATCH_SIZE, INSERTION_BATCH_CONCURRENCY
from utils.reviews import choose_featured
from utils.db import get_astra_db_client
from utils.batching import batch_iterable
from utils.dates import dt_to_int


this_dir = os.path.abspath(os.path.dirname(__file__))
astra_db_client = get_astra_db_client()


def create_reviews_collection():
    return astra_db_client.create_collection(
        REVIEWS_COLLECTION_NAME,
        dimension=1,
        metric="dot_product",
    )


def parse_date(date_str) -> datetime.datetime:
    trunc_date = date_str[: date_str.find("T")]
    return datetime.datetime.strptime(trunc_date, "%Y-%m-%d")


def populate_reviews_collection_from_csv(rev_col):
    hotel_review_file_path = os.path.join(this_dir, HOTEL_REVIEW_FILE_NAME)
    hotel_review_data = pd.read_csv(hotel_review_file_path)

    chosen_columns = pd.DataFrame(
        hotel_review_data,
        columns=["hotel_id", "date", "id", "title", "text", "rating", "review_upvotes"],
    )
    review_df = chosen_columns.rename(
        columns={
            # "hotel_id": "hotel_id",
            "date": "date_added",
            # "id": "id",
            # "title": "title",
            "text": "body",
            # "rating": "rating",
            "review_upvotes": "upvotes",
        }
    )
    review_df["title"] = review_df["title"].fillna("Review")
    review_df["body"] = review_df["body"].fillna("(empty review)")
    review_df["rating"] = review_df["rating"].fillna(5)

    # Caution: datetimes are at play here
    docs_to_insert = (
        {
            # it so happens that the review ID is globally unique
            "_id": row["id"],
            # the data:
            "hotel_id": row["hotel_id"],
            "date_added_int": dt_to_int(parse_date(row["date_added"])),
            "$vector": [dt_to_int(parse_date(row["date_added"]))],
            "id": row["id"],
            "title": row["title"],
            "body": row["body"],
            "rating": row["rating"],
            "featured": choose_featured(row["upvotes"]),
        }
        for _, row in review_df.iterrows()
    )

    with ThreadPoolExecutor(max_workers=INSERTION_BATCH_CONCURRENCY) as tpe:
        _ = list(
            tpe.map(
                rev_col.insert_many,
                (
                    list(batch)
                    for batch in batch_iterable(docs_to_insert, INSERTION_BATCH_SIZE)
                ),
            )
        )

    print(f"[5-populate-reviews-collection.py] Inserted {len(review_df)} reviews")


if __name__ == "__main__":
    rev_col = create_reviews_collection()
    populate_reviews_collection_from_csv(rev_col)
