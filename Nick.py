#Jacob Gartenstein
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.figure_factory as ff
import re
from geopy.geocoders import Nominatim
import plotly.express as px
import dash_table
import geopandas
import dash   
import dash_core_components as dcc   
import dash_html_components as html 
from dash.dependencies import Input, Output 
from datetime import date
import plotly.graph_objects as go
import plotly

plotly.io.orca.config.executable = '/../../anaconda3/bin/orca'

def searchSalesWeb():
    s = requests.Session()

    URL = 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=28'
    page = s.get(URL)

    soup = BeautifulSoup(page.content, 'html.parser')

    table = soup.find_all('table')[1] # Grab the first table
    rows = table.find_all('tr')

    links = []

    #Scraping first page for links to individual "details" pages, for real estate items 
    rows = rows[2:]
    for row in rows:
        if row('td')[-1].get_text(strip = True) == "Real Estate":
            possible_link = row.find('a')
            if possible_link.has_attr('href'):
                links.append(possible_link.attrs['href'])

    #Gathering column headers to create dictionary
    url = 'https://salesweb.civilview.com' + links[0]

    details_page = s.get(url)
    details_soup = BeautifulSoup(details_page.content, 'html.parser')
    table = details_soup.find_all('table')[0].find_all("tr")
    info = {}
    for row in table:
        key = row.find('td', class_="heading-bold columnwidth-15").get_text(strip = True)[:-6]
        info[key] = []
    info["Sheriff's Link"] = []
    info["Auction Date"] = []

    #Scrape detailspages 
    for link in links:
        url = "http://salesweb.civilview.com" + link
        details_page = s.get(url)
        details_soup = BeautifulSoup(details_page.content, 'html.parser')
        table = details_soup.find_all('table')[0].find_all('tr')
        table2 = details_soup.find_all('table')[1].find_all('tr')

        for row in table:
            key = row.find('td', class_="heading-bold columnwidth-15").get_text(strip = True)[:-6]
            value = row.find_all('td')[1].get_text(strip = True)
    
            info[key].append(value)
        
        sheriff_link = "<a href=" + url + ">Sheriff's Link</a>"
        info["Sheriff's Link"].append(sheriff_link)

        #scrape auction date
        info["Auction Date"].append(table2[1].find_all('td')[1].get_text(strip = True))
    #Create DataFrame from details page information
    df = pd.DataFrame.from_dict(info)
    # df = df.dropna()
    df = df.drop(columns = ['Sheriff #', 'Property Type'])
    return df


"""
{Land Area: [], Building Area: [], 2019[Year[], Land Value[],...], 2020]
"""
def searchTaxAssessor(addresses):
    df = pd.DataFrame()
    main_url = "http://qpublic9.qpublic.net/la_orleans_display.php?KEY="
    for address in addresses:
        street_address = match_address_type(address)
    
        #Search for URL by adding address ID to end of url
        url = main_url + street_address
        s1 = requests.Session()
        page = s1.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        area_table = soup.find_all('table')[2].find_all('tr')
        area_table_headers =  ["Land Area (sq ft)" , "Building Area (sq ft)"]  
        area_table_data = []

        #parse data for appropriate values
        i = 5 #variable to move from tr4 -> tr5
        for header in area_table_headers:
            value = area_table[i].find_all('td')[3].get_text(strip = True)
            area_table_data.append(value)
            i = i+1

        area_table_data =[area_table_data]

        area_df = pd.DataFrame(np.array(area_table_data), columns = area_table_headers)

        #scrape value information tablle
        value_info_table = soup.find_all('table')[3].find_all('tr')
        table_headers = value_info_table[2]
        keys = table_headers.find_all('td', class_="tax_header")
        keys = keys[:-4]

        info = {}
        #Setup dictionary
        for i, key in enumerate(keys):
            info[key.get_text(strip = True)] = []
            keys[i] = key.get_text(strip = True)

        value_info_table =value_info_table[3:6]
        #parse data into appropriate boxes
        for row in value_info_table:
            values = row.find_all('td', class_="tax_value")  
            values = values[:-4]
            for i, value in enumerate(values):
                info[keys[i]].append(value.get_text(strip = True))
        
        value_info_df = pd.DataFrame.from_dict(info)

        #Add address column to both tables for merge, and tax link
        area_df["Address"] = address
        value_info_df["Address"] = address
        value_info_df["Tax Link"] = "<a href='"+ url +"'>Tax Link</a>"

        #merge tables on Address and set it as index
        tax_df = area_df.merge(value_info_df, on = 'Address')

        #Add to dataframe for every Address
        df = df.append(tax_df)
        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        #     print(tax_df)

    return df


