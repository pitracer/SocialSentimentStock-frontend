import streamlit as st
import pandas as pd
import sys
import os
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime


sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

st.title("SocialStockSentiment")

st.subheader('SocialStockSentiment is designed to simplify your stock research by pulling historical sentiment, on a given top 5 NASDAQ company for a time window of your choosing.')

# Ticker input
ticker = st.selectbox(
    'Please select a stock ticker:',
    options=['AAPL', 'TSLA', 'GOOG', 'AMZN', 'MSFT']
)

# Date Inputs
start_date = st.text_input('Please select the start date ("YYYY-MM-DD")').strip()  # Remove whitespace
end_date = st.text_input('Please select the end date ("YYYY-MM-DD")').strip()      # Remove whitespace

# Interval Input
interval = st.selectbox(
    'Would you like your data to be daily ("1d"), weekly ("1wk"), monthly ("1mo"), quarterly ("3mo")?',
    options=['1d', '1wk', '1mo', '3mo']
)

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

            params_sentiment = {'ticker_symbol' : ticker,
                      'start_date' : start_date,
                      'end_date' : end_date}
            sentiment_url = 'https://socialsentimentstock-438782600472.europe-west1.run.app/sentiment_data?'

            sentiment = requests.get(sentiment_url,params_sentiment).json()
            sentiment = pd.DataFrame(sentiment)
            sentiment['Date'] = pd.to_datetime(sentiment['post_date'])
            sentiment.set_index('Date', inplace=True)

            # sentiment['']



            # Display result or error
            if isinstance(data, str):  # If the function returns an error message
                st.error(data)
            else:
                # Ensure 'Date' is a datetime index
                data = pd.DataFrame(data)
                data['Date'] = pd.to_datetime(data['Date'], errors='coerce', utc=True)  # Handle mixed time zones
                data.set_index('Date', inplace=True)

                interval_dict = {'1m':'m',
                                 '2m':'2m',
                                 '5m':'5m',
                                 '30m':'30m',
                                 '1h':'h',
                                 '1d':'D',
                                 '1wk':'7D',
                                 '1mo':'M',
                                 '3mo':'3M'}

                if not data.empty and not sentiment.empty:


                    data = data['Close'].resample(interval_dict[interval]).last()
                    sentiment = sentiment['numerical_sentiment'].resample(interval_dict[interval]).mean()



                else:
                    st.error("No data available for the specified ticker or date range.")
                    st.stop()

#<<<<<<////////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\>>>>>>

                # Create Plotly figure
                fig = go.Figure()

                # Add stock line plot
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data.values,
                    mode='lines',
                    name='Stock Price',
                    line=dict(color='blue'),
                    yaxis='y1'
                ))

                # Add sentiment bar plot
                fig.add_trace(go.Bar(
                    x=sentiment.index,
                    y=sentiment.values,
                    name='Sentiment',
                    marker_color=['green' if val > 0 else 'red' for val in sentiment.values],
                    opacity=0.7,
                    yaxis='y2'
                ))

                # Update layout for dual axes
                fig.update_layout(
                    title=f"{ticker} Stock Price and Sentiment",
                    xaxis=dict(title='Date'),
                    yaxis=dict(title='Stock Price', side='left'),
                    yaxis2=dict(title='Sentiment', side='right', overlaying='y', showgrid=False),
                    legend=dict(x=0, y=1)
                )

                # Display the chart

                st.plotly_chart(fig)



                # Calculate percentage change manually
                data = pd.DataFrame(data)
                data['Percent Change'] = data['Close'].diff() / data['Close'].shift(1) * 100


                # Align sentiment data with stock data

                sentiment = pd.DataFrame(sentiment)

