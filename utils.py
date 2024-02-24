import logging

import requests

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def create_url(for_user):
    return "https://api.twitter.com/2/users/{}/tweets".format(for_user)


def get_params(last_tweet_id):
    return {"tweet.fields": "created_at", "max_results": 5, "since_id": last_tweet_id}


def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers


def connect_to_endpoint(url, headers, params):
    try:
        response = requests.request(
            "GET", url, headers=headers, params=params, timeout=15
        )
        if response.status_code != 200:
            raise Exception(
                "Request returned an error: {} {}".format(
                    response.status_code, response.text
                )
            )
        return response.json()
    except Exception as ee:
        logger.error("{}".format(ee))


def get_tweets(last_tweet_id, bearer_token, for_user):
    url = create_url(for_user)
    headers = create_headers(bearer_token)
    params = get_params(last_tweet_id)
    json_response = connect_to_endpoint(url, headers, params)
    return json_response
