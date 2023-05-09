#https://medium.com/analytics-vidhya/altair-interactive-multi-line-chart-59a29c9287d#
# Import libraries
import altair as alt
import pandas as pd
import streamlit as st

import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import pyti
import ta
# Define function to calculate price-to-earnings ratio
def get_pe_ratio(ticker):
    stock = yf.Ticker(ticker)
    try :
        pe_ratio = stock.info['trailingPE']
    except : 
        pe_ratio = 200
    return pe_ratio

# Define function to get stock information for energy sector companies in the S&P 500
def get_energy_stocks():
    sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
    energy_stocks = sp500[sp500['GICS Sector'] == 'Energy']['Symbol'].tolist()
    return energy_stocks


# Define function to filter undervalued stocks based on price-to-earnings ratio
def get_undervalued_stocks():
    energy_stocks = get_energy_stocks()
    undervalued_stocks = []
    for stock in energy_stocks:
        pe_ratio = get_pe_ratio(stock)
        if pe_ratio < 20:
            undervalued_stocks.append(stock)
    return undervalued_stocks

def get_bookValue(ticker):
    stock = yf.Ticker(ticker)
    try :
        bookValue = stock.info['bookValue']
    except : 
        bookValue = 0
    return bookValue
    
# Get list of undervalued stocks in the energy sector
undervalued_energy_stocks = get_undervalued_stocks()

# Print the list of undervalued stocks
st.write(undervalued_energy_stocks)
def get_sp500_financials():
    # Download the list of companies in the S&P 500
    sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
    symbols = sp500['Symbol'].tolist()
    symbols = symbols[:10]
    st.write("symbols",symbols)
    # Define the financial metrics to retrieve
    metrics = ['shortName','sector','marketCap', 'enterpriseValue', 'bookValue','trailingPE', 'forwardPE',
                 'priceToBook', 'enterpriseToRevenue',
                'profitMargins', 'grossMargins', 'operatingMargins',
               'returnOnAssets', 'returnOnEquity', 'revenue', 'revenuePerShare', 'ebitda',
               'netIncomeToCommon',
               'totalCash', 'totalCashPerShare', 'totalDebt',
               'currentRatio', 'quickRatio']
    


    # Create an empty DataFrame to store the financial data
    financials = pd.DataFrame(columns=['symbol'] + metrics)
    st.write("financials",financials.head())
    # Loop through each company and download its financial data
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            row = {'symbol': symbol}
            for metric in metrics:
                row[metric] = info.get(metric, None)
            financials = pd.concat([financials, pd.DataFrame(row, index=[0])], ignore_index=True)
        except:
            pass

    return financials

sp500_financials = get_sp500_financials()
sp500_financials.to_csv('sp500_financials.csv', index=False)
st.write(sp500_financials.head())
def get_historical_data(symbol, start_date, end_date):
    # Download the historical data using yfinance
    stock = yf.Ticker(symbol)
    data = stock.history(start=start_date, end=end_date)

    # Return the data as a Pandas DataFrame
    return data.reset_index()

AAPL = get_historical_data('AAPL', '2015-01-01', '2020-12-31')
st.write("AAPL",AAPL.head())
st.write('title','AAPL Stock Price')
#AAPL.plot(x='Date', y='Open', title='AAPL Stock Price')
fig=plt.figure()
ax=fig.add_subplot(1,1,1)
ax.scatter(
        AAPL["Date"],
        AAPL["Open"],
    )
ax.set_xlabel("Date")
ax.set_ylabel("Open")
st.write(fig)
#AAPL.plot(x='Date', y='Dividends', title='AAPL Dividends')
st.write('title','AAPL Dividends')
fig1=plt.figure()
ax=fig1.add_subplot(1,1,1)
ax.scatter(
        AAPL["Date"],
        AAPL["Dividends"],
    )
ax.set_xlabel("Date")
ax.set_ylabel("Dividends")
st.write(fig1)
import altair as alt
from vega_datasets import data

# uses intermediate json files to speed things up
alt.data_transformers.enable('json')

domain_stock_list = ["AAPL", "DIS", "FB", "MSFT", "NFLX", "TSLA"]

