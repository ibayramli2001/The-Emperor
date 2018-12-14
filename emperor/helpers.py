import requests
import os
import urllib.parse
import json
import pandas as pd
import re
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import pandas_datareader.data as web

from datetime import datetime
from flask import redirect, render_template, request, session, json
from functools import wraps

# error page
def apology(message, code=400):
    """Render message as an apology to user."""
    return render_template("apology.html", top=code, bottom=message)

# | from cs50 source code
def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# get stock data | from cs50 source code
def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        response = requests.get(f"https://api.iextrading.com/1.0/stock/{urllib.parse.quote_plus(symbol)}/quote")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"],
            "change": quote["changePercent"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def lookup_2(symbol):
    try:
        symbol = (symbol.lower()).strip()
        response = requests.get(f"https://financialmodelingprep.com/api/company/profile/{urllib.parse.quote_plus(symbol)}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
    # The request contains two redundant <pre> tags which .json() could not parse.
    # So. I used Regex instead to read text file from the API and then turn it into a JSON.
        profile = json.loads(re.sub(re.compile('<.*?>'), "", response.text))
        return {
            "companyName": profile[symbol]["companyName"],
            "Price": "{: .2f}".format(float(profile[symbol]["Price"])),
            "ChangesPerc": "{:.2f}".format(float((profile[symbol]["ChangesPerc"]).strip("()%"))),
            "Beta": "{: .2f}".format(float(profile[symbol]["Beta"])),
            "VolAvg": "{: .2f}".format(float(profile[symbol]["VolAvg"])/1000),
            "MktCap": "{: .2f}".format(float(profile[symbol]["MktCap"])/1000000),
            "LastDiv": "{: .2f}".format(float(profile[symbol]["LastDiv"])),
            "Range": profile[symbol]["Range"],
            "Changes": "{: .2f}".format(float(profile[symbol]["Changes"])),
            "exchange": profile[symbol]["exchange"],
            "industry": profile[symbol]["industry"],
            "website": profile[symbol]["website"],
            "sector": profile[symbol]["sector"],
            "image": profile[symbol]["image"]
        }
    except (KeyError, TypeError, ValueError):
        return None


#| from cs50 source code
def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

#| creates the stock graph on stockinfo
def graph(symbol):
    plotly.tools.set_credentials_file(username='lazimsiz1234', api_key='G0LQ3vuNvC8cX2NGbor4')
    try:
        df = web.DataReader(symbol.upper(), 'iex',
                        datetime(datetime.today().year - 1, datetime.today().month, datetime.today().day).strftime('%Y-%m-%d'),
                        datetime.today().strftime('%Y-%m-%d')).reset_index()
    except:
        return apology("Please input a valid symbol.")

    if df.empty:
        return apology("Please input a valid symbol.")

    trace_high = go.Scatter(
        x=df.date,
        y=df.high,
        name = f"{symbol} High",
        line = dict(color = '#17BECF'),
        opacity = 0.8)

    trace_low = go.Scatter(
        x=df.date,
        y=df.low,
        name = f"{symbol} Low",
        line = dict(color = '#7F7F7F'),
        opacity = 0.8)

    data = [trace_high,trace_low]

    layout = dict(
        title='Time Series with Rangeslider',
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(label='1y',
                        step='all'),
                    dict(count=6,
                         label='6m',
                         step='month',
                         stepmode='backward'),
                    dict(count=1,
                         label='1m',
                         step='month',
                         stepmode='backward')
                ])
            ),
            rangeslider=dict(
                visible = True
            ),
            type='date'
        )
    )
    fig = dict(data=data, layout=layout)
    return (py.plot(fig, filename = "Time Series with Rangeslider", auto_open = False) + ".embed")



