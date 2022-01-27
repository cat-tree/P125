import dash
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import dispatch_processing as dispatch
import climate_processing as climate
import twitter_processing as twitter

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])


app.title = "Firewatch"

from dotenv import find_dotenv, load_dotenv
import os

# Loads the dotenv file into the environment. This exposes the variables in that
# file as though they were actual environment variables to the os module.
load_dotenv(find_dotenv())

BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
MAP_API_KEY = os.environ.get("MAP_API_KEY")


# Retrieve dispatch data and set climate variables
lat = 37.773972
lon = -122.431297
api_key = MAP_API_KEY
climate_data = climate.retrieve_climate_data(lat, lon, api_key)
climate_features = ['temp', 'feels_like', 'pressure', 'humidity', 'dew_point', 'uvi', 'clouds', 'visibility',
                    'wind_speed', 'wind_deg', 'wind_gust']

# Retrieve dispatch data and set related variables
lookback_period = 10
cfs_data = dispatch.retrieve_cfs_data(lookback_period) # Fetch all data
responseTimes = dispatch.processing_response_times(cfs_data) # Process for Response Times
mappingData = dispatch.prepare_data_for_mapping(cfs_data) # Process for Mapping Active Incidents

# Retrieve twitter data and set related variables
bearer_token = BEARER_TOKEN
twitter_search_days = 6
keywords = "san francisco wildfire lang:en"
twitter_data = twitter.retrieve_tweets(twitter_search_days, bearer_token, keywords)

app.layout = dbc.Container(
    [
        dbc.Row(dbc.Col(html.H2('FIREWATCH DASHBOARD', className='text-center text-primary, mb-3'))),  # header row
        dbc.Row([  # start of second row
            dbc.Col([html.H5('Map of Active Incidents', className='text-center'),
                     dcc.Graph(id='incidentsMap',
                          figure= dispatch.create_map_active_incidents(mappingData),
                          ),
                html.Hr()
            ], width={'size': 6, 'offset': 0, 'order': 1},
                   #style={ "height": "100%"}
                    ), # end of first column
            dbc.Col([  # second column on second row
                html.H5('Avg Response Time Past Week', className='text-center'),
                dcc.Graph(id='responsesChart',
                          figure=dispatch.plot_avg_response(responseTimes),
                          ),
                html.Hr()
            ], width={'size': 4, 'offset': 1, 'order': 2}
                #,style={ "height": "100%"}
            )  # width second column on second row
        ], #className="h-100"
        ),  # end of second row
dbc.Row([  # start of second row
            dbc.Col([  # first column on second row
                html.H5('Climate Data', className='text-center'),
                dcc.Dropdown(id='climate_dropdown',
                             value='temp',
                             options=[{'label': ctype, 'value': ctype}
                                      for ctype in climate_features]),
                dcc.Graph(id='weatherChart'),
                html.Hr(),
            ], width={'size':6, 'offset': 0, 'order': 1},
                #style={ "height": "50%"}
            ),  # width first column on second row
            dbc.Col([  # second column on second row
                html.H5('Fire Related Tweets', className='text-center'),
                 dcc.Graph(id='tweetList',
                          figure=twitter.list_tweets(twitter_data),
                          ),
                html.Hr()
            ], width={'size': 6, 'offset': 0, 'order': 2}
                #,style={ "height": "50%"}
            )  # width second column on second row
        ], #className="h-100"
        ),  # end of second row
    ], fluid=True,
    style={"height": "100vh"},
)


@app.callback(Output('weatherChart', 'figure'),
              Input('climate_dropdown', 'value'))
def plot_iclimate_features(ctype):
    fig = go.Figure()
    fig = px.line(climate_data, x='dt', y=ctype, markers=True)
    fig.layout.title = f'Weather data for {ctype}'
    fig.layout.paper_bgcolor = "#FFD700"
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
