import streamlit as st
import pandas as pd
import sys
import os
import requests
import plotly.graph_objects as go


sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

st.title("SocialStockSentiment")

st.subheader('SocialStockSentiment is designed to simplify your stock research by pulling current and historical sentiment, on a given company for a time window of your choosing, stock price, ongoing themes into one location')

ticker = st.text_input('Please insert stock ticker (without $)').strip().upper()  # Remove whitespace and ensure uppercase

# Date Inputs
start_date = st.text_input('Please select the start date ("YYYY-MM-DD")').strip()  # Remove whitespace
end_date = st.text_input('Please select the end date ("YYYY-MM-DD")').strip()      # Remove whitespace

# Interval Input
interval = st.text_input(
    'Would you like your data to be daily ("1d"), weekly ("1wk"), monthly ("1mo"), quarterly ("3mo")?'
).strip()

# Check that all inputs are provided
if ticker and start_date and end_date and interval:
    if st.button(f'Pull data for {ticker}'):
        # Validate date format
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            st.error("Invalid date format. Please use YYYY-MM-DD.")
            start_date, end_date = None, None

        if start_date and end_date:
            # Call the function
            url = 'https://socialsentimentstock-438782600472.europe-west1.run.app/stock_data?'
            params = {'ticker_symbol' : ticker,
                      'start_date' : start_date,
                      'end_date' : end_date,
                      'interval' : interval}
            data = requests.get(url,params).json()

            sentiment_url = 'https://socialsentimentstock-438782600472.europe-west1.run.app/sentiment_data?'

            sentiment = requests.get(sentiment_url,params).json()
            st.write(sentiment)

            # Display result or error
            if isinstance(data, str):  # If the function returns an error message
                st.error(data)
            else:
                # Ensure 'Date' is a datetime index
                data = pd.DataFrame(data)
                # sentiment = pd.DataFrame(sentiment)
                data.index = pd.to_datetime(data.index)
                # sentiment.index = pd.to_datetime(data.index)

                interval_dict = {'1m':'m',
                                 '2m':'2m',
                                 '5m':'5m',
                                 '30m':'30m',
                                 '1h':'h',
                                 '1d':'D',
                                 '1wk':'7D',
                                 '1mo':'M',
                                 '3mo':'3M'}

                # Resample the data to end of each month and pick the last closing price
                data = data['Close'].resample(interval_dict[interval]).last()
                st.write(sentiment)
                # # Create Plotly figure
                # fig = go.Figure()

                # # Add stock line plot
                # fig.add_trace(go.Scatter(
                #     x=data.index,
                #     y=data.values,
                #     mode='lines',
                #     name='Stock Price',
                #     line=dict(color='blue'),
                #     yaxis='y1'
                # ))

                # # Add sentiment bar plot
                # fig.add_trace(go.Bar(
                #     x=sentiment.index,
                #     y=sentiment.values,
                #     name='Sentiment',
                #     marker_color=['green' if val > 0 else 'red' for val in sentiment.values],
                #     opacity=0.7,
                #     yaxis='y2'
                # ))

                # # Update layout for dual axes
                # fig.update_layout(
                #     title=f"{ticker} Stock Price and Sentiment",
                #     xaxis=dict(title='Date'),
                #     yaxis=dict(title='Stock Price', side='left'),
                #     yaxis2=dict(title='Sentiment', side='right', overlaying='y', showgrid=False),
                #     legend=dict(x=0, y=1)
                # )

                # # Display the chart
                # st.plotly_chart(fig)
