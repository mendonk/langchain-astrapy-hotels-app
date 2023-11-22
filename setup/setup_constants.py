# File names are relative to "setup/"
RAW_REVIEW_SOURCE_FILE_NAME = "original/Datafiniti_Hotel_Reviews_Jun19.csv"
EMBEDDING_FILE_NAME = "precalculated_embeddings.json"
HOTEL_REVIEW_FILE_NAME = "hotel_reviews.csv"

MAX_REVIEW_TEXT_LENGTH = 4096
MAX_REVIEW_TITLE_LENGTH = 256

INSERTION_BATCH_SIZE = 20  # 20 is the max in JSON API
INSERTION_BATCH_CONCURRENCY = 20