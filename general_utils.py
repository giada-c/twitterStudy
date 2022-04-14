import json


def get_string_json(s, index):
    value = []
    s = s.replace("\'", "\"")
    s = s.replace('\0', '')
    try:
        for j in json.loads(s):
            value.append(j[index])
    except json.decoder.JSONDecodeError:
        pass
    return value

def separate_post_type(tweets):
    cols_needed = ['rt_created_at','quoted_status_id','in_reply_to_user_id','in_reply_to_screen_name']
    if not set(cols_needed).issubset(tweets.columns):
        return [float('nan')] * 4
    
    retweets = tweets.dropna(subset=['rt_created_at'])
    quotes = tweets[tweets["quoted_status_id"].notna() & tweets["rt_created_at"].isna()]
    replies = tweets[tweets["in_reply_to_user_id"].notna() & tweets["quoted_status_id"].isna()]
    original_tweets = tweets[tweets["in_reply_to_screen_name"].isna() & tweets["rt_created_at"].isna() & tweets["quoted_status_id"].isna()]
    
    return[original_tweets,retweets,replies,quotes]
