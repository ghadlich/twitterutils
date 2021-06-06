# twitterutils

## Intro
This repository holds twitter utilities I find useful to query tweets from my personal feed and on a specific topic. Personal feed APIs rely on tweepy whereas custom search queries rely on the Twitter v2 API.

## Prereqs
In order to use this libary, tweepy needs to be installed. This library also relies on environment variables to function. These need to be filled out with information from the Twitter developer portal:

| Environment Var          | Description                             |
| ------------------------ |:---------------------------------------:|
| BEARER_TOKEN             | Twitter API OAuth 2.0 Bearer Token      |
| ACCESS_TOKEN             | Twitter API Access Token                |
| ACCESS_TOKEN_SECRET      | Twitter API Access Secret Token         |
| CONSUMER_KEY             | Twitter API Consumer Key                |
| CONSUMER_SECRET          | Twitter API Consumer Secret             |
| TWITTER_USER             | Twitter Handle (Example: @GrantHadlich) |

## API

#### def tweet(status_text, image_path=None, enable_tweet=True, in_reply_to_status_id=None)
This function will tweet content to the TWITTER_USER account. Optional fields include image_path which points to an image to be uploaded and included in the tweet. An additional optional field is in_reply_to_status_id when this tweet is in response to another previously tweeted tweet.

#### get_tweets(count = 800, verbose=True)
This function pulls up to 800 tweets from the authenticated user's timeline

#### def recent_search_query(input_query, output_file, place=None, max_results = 3000, verbose=False)
This function does a recent search (last 7 days) with the input query. It places the results into a specified output_file. An optional parameter place is used when a specific place entity is desired to be matched to. For example, if one wanted to return confirmed 'North Dakota' entity matches, place would contain 'North Dakota'.

## Examples

### Pulling Status and Tweeting
```
from twitterutils import tweet
from twitterutils import get_tweets

if __name__ == "__main__":
    print("Pulling Latest Statuses")
    statuses = get_tweets()
	
	for status in statuses:
	    print("Tweet Content: " + status.text)

	# Post a tweet and image to Twitter
    print("Creating Initial Tweet")
    text = "This tweet and image will change the world!"
    id = tweet(text, image_path="./img/change_the_world.png")
	
	# Post a follow up reply
    text = "This one too!"
    id = tweet(text, image_path="./img/change_the_world_2.png", in_reply_to_status_id=id)
```

### Query Twitter
```
from twitterutils import recent_search_query

if __name__ == "__main__":
    # Pull latest 1000 tweets about the entity North Dakota	
	recent_search_query(f"-is:retweet lang:en North Dakota", 
                                output_file="nd.txt", 
                                place="North Dakota", 
                                max_results = 1000)
```

