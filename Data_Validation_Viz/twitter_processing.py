import datetime
import pandas as pd
import plotly.graph_objects as go
import requests

# Twitter functions
def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}

    return headers

def create_url(keyword, start_date, end_date, max_results=10):
    search_url = "https://api.twitter.com/2/tweets/search/recent"  # Change to the endpoint you want to collect data from

    # change params based on the endpoint you are using
    query_params = {'query': keyword,
                    'start_time': start_date,
                    'end_time': end_date,
                    'max_results': max_results,
                    'expansions': 'author_id,in_reply_to_user_id,geo.place_id',
                    'tweet.fields': 'id,text,author_id,in_reply_to_user_id,geo,conversation_id,created_at,lang,public_metrics,referenced_tweets,reply_settings,source',
                    'user.fields': 'id,name,username,created_at,description,public_metrics,verified',
                    'place.fields': 'full_name,id,country,country_code,geo,name,place_type',
                    'next_token': {}}
    return (search_url, query_params)


def connect_to_endpoint(url, headers, params, next_token=None):
    params['next_token'] = next_token  # params object received from create_url function
    response = requests.request("GET", url, headers=headers, params=params)
    print("Endpoint Response Code: " + str(response.status_code))
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()

def retrieve_tweets(days, bearer_token, keyword):
    periodend = datetime.datetime.now().isoformat()
    periodstart = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
    headers = create_headers(bearer_token) # Inputs for the request
    start_time = periodstart[:-2] + 'Z'
    end_time = periodend[:-2] + 'Z'
    max_results = 100 # TAKE THIS OFF FOR PROD!
    url = create_url(keyword, start_time, end_time, max_results)
    json_response = connect_to_endpoint(url[0], headers, url[1])
    tweets = pd.json_normalize(json_response['data'])
    # Exclude re-tweets
    tweets.drop(tweets[tweets['referenced_tweets'].notna()].index, inplace=True)
    tweets.reset_index(inplace=True, drop=True)
    # Include only relevant columns
    cols = ['text', 'created_at']
    skinnyTweets = tweets[cols].copy()
    skinnyTweets = skinnyTweets.rename(columns={"text": "Tweet", "created_at": "Timestamp"})

    return skinnyTweets

def list_tweets(df):
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    fill_color='#F28C28',
                    #align='left'
                    ),
        cells=dict(values=[df.Tweet, df.Timestamp],
                   fill_color='#FAC898',
                   #align='left'
                   ))
    ])

    return fig