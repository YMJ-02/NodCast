"""
Uploads posts and images to X (Twitter).
"""

import os
import logging
import tweepy
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", ".env")
load_dotenv(env_path)

logger = logging.getLogger(__name__)


def upload_to_twitter(text, media_path=None):
    """
    Uploads a post to X (Twitter) using Tweepy V2 API.
    Returns True on success, False on failure.
    """
    try:
        # Kill switch: set ENABLE_TWITTER_POSTING=false to skip uploads
        # (e.g. when the monthly API quota is exhausted).
        if os.getenv("ENABLE_TWITTER_POSTING", "true").lower() in ("false", "0", "no"):
            logger.warning("Twitter posting disabled via ENABLE_TWITTER_POSTING. Skipping upload.")
            return False

        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

        if not all([api_key, api_secret, access_token, access_token_secret]):
            logger.error("Twitter API keys are missing. Skipping upload.")
            return False
        if any("your_" in str(v) for v in [api_key, api_secret, access_token, access_token_secret]):
            logger.error("Twitter API keys appear to be placeholder values. Skipping upload.")
            return False

        # V1.1 API for media upload
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
        api_v1 = tweepy.API(auth)

        # V2 API for tweeting
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )

        media_id = None
        if media_path and os.path.exists(media_path):
            logger.info(f"Uploading media: {media_path}")
            media = api_v1.media_upload(media_path)
            media_id = media.media_id

        logger.info("Publishing tweet...")
        if media_id:
            response = client.create_tweet(text=text, media_ids=[media_id])
        else:
            response = client.create_tweet(text=text)

        logger.info(f"Tweet published! ID: {response.data['id']}")
        return True

    except tweepy.errors.Forbidden as e:
        details = e.response.text if hasattr(e, 'response') else str(e)
        logger.error(f"Twitter 403 Forbidden: {details}")
        return False
    except Exception as e:
        logger.error(f"Error uploading to Twitter: {e}")
        return False


def publish_all(text, local_image_path=None):
    """
    Publishes to all active platforms. Returns True if all uploads succeeded.
    """
    logger.info("--- Starting Social Media Publishing ---")
    twitter_ok = upload_to_twitter(text, local_image_path)

    if not twitter_ok:
        logger.error("Twitter upload FAILED.")
    else:
        logger.info("All uploads completed successfully.")

    return twitter_ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
    logger.info("Testing SNS Uploader...")
    publish_all("Test Post from DeepTech_Scanner Bot #Tech #Beta")
