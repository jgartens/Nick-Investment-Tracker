#Jacob Gartenstein
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.figure_factory as ff
import re
from geopy.geocoders import Nominatim

def searchSalesWeb():
    s = requests.Session()

    URL = 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=28'
    page = s.get(URL)

    soup = BeautifulSoup(page.content, 'html.parser')

    # print(soup.prettify())

    table = soup.find_all('table')[1] # Grab the first table
    # print(table.prettify)
    rows = table.find_all('tr')

    links = []

    rows = rows[2:]
    for row in rows:
        if row('td')[-1].get_text(strip = True) == "Real Estate":
            possible_link = row.find('a')
            if possible_link.has_attr('href'):
                links.append(possible_link.attrs['href'])
    # print(links)

    url = 'https://salesweb.civilview.com' + links[0]

    details_page = s.get(url)
    details_soup = BeautifulSoup(details_page.content, 'html.parser')
    columns = []
    table = details_soup.find_all('table')[0].find_all("tr")
    for row in table:
        key = row.find('td', class_="heading-bold columnwidth-15").get_text(strip = True)[:-6]
        columns.append(key)
    columns.append("Sheriff's Link")

    # print(info)
    df = pd.DataFrame(columns = columns)
    # print(df)


    for link in links:
        url = 'http://salesweb.civilview.com' + link
        details_page = s.get(url)
        details_soup = BeautifulSoup(details_page.content, 'html.parser')
        table = details_soup.find_all('table')[0].find_all("tr")
        info = {}
        for row in table:
            key = row.find('td', class_="heading-bold columnwidth-15").get_text(strip = True)[:-6]
            value = row.find_all('td')[1].get_text(strip = True)
            m = re.search('Writ Amount: (\$\d+,\d+\.\d+)', value)
            p = re.search('Writ Amount: (\$\d+,\d+,\d+\.\d+)', value)
            q = re.search('Writ Amount: (\$)', value)
            if m != None:
                value = m.group()
            elif p != None:
                value = p.group()
            elif q != None:
                continue
            value = value[:40]
            info[key] = value
            info["Sheriff's Link"] = "<a href='"+ url +"'>Sheriff's Link</a>"
        df = df.append(info, ignore_index = True)
    df = df.dropna()
    df = df.drop(columns = ['Sheriff #', 'Plaintiff','Attorney','Property Type'])
    return df


# print(df.to_string())



def searchTaxAssessor(addresses):
    main_url = "http://qpublic9.qpublic.net/la_orleans_display.php?KEY="
    list_of_dicts = []
    for address in addresses:
        street_address = match_address_type(address)
        if street_address == None:
            list_of_dicts.append(None)
            continue
        url = main_url + street_address
        # print(url)
        s1 = requests.Session()
        page = s1.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        if len(soup.find_all('table')) < 5 :
            list_of_dicts.append(None)
            continue
        # print(soup.prettify())
        table = soup.find_all('table')[3].find_all('tr')
        labels = table[2].find_all('td', class_="tax_header")
        labelsreal = []
        for label in labels:
            labelsreal.append(label.get_text(strip = True))
        labelsreal = labelsreal[:-4]
        # print(labelsreal)
        data = table[4].find_all('td', class_="tax_value")
        datareal = []
        for d in data:
            datareal.append(d.get_text(strip = True))
        info = {}
        info['Address'] = address
        info['Tax Link'] = "<a href='"+ url +"'>Tax Link</a>"
        for i, j in enumerate(labelsreal):
            info[j] = datareal[i]
        # print(info)
        # print(table)
        list_of_dicts.append(info)
    emptydict = {}
    emptydict["Address"] = address
    emptydict["Tax Link"] = None
    for label in labelsreal:
        emptydict[label] = None
    for i,dict in enumerate(list_of_dicts):
        if dict == None:
            list_of_dicts[i] = emptydict
    return list_of_dicts

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


df = searchSalesWeb()
addresses = df['Address']
dict = searchTaxAssessor(addresses)
df2 = pd.DataFrame(dict)
df = df.merge(df2, how = 'left', on = "Address")
df = df.drop(columns = ['Year'])
df =df.drop_duplicates(subset=['Address'], keep='first')
###DISPLAY DATAFRAME AS TABLE
fig =  ff.create_table(df)
fig.update_layout(
    autosize=False,
    width=4000,
    height=2000,
)
fig.write_image("table_plotly.png", scale=2000)
fig.show()