def match_address_type(address):
    l = re.search('(\d+)-(\d+)', address)
    m = re.search('(\d+) ([A-Z]+) ([A-Z][A-Z])([nN][eE][wW])', address)
    n = re.search('(\d+) ([A-Z]+) ([A-Z]+) ([A-Z][A-Z])([nN][eE][wW])', address)
    o = re.search('(\d+) ([A-Z]+) ([A-Z]+) ([A-Z][A-Z]).*([nN][eE][wW])', address)
    p = re.search('(\d+) ([A-Z]+) ([A-Z][A-Z])[A-Z]+([nN][eE][wW])', address)
    q = re.search('(\d+) ([A-Z]) ([A-Z]+) ([A-Z][A-Z])([nN][eE][wW])', address)
    r = re.search('(\d+) ([A-Z]+) ([A-Z][A-Z]).*([nN][eE][wW])', address)
    if l != None:
        return None
    if m != None:
        num = m.group(1)
        name = m.group(2)
        type = m.group(3)
        street_address = num + "-" + name + type
        #print(street_address + " , m")
    elif n != None:
        num = n.group(1)
        name1 = n.group(2)
        name2 = n.group(3)
        type = n.group(4)
        street_address = num + "-" + name1 + name2 + type
        #print(street_address + " , n")
    elif o != None:
        num = o.group(1)
        name1 = o.group(2)
        name2 = o.group(3)
        type = o.group(4)
        if type == "WA":
            type = "WY"
        street_address = num + "-" + name1 + name2 + type
        #print(street_address + " , o")
    elif p != None:
        num = p.group(1)
        name = p.group(2)
        type = p.group(3)
        if type == "WA":
            type = "WY"
        street_address = num + "-" + name + type
        # print(street_address + " , p")
    elif q != None:
        num = q.group(1)
        dir = q.group(2)
        name = q.group(3)
        type = q.group(4)
        street_address = num + "-" + dir + name + type
        #print(street_address + " , q")
    elif r != None:
        num = r.group(1)
        name = r.group(2)
        type = r.group(3)
        street_address = num + "-" + name + type
        #print(street_address + " , r")
    else:
        return None
    return street_address

