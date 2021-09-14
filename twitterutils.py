#!/usr/bin/env python
# encoding: utf-8

# Copyright (c) 2021 Grant Hadlich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE. 
import os
import time
import tweepy
import urllib.parse
import requests
from requests.auth import AuthBase
import json
from tqdm.auto import tqdm

# Bearer Token
BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
ACCESS_TOKEN = os.environ.get("TWITTER_ACCOUNT_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCOUNT_SECRET")
CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")
TWITTER_USER = os.environ.get("TWITTER_USER")

def tweet(status_text, image_path=None, enable_tweet=True, in_reply_to_status_id=None):
    """
    Creates a Tweet for the Authenticated Twitter User

    status_text - Body of the Tweet

    image_path - path to image to include in Tweet

    enable_tweet - if True, Tweet will be sent

    in_reply_to_status_id - Modifies the Tweet to be a reply to an existing Tweet
    """
    ret = None
    if enable_tweet:
        # Set up tweepy
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        api = tweepy.API(auth)

        # Prep status
        status = status_text

        # Upload Image
        if (image_path != None):
            ret = api.media_upload(image_path)
            media_ids = [ret.media_id]
        else:
            media_ids = None

        # If this is a reply, add in TWITTER_USER to front
        if (in_reply_to_status_id != None):
            status_text = f"{TWITTER_USER} {status_text}"

        # Upload Status
        status_ret = api.update_status(status=status, media_ids=media_ids, in_reply_to_status_id=in_reply_to_status_id)
        ret = status_ret.id
    else:
        print("Would have tweeted: " + status_text)

    return ret

def get_tweets(count = 800, output_file=None,verbose=True):
    """
    Pulls Tweets from Authenticated Twitter User

    Twitter API maxes out at 800 or input count number
    """
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    ret = []

    max_id = None

    queries = 0

    while count - len(ret) > 0 and queries < 4:
        time.sleep(2)
        queries += 1
        if max_id == None:
            query = api.home_timeline(count=200, exclude_replies=True, tweet_mode='extended')
        else:
            query = api.home_timeline(count=200, exclude_replies=True, max_id=max_id, tweet_mode='extended')

        if len(query) == 0:
            break

        # Save query
        ret = ret + query

        if verbose:
            print("Queried " + str(len(query)) + " tweets")

        max_id = query[-1].id

    if verbose:
        print("Found " + str(len(ret)) + " tweets")

    if output_file != None:
        output = []

        for item in ret:
            tweet = dict()

            tweet["author_id"] = item.author.id_str
            tweet["id"] = item.id_str
            tweet["lang"] = item.lang
            tweet["text"] = item.full_text
            tweet["source"] = item.source
            tweet["author"] = item.author.screen_name
            tweet["author_name"] = item.author.name
            tweet["author_followers"] = item.author.followers_count
            tweet["author_following"] = item.author.friends_count
            tweet["created_at"] = item.created_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")

            tweet["public_metrics"] = dict()
            tweet["public_metrics"]["retweet_count"] = item.retweet_count
            tweet["public_metrics"]["reply_count"] = 0
            tweet["public_metrics"]["like_count"] = item.favorite_count
            tweet["public_metrics"]["quote_count"] = 0

            tweet["entities"] = item.entities

            output.append(tweet)

        with open(output_file, 'w') as outfile:
            json.dump(output, outfile)

    return ret

# V2 APIs
def _get_recent_tweets(query, next_token, num_results):
    SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent?query="
    MAX_RESULTS_PER_QUERY = 100
    MIN_RESULTS_PER_QUERY = 10
    OPTIONS = f"&expansions=attachments.media_keys&tweet.fields=created_at,author_id,lang,source,public_metrics,context_annotations,entities"

    num_results = min(num_results, MAX_RESULTS_PER_QUERY)
    num_results = max(num_results, MIN_RESULTS_PER_QUERY)

    url = f"{SEARCH_URL}{query}{OPTIONS}&max_results={int(num_results)}"

    if (next_token != None):
        url = f"{url}&next_token={next_token}"

    header = {"Authorization": f"Bearer {BEARER_TOKEN}"}

    response = dict()

    attempts = 3

    while attempts > 0:
        attempts = attempts-1
        response = requests.get(url, headers=header)

        if response.status_code == 200:
            # Success
            break
        elif response.status_code == 503:
            print (f"Error with request (HTTP error code: {response.status_code} - {response.reason} - sleeping 30 seconds")
            time.sleep(30)
        elif response.status_code != 200:
            print (f"Error with request (HTTP error code: {response.status_code} - {response.reason} - sleeping 60 seconds")
            time.sleep(60)

    return response
    

def recent_search_query(input_query, output_file, place=None, max_results = 3000, verbose=False):
    query = urllib.parse.quote(input_query)

    #As we page through results, we will be counting these: 
    request_count = 0
    tweet_count = 0
    total_tweet_count=0

    query_result = []
    query_result_raw = []
    next_token = None

    consecutive_zero_query = 0
    MAX_CONSECUTIVE_ZERO_QUERIES = 5

    with tqdm(total=max_results, position=0, leave=True, desc=output_file) as pbar:
        while tweet_count < max_results and consecutive_zero_query <= MAX_CONSECUTIVE_ZERO_QUERIES:
            #loop body
            request_count += 1
            if (place is None):
                response = _get_recent_tweets(query, next_token, max_results-tweet_count)
            else:
                response = _get_recent_tweets(query, next_token, max(max_results-tweet_count, 50))
            parsed = json.loads(response.text)

            raw_data = parsed["data"]

            query_result_raw += raw_data

            if (place is None):
                data = raw_data
            else:
                data = []
                for tweet in raw_data:
                    done = False
                    try:
                        for annotation in tweet['entities']['annotations']:
                            if (annotation['type'] == "Place" and
                                annotation['probability'] > 0.5 and
                                (place.lower() == annotation['normalized_text'].lower() or 
                                 f"{place} State".lower() == annotation['normalized_text'].lower())):
                                data.append(tweet)
                                done = True
                                break
                    except KeyError:
                        pass

                    if done == True:
                        continue

                    try:
                        # Try Hashtags
                        for annotation in tweet['entities']['hashtags']:
                            if (place.lower().replace(" ","") == annotation['tag'].lower()):
                                data.append(tweet)
                                break
                    except KeyError:
                        pass

            query_result += data

            try:
                next_token  = parsed['meta']['next_token']
            except KeyError:
                next_token = None

            try:
                if (place is None):
                    tweet_count  += parsed['meta']['result_count']
                    pbar.update(parsed['meta']['result_count'])
                else:
                    total_tweet_count += parsed['meta']['result_count']
                    tweet_count += len(data)
                    pbar.update(len(data))
                    if (len(data) > 0):
                        consecutive_zero_query = 0
                    else:
                        consecutive_zero_query += 1
            except KeyError:
                pass

            if (next_token is None): break

            time.sleep(2)

        if (verbose):
            if (place is None):
                print(f"Made {request_count} requests and received {tweet_count} Tweets from Query: {input_query}")
            else:
                print(f"Made {request_count} requests and received {total_tweet_count} Tweets of which {tweet_count} were relevant from Query: {input_query}")
        try:
            with open(output_file, 'w') as outfile:
                json.dump(query_result, outfile)

            if len(query_result_raw) != len(query_result):
                with open(output_file.replace(".txt", "_raw.txt"), 'w') as outfile:
                    json.dump(query_result_raw, outfile)
        except:
            print("Printing to output file failed: " + outfile + " dumping to temp.txt")
            with open("temp.txt", 'w') as outfile:
                json.dump(query_result, outfile)
