import sqlite3
from pathlib import Path


def create_tables():
    """
    Creates the necessary tables in the SQLite database with appropriate
    data types, foreign key constraints, and indexing for optimization.
    """
    db_path = Path(__file__).parent / "JK_ig.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the 'content' table with appropriate data types and constraints
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content (
            content_id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT,
            media_type TEXT,
            title TEXT,
            caption TEXT,
            hashtags TEXT,
            mentions TEXT,
            location_id INTEGER,
            music_track_id TEXT,
            media_file_names TEXT,
            media_paths TEXT,
            link TEXT,
            publish_date TEXT,
            publish_time TEXT,
            status TEXT,
            gs_row_number INTEGER,
            error_message TEXT
        )
    """)

    # Create the 'posts' table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            post_id INTEGER PRIMARY KEY,
            content_id INTEGER,
            media_type INTEGER,
            product_type TEXT,
            caption TEXT,
            timestamp TEXT,
            media_url TEXT,
            location_pk INTEGER,
            location_name TEXT,
            like_count INTEGER,
            comment_count INTEGER,
            is_album INTEGER,
            album_media_ids TEXT,
            album_media_urls TEXT,
            status TEXT,
            FOREIGN KEY (content_id) REFERENCES content(content_id)
        )
    """
    )

    # Create the 'reels' table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reels (
            reel_id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER,
            caption TEXT,
            timestamp TEXT,
            media_url TEXT,
            thumbnail_url TEXT,
            location_pk INTEGER,
            location_name TEXT,
            like_count INTEGER,
            comment_count INTEGER,
            audio_track TEXT,
            effects TEXT,
            duration INTEGER,
            status TEXT,
            FOREIGN KEY (content_id) REFERENCES content(content_id)
        )
    """
    )

    # Create the 'stories' table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stories (
            pk INTEGER PRIMARY KEY,
            story_id TEXT,
            content_id INTEGER,
            code TEXT,
            taken_at TEXT,
            reel_url TEXT,
            caption TEXT,
            mentions TEXT,
            location_id INTEGER,
            hashtags TEXT,
            link TEXT,
            FOREIGN KEY (content_id) REFERENCES content(content_id)
        )
    """
    )

    # Create the 'comments' table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            comment_id INTEGER PRIMARY KEY,
            post_id INTEGER,
            user_id INTEGER,
            comment_text TEXT,
            timestamp TEXT,
            reply_to_comment_id INTEGER,
            status TEXT,
            user_name TEXT,
            user_full_name TEXT,
            is_business_account INTEGER,
            FOREIGN KEY (post_id) REFERENCES posts(post_id)
        )
    """
    )

    # Create indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_posts_content_id ON posts (content_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_reels_content_id ON reels (content_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_stories_content_id ON stories (content_id)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_status ON content (status)")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
