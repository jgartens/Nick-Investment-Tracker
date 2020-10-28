# import Nick.py

import pandas as pd  
import plotly.express as px
import geopandas as gpd
import dash   
import dash_core_components as dcc   
import dash_html_components as html 
from dash.dependencies import Input, Output 
from datetime import date
import plotly.graph_objects as go
import importlib
from geopy.geocoders import Nominatim

importlib.import_module("Nick")
app = dash.Dash(__name__)



app.layout = html.Div([

    html.Div(id = 'heading', children= [ 
        html.H1("Houses For Impedding Auction", style= {'text-align': 'center'}),
        html.H3("New Orleans"),
        html.H3(date.today())
    ]),

    dcc.Dropdown(id="slct_neighborhood",
                options=[
                    {"label": "Uptown", "value" : "uptown"},
                    {"label": "Midcity", "value" : "midcity"},
                    {"label": "Garden District", "value" : "garden"},
                    {"label": "Downtown / Remainder", "value" : "downtown"}
                ],
                multi=False, 
                value= "",
                style={'width': "40%"}
                ),
    
    dcc.Input(
    id="input_neighborhood",
    placeholder='Enter a value...',
    type='text',
    value=''),

    html.Div(id='output_container', children=[]),
    html.Br(),

    dcc.Graph(id='houses_for_auction_nola', children=[])

])

@app.callback(
    [Output(component_id='output_container', component_property='children'),
    Output(component_id='houses_for_auction_nola', component_property='figure')],
    [Input(component_id='slct_neighborhood', component_property='value'),
    Input(component_id='input_neighborhood', component_property='value')]
)
def update_graph(neighborhood_choice, neigborhood_input):

    # dff = df.copy()

    px.set_mapbox_access_token("pk.eyJ1IjoiamdhcnRlbnMiLCJhIjoiY2tndHd0bmZ5MDJkbTJzdGhldDVrdDgydyJ9.5Ols2mna_XccKHQC-XoCvA")
    df = px.data.carshare()
    fig = px.scatter_mapbox(df, lat="centroid_lat", lon="centroid_lon",     color="peak_hour", size="car_hours",
                  color_continuous_scale=px.colors.cyclical.IceFire, size_max=15, zoom=10)
    fig.show()

   

    return "hello", fig



if __name__ == '__main__':
    app.run_server(debug=True)