def createGeocode(address):
    l = re.search('(\d+)-(\d+)', address)
    m = re.search('(\d+) ([A-Z]+) ([A-Z][A-Z])([nN][eE][wW])', address)
    n = re.search('(\d+) ([A-Z]+) ([A-Z]+) ([A-Z][A-Z])([nN][eE][wW])', address)
    o = re.search('(\d+) ([A-Z]+) ([A-Z]+) ([A-Z][A-Z]).*([nN][eE][wW])', address)
    p = re.search('(\d+) ([A-Z]+) ([A-Z][A-Z])[A-Z]+([nN][eE][wW])', address)
    q = re.search('(\d+) ([A-Z]) ([A-Z]+) ([A-Z][A-Z])([nN][eE][wW])', address)
    r = re.search('(\d+) ([A-Z]+) ([A-Z][A-Z]).*([nN][eE][wW])', address)
    if l != None:
        return None
    if m != None:
        num = m.group(1)
        name = m.group(2)
        type = m.group(3)
        street_address = num + " " + name + " " + type + " New Orleans LA"
        #print(street_address + " , m")
    elif n != None:
        num = n.group(1)
        name1 = n.group(2)
        name2 = n.group(3)
        type = n.group(4)
        street_address = num + " " + name1 + " " + name2 + " " + type + " New Orleans LA"
        #print(street_address + " , n")
    elif o != None:
        num = o.group(1)
        name1 = o.group(2)
        name2 = o.group(3)
        type = o.group(4)
        if type == "WA":
            type = "Way"
        street_address = num + " " + name1 + " " + name2 + " " + type + " New Orleans LA"
        #print(street_address + " , o")
    elif p != None:
        num = p.group(1)
        name = p.group(2)
        type = p.group(3)
        if type == "WA":
            type = "Way"
        street_address = num + " " + name + " " + type + " New Orleans LA"
        # print(street_address + " , p")
    elif q != None:
        num = q.group(1)
        dir = q.group(2)
        name = q.group(3)
        type = q.group(4)
        street_address = num + " " + dir + " " + name + " " + type + " New Orleans LA"
        #print(street_address + " , q")
    elif r != None:
        num = r.group(1)
        name = r.group(2)
        type = r.group(3)
        street_address = num + " " + name + " " + type + " New Orleans LA"
        #print(street_address + " , r")
    else:
        return None
    return street_address

def getWritAmount(string):
    m = re.search('Writ Amount: (\$\d+,\d+\.\d+)', string)
    p = re.search('Writ Amount: (\$\d+,\d+,\d+\.\d+)', string)
    if m != None:
        return m.group(1)
    elif p != None:
        return p.group(1)
    else: 
        return np.nan

def getWritDate(string):
    t = re.search('Writ Assigned Date: (\d+\/\d+\/\d+)', string)
    if t != None:
        return t.group(1)
    else:
        return np.nan

def getWithAppraisal(string):
    q = re.search('With Appraisal: Yes', string)
    s = re.search('With Appraisal : Yes', string)
    if q != None or s != None: 
        return "Yes"
    else: 
        return "No"

def hasTaxLink(address):
    main_url = "http://qpublic9.qpublic.net/la_orleans_display.php?KEY="
    street_address = match_address_type(address)
    if street_address == None:
        return False
    url = main_url + street_address
    s1 = requests.Session()
    page = s1.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    if len(soup.find_all('table')) < 5 :
        return False
    return True
        
    

#create dataframe with salesweb search
df = searchSalesWeb()

df["Writ Amount"] = df.apply(lambda row: getWritAmount(row["Writ and Appraisal"]), axis= 1)
df["Writ Assigned Date"] = df.apply(lambda row: getWritDate(row["Writ and Appraisal"]), axis= 1)
df["Appraisal"] = df.apply(lambda row: getWithAppraisal(row["Writ and Appraisal"]), axis= 1)
df = df.drop(columns = ['Writ and Appraisal'])

#test if it can be found on tax link
df["hastaxlink"] = df.apply(lambda row: hasTaxLink(row["Address"]), axis= 1)

#seperate into seperate dataframes
bad_df = df[df['hastaxlink'] == False].drop(columns = ["hastaxlink"])
df = df[df['hastaxlink'] == True].drop(columns = ["hastaxlink"])


#Search Tax Assesor for more data 
addresses = df['Address']
df2 = searchTaxAssessor(addresses)
df = df.merge(df2, on = "Address")





df["Address"] = df.apply(lambda row: createGeocode(row["Address"]), axis= 1)

value_info_df = df.drop(columns = ["Appraisal", "Land Area (sq ft)", 
"Building Area (sq ft)", "Auction Date", "Writ Amount", 
"Writ Assigned Date", "Appraisal", "Attorney", "Plaintiff", "Tax Link", "Sheriff's Link"])
value_info_df.set_index(["Address", "Year"])

df = df[df['Year'] == "2021"]
# df = df.set_index(["Address"])

