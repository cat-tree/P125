import pandas as pd
import datetime
import plotly.express as px


# ********* DATA RETRIEVAL *********

def retrieve_cfs_data(lookback):
    # set lookback window
    periodend = datetime.datetime.now().isoformat()
    periodstart = (datetime.datetime.now() - datetime.timedelta(days=lookback)).isoformat()
    # Get count of incidents to determine limit to retrieve
    num = pd.read_json(
        "https://data.sfgov.org/resource/RowID.json?$select=COUNT(incident_number)&$where=call_date%20between%20%27"
        + str(periodstart) + "%27%20AND%20%27" + str(periodend) + "%27")
    maxNumber = num.iloc[0, 0]
    # Use record to write query call to API to get all incidents needed/bypass API default of 1000
    query_str = ("https://data.sfgov.org/resource/RowID.json?$where=call_date%20between%20%27"
                 + str(periodstart) + "%27%20AND%20%27"
                 + str(periodend) + "%27&$limit=" + str(maxNumber))
    cfs_data = pd.read_json(query_str)

    return cfs_data


# ********* RESPONSE TIMES *********

def processing_response_times(cfs_data):
    # Select relevant data needed for aggregation
    cols = ['dispatch_dttm', 'on_scene_dttm', 'battalion', 'original_priority', 'unit_type']
    responseTimes = cfs_data[cols].copy()
    # Clean data - remove empty values
    responseTimes.dropna(inplace=True)
    # Clean data - convert data to date/time
    responseTimes['dispatch_dttm'] = pd.to_datetime(responseTimes['dispatch_dttm'])
    responseTimes['on_scene_dttm'] = pd.to_datetime(responseTimes['on_scene_dttm'])
    # Calculation - time from dispatch to on scene
    responseTimes['ResponseMins'] = ((responseTimes.on_scene_dttm - responseTimes.dispatch_dttm).dt.total_seconds())/60
    # Aggregation - Response time by day
    responseTimes = responseTimes.set_index('dispatch_dttm').groupby(pd.Grouper(freq='d')).mean().dropna(how='all')

    return responseTimes


def plot_avg_response(df):
    fig = px.line(df, title='Avg Response Time Past Week')
    fig.update_layout(paper_bgcolor="#e0e0e0",
                      font_color="black",
                      xaxis_title="Date (Prior 10 days)",
                      yaxis_title="Average Response Time (Minutes)")
    return fig

# ********* MAP OF INCIDENTS *********

def prepare_data_for_mapping(df):
    cols = ['entry_dttm', 'on_scene_dttm', 'call_type', 'case_location'] # Relevant data needed for aggregation
    activeInc = df[cols].copy()
    activeInc.dropna(inplace=True) # Clean data - remove empty values
    # Clean data - convert data to date/time
    activeInc['entry_dttm'] = pd.to_datetime(activeInc['entry_dttm'])
    activeInc['on_scene_dttm'] = pd.to_datetime(activeInc['on_scene_dttm'])
    # Calculation - time on scene
    activeInc['OnSceneMins'] = (activeInc.on_scene_dttm - activeInc.entry_dttm).dt.total_seconds()/60
    activeInc['OnSceneMins'] = activeInc['OnSceneMins'].astype(int)
    activeInc['on_scene_dttm'] = activeInc['on_scene_dttm'].dt.round("5min")
    activeInc = activeInc.drop(['entry_dttm'], axis=1)
    activeInc['date_str'] = activeInc['on_scene_dttm'].apply(lambda x: str(x))
    activeInc = activeInc.loc[activeInc['OnSceneMins'] > 0]
    activeInc = pd.concat(
        [activeInc.drop(['case_location'], axis=1), activeInc['case_location'].apply(pd.Series)], axis=1)
    activeInc[['long', 'lat']] = pd.DataFrame(activeInc.coordinates.tolist(), index=activeInc.index)

    return activeInc

def create_map_active_incidents(df):
    fig = px.scatter_mapbox(df,
                            lat="lat", lon="long", color="call_type",
                            size=df.OnSceneMins, hover_name="call_type",
                            color_continuous_scale=px.colors.cyclical.IceFire, size_max=15, zoom=10,
                            mapbox_style="carto-positron")
    return fig