def getBaseChart():
    """
      Creates a chart by encoding the Data along the X positional axis and rolling mean along the Y positional axis 
      The mark (bar/line..) can be decided upon by the calling function.
    """
    base = (
        alt.Chart(AAPL)
        .encode(
            x=alt.X(
                "Date:T",
                axis=alt.Axis(title=None, format=("%b %Y"), labelAngle=0, tickCount=6),
            ),
            y=alt.Y(
                "rolling_mean:Q", axis=alt.Axis(title="Close (rolling mean in USD)")
            ),
        )
        .properties(width=500, height=400)
    )
    return base

def getSelection():
    """
      This function creates a selection element and uses it to "conditionally" set a color for a categorical variable (stock).
      It return both the single selection as well as the Category for Color choice set based on selection 
    """
    radio_select = alt.selection_multi(
        fields=["stock"], name="Stock", 
    )

    stock_color_condition = alt.condition(
        radio_select, alt.Color("stock:N", legend=None), alt.value("lightgrey")
    )

    return radio_select, stock_color_condition
    
def createChart():
    """
      This function uses the "base" encoding chart to create a line chart.
      The highlight_stocks variable uses the mark_line function to create a line chart out of the encoding.
      The color of the line is set using the conditional color set for the categorical variable using the selection.
      The chart is bound to the selection using add_selection.
      It also creates a selector element of a vertical array of circles so that the user can select between stocks 
    """

    radio_select, stock_color_condition = getSelection()

    make_selector = (
        alt.Chart(AAPL)
        .mark_circle(size=200)
        .encode(
            y=alt.Y("stock:N", axis=alt.Axis(title="Pick Stock", titleFontSize=15)),
            color=stock_color_condition,
        )
        .add_selection(radio_select)
    )

    base = getBaseChart()

    highlight_stocks = (
        base.mark_line(strokeWidth=2)
        .add_selection(radio_select)
        .encode(color=stock_color_condition)
    ).properties(title="Rolling Average of Stock Close")

    return base, make_selector, highlight_stocks, radio_select

def createTooltip(base, radio_select):
    """
        This function uses the "base" encoding chart and the selection captured.
        Four elements related to selection are created here
    """
    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(
        type="single", nearest=True, on="mouseover", fields=["Date"], empty="none"
    )

    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = (
        alt.Chart(AAPL)
        .mark_point()
        .encode(
            x="Date:T",
            opacity=alt.value(0),
        )
        .add_selection(nearest)
    )


    # Draw points on the line, and highlight based on selection
    points = base.mark_point(size=5, dy=-10).encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    ).transform_filter(radio_select)
    

    # Draw text labels near the points, and highlight based on selection
    tooltip_text = base.mark_text(
        align="left",
        dx=-60,
        dy=-15,
        fontSize=15,
        fontWeight="bold",
        lineBreak = "\n",
    ).encode(
        text=alt.condition(
            nearest, 
            alt.Text("rolling_mean:Q", format=".2f"), 
            alt.value(" "),
 
        ),
    ).transform_filter(radio_select)


    # Draw a rule at the location of the selection
    rules = (
        alt.Chart(AAPL)
        .mark_rule(color="black", strokeWidth=2)
        .encode(
            x="Date:T",
        )
        .transform_filter(nearest)
    )
    return selectors, rules, points, tooltip_text

def getImageLayer():
    """ 
      This function adds an image title to the chart. The Image is stored in relative path data
    """
    img_layer = (
        alt.Chart({"values": [{"url": "data/FooterImageForArticle.PNG"}]})
        .mark_image(align="left")
        .encode(
            x=alt.value(-100),
            x2=alt.value(650),
            y=alt.value(0),
            y2=alt.value(50),  # pixels from top
            url="url:N",
        )
        .properties(
            # set the dimensions of the visualization
            width=600,
            height=50,
        )
    )
    return img_layer

base, make_selector, highlight_stocks, radio_select  = createChart()

selectors, rules, points, tooltip_text  = createTooltip(base, radio_select)

img_layer = getImageLayer()

### Bring all the layers together with layering and concatenation
img_layer & (make_selector | alt.layer(highlight_stocks, selectors, points,rules, tooltip_text ))
AAPL = get_historical_data('AAPL', '2015-01-01', '2020-12-31')
st.write("AAPL",AAPL.head(2))
st.write("AAPL",AAPL.tail(2))