# with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
#     print(df)


# print(df["Address"])
geolocator = Nominatim(user_agent="nick-application")
df['geo'] = df.apply(lambda row: geolocator.geocode(row['Address']), axis=1)
df = df.dropna()
df['lat'] = df.apply(lambda row: geolocator.geocode(row['Address']).latitude, axis=1)
df['lon'] = df.apply(lambda row: geolocator.geocode(row['Address']).longitude, axis=1)

gdf = geopandas.GeoDataFrame(
    df, geometry=geopandas.points_from_xy(df.lon, df.lat))

gdf.drop(columns = ["lon", "lat"])







 


# ##DISPLAY DATAFRAME AS TABLE
# chart =  ff.create_table(df)
# chart.update_layout(
#     autosize=True,
#     # width=4000,
#     # height=2000,
# )
# # chart.write_image("table_plotly.png", scale=2000)
# chart.show()



###------------------------------------------------------------------------------------
## Web App using Bash 

app = dash.Dash(__name__)


app.layout = html.Div([

    html.Div(id = 'heading', children= [ 
        html.H1("Houses For Impedding Auction", style= {'text-align': 'center'}),
        html.H3("New Orleans"),
        html.H3("{:%d, %b %Y}".format(date.today()))
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

    # html.Br(),

    dcc.Graph(id='houses_for_auction_nola', children=[]),
    
    html.Div(id='output_container', children=[]),

    html.Div(id = "table", children = [
        html.H2("Properties without Tax Accesor Matches", style= {'color': 'red'}),
        dcc.Graph(
        id='bad_table', children = [])])

])

@app.callback(
    [Output(component_id='output_container', component_property='children'),
    Output(component_id='houses_for_auction_nola', component_property='figure'),
    Output(component_id='bad_table', component_property='figure')],
    [Input(component_id='slct_neighborhood', component_property='value'),
    Input(component_id='input_neighborhood', component_property='value')]
)
def update_graph(neighborhood_choice, neigborhood_input):

    px.set_mapbox_access_token("pk.eyJ1IjoiamdhcnRlbnMiLCJhIjoiY2tndHd0bmZ5MDJkbTJzdGhldDVrdDgydyJ9.5Ols2mna_XccKHQC-XoCvA")

    Address = gdf["Address"]
    Auction = gdf["Auction Date"]
    Value = gdf["Total Value"]
    Land = gdf["Land Area (sq ft)"]
    Writ = gdf["Writ Amount"]
    Appraisal = gdf["Appraisal"]

    fig = px.scatter_mapbox(gdf,
                        lat=gdf.geometry.y,
                        lon=gdf.geometry.x,
                        
                        # hover_name="Address",
                        # hoverinfo = "text",
                        # hover_data={"lat": False,  "Auction Date": True, "Total Value": True, "Land Area (sq ft)": True, "Writ Amount": True, "Appraisal": True},
                        hovertemplate =
                        '<h3> %{Address}</h3><br>' +
                        '%{Auction}<br>' +
                        '%{Value} <br>'+
                        '%{Land}<br>' +
                        '%{Writ}<br>' +
                        '%{Appraisal}<br><extra></extra>' ,
                        showlengend = False,
                        color_discrete_sequence=["green"], 
                        zoom=10, 
                        height=800)

    # fig.add_trace(go.Scatter(
        
    #     hovertemplate = 'Price: %{y:$.2f}<extra></extra>',
    #     showlegend = False))

    table = go.Figure(data=[go.Table(
            columnorder = [1,2,3],
            columnwidth = [300, 200, 100],
            header=dict(values= ["Address", "Sheriff's Link"],
            fill_color='paleturquoise',
            align='left'),
            cells=dict(values= [bad_df.Address,  bad_df["Sheriff's Link"]],
            fill_color='lavender',
            align='left'))])

    fig.show()
    table.show()

    return "Display selected data here", fig, table



if __name__ == '__main__':
    app.run_server(debug=True)

















