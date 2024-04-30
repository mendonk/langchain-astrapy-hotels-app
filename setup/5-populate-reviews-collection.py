import datetime
import os

import astrapy
import pandas as pd

from common_constants import REVIEWS_COLLECTION_NAME
from setup.setup_constants import HOTEL_REVIEW_FILE_NAME, INSERT_MANY_CONCURRENCY
from utils.db import get_database
from utils.reviews import choose_featured

this_dir = os.path.abspath(os.path.dirname(__file__))
database = get_database()


def create_reviews_collection() -> astrapy.Collection:
    coll: astrapy.Collection = database.create_collection(
        REVIEWS_COLLECTION_NAME,
        indexing={"allow": ["_id", "hotel_id", "date_added", "featured"]},
    )
    return coll


def parse_date(date_str: str) -> datetime.datetime:
    trunc_date = date_str[: date_str.find("T")]
    return datetime.datetime.strptime(trunc_date, "%Y-%m-%d")


def populate_reviews_collection_from_csv(rev_col: astrapy.Collection) -> None:
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
            "date_added": parse_date(row["date_added"]),
            "id": row["id"],
            "title": row["title"],
            "body": row["body"],
            "rating": row["rating"],
            "featured": choose_featured(row["upvotes"]),
        }
        for _, row in review_df.iterrows()
    )

    insert_result = rev_col.insert_many(
        docs_to_insert,
        ordered=False,
        concurrency=INSERT_MANY_CONCURRENCY,
    )

    print(
        f"[5-populate-reviews-collection.py] Inserted {len(insert_result.inserted_ids)} reviews"
    )


if __name__ == "__main__":
    rev_col = create_reviews_collection()
    populate_reviews_collection_from_csv(rev_col)