#<<<<<<////////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\>>>>>>

                # Merge datasets

                data = data.reset_index()
                sentiment=sentiment.reset_index()
                if interval == '1wk':
                    sentiment['Date'] = sentiment['Date'] - pd.to_timedelta(sentiment['Date'].dt.dayofweek, unit='d')
                else:
                    sentiment['Date'] = sentiment['Date']
                merged_data = data.merge(sentiment, how='inner')
                # Add table of data so user can see
                st.write(merged_data)
                # Create Scatter Plot
                scatter_fig = px.scatter(
                    merged_data,
                    x='numerical_sentiment',
                    y='Percent Change',
                    title=f"Sentiment vs. Stock Price Change ({ticker})",
                    labels={'numerical_sentiment': 'Sentiment Score', 'Percent Change': 'Stock Price Change (%)'},
                    hover_data=['Date'],
                    color='Percent Change',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    size=[10] * len(merged_data)
                )
                # Update the layout to include a grid and ensure 0,0 is visible
                scatter_fig.update_layout(
                    xaxis=dict(
                        title='Sentiment Score',
                        zeroline=True,  # Add a zero line
                        zerolinecolor='black',  # Zero line color
                        showgrid=True,  # Show grid lines
                        gridcolor='lightgray'  # Grid line color
                    ),
                    yaxis=dict(
                        title='Stock Price Change (%)',
                        zeroline=True,  # Add a zero line
                        zerolinecolor='black',  # Zero line color
                        showgrid=True,  # Show grid lines
                        gridcolor='lightgray'  # Grid line color
                    ),
                )

                # Display scatter plot
                st.plotly_chart(scatter_fig)

#<<<<<<////////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\>>>>>>



                # Calculate percent changes
                merged_data['Sentiment Change'] = merged_data['numerical_sentiment'].pct_change() * 100
                merged_data['Price Change'] = merged_data['Close'].pct_change() * 100

                # Melt data for side-by-side bar chart
                bar_data = merged_data.melt(
                    id_vars='Date',
                    value_vars=['Sentiment Change', 'Price Change'],
                    var_name='Metric',
                    value_name='Change Percentage'
                )

                # Create figure with secondary y-axis
                fig = make_subplots(
                    rows=1, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.3,
                    subplot_titles=[f"{ticker} Sentiment vs Stock Price Change"],
                    specs=[[{'secondary_y': True}]]
                )

                # Adjusting the bar positions to prevent overlap
                bar_width = 0.4  # Adjust bar width for spacing
                sentiment_bar_offset = -bar_width / 2  # Offset for sentiment bars
                price_bar_offset = bar_width / 2  # Offset for price bars

                # Add Sentiment Change bars (first y-axis)
                fig.add_trace(
                    go.Bar(
                        x=bar_data[bar_data['Metric'] == 'Sentiment Change']['Date'],
                        y=bar_data[bar_data['Metric'] == 'Sentiment Change']['Change Percentage'],
                        name='Sentiment Change',
                        marker=dict(color='green'),
                        width=bar_width,  # Control the width of the bars
                        offsetgroup=1  # Group bars together for the same time values
                    ),
                    secondary_y=False
                )

                # Add Price Change bars (second y-axis)
                fig.add_trace(
                    go.Bar(
                        x=bar_data[bar_data['Metric'] == 'Price Change']['Date'],
                        y=bar_data[bar_data['Metric'] == 'Price Change']['Change Percentage'],
                        name='Price Change',
                        marker=dict(color='blue'),
                        width=bar_width,  # Control the width of the bars
                        offsetgroup=2  # Group bars together for the same time values
                    ),
                    secondary_y=True
                )

                # Update layout with two y-axes and separate bars
                fig.update_layout(
                    title=f"{ticker} Sentiment vs Stock Price Change",
                    xaxis_title='Date',
                    yaxis=dict(
                        title='Sentiment Change (%)',
                        side='left',
                        range=[-1000, 1000]  # Adjust the range as per your data scale
                    ),
                    yaxis2=dict(
                        title='Price Change (%)',
                        side='right',
                        overlaying='y',
                        range=[-10, 10]  # Adjust the range as per your data scale
                    ),
                    barmode='group',  # 'group' mode places bars side by side
                    bargap=0.2,  # Increase the gap between bars
                    legend=dict(x=0, y=1),
                )

                # Display the chart
                st.plotly_chart(fig)
