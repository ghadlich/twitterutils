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
from tweepy.error import TweepError

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

def get_tweets(count = 800, verbose=True):
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
            query = api.home_timeline(count=200, exclude_replies=True)
        else:
            query = api.home_timeline(count=200, exclude_replies=True, max_id=max_id)

        if len(query) == 0:
            break

        # Save query
        ret = ret + query

        if verbose:
            print("Queried " + str(len(query)) + " tweets")

        max_id = query[-1].id

    if verbose:
        print("Found " + str(len(ret)) + " tweets")

    return ret
