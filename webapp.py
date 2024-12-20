import streamlit as st
import pandas as pd
import sys
import os
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, date




sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
st.title("SocialSentimentStock")
st.subheader('SocialSentimentStock is designed to simplify your stock research by pulling historical sentiment, on the top 5 NASDAQ companies, for a time window of your choosing.')

tweet_url = 'https://socialsentimentstock-438782600472.europe-west1.run.app/get_tweet?'


# Initialize session state
if 'data_fetched' not in st.session_state:
    st.session_state['data_fetched'] = False

# Ticker input
ticker = st.selectbox(
    'Please select a stock ticker:',
    options=['AAPL', 'TSLA', 'GOOG', 'AMZN', 'MSFT']
)

# Date inputs
start_date = st.date_input(
    "Please select the start date",
    value=date(2015, 1, 1),
    min_value=date(2015, 1, 1),
    max_value=date(2019, 12, 31),
)
end_date = st.date_input(
    "Please select the end date",
    value=date(2015, 1, 31),
    min_value=date(2015, 1, 1),
    max_value=date(2019, 12, 31),
)

# Interval input
interval = st.selectbox(
    'Would you like your data to be daily ("1d"), weekly ("1wk"), monthly ("1mo"), quarterly ("3mo")?',
    options=['1d', '1wk', '1mo', '3mo']
)

if start_date > end_date:
    st.error("The start date must be earlier than or equal to the end date.")

# Fetch data only on button click
if ticker and start_date and end_date and interval:

    if st.button(f'Pull data for {ticker}') or st.session_state['data_fetched']:
        if not st.session_state['data_fetched']:
            # API URLs
            stock_url = 'https://socialsentimentstock-438782600472.europe-west1.run.app/stock_data?'
            sentiment_url = 'https://socialsentimentstock-438782600472.europe-west1.run.app/sentiment_data?'

            # API parameters
            params = {'ticker_symbol': ticker, 'start_date': start_date, 'end_date': end_date, 'interval': interval}
            sentiment_params = {'ticker_symbol': ticker, 'start_date': start_date, 'end_date': end_date}

            # Fetch and process stock data
            stock_data = requests.get(stock_url, params=params).json()
            stock_df = pd.DataFrame(stock_data)
            stock_df['Date'] = pd.to_datetime(stock_df['Date'], errors='coerce', utc=True)
            stock_df.set_index('Date', inplace=True)

            # Fetch and process sentiment data
            sentiment_data = requests.get(sentiment_url, params=sentiment_params).json()
            sentiment_df = pd.DataFrame(sentiment_data)
            sentiment_df['Date'] = pd.to_datetime(sentiment_df['post_date'])
            sentiment_df.set_index('Date', inplace=True)

            # Store data in session state
            st.session_state['stock_df'] = stock_df
            st.session_state['sentiment_df'] = sentiment_df
            st.session_state['data_fetched'] = True
            st.write("Click the button below to refresh the page.")

        def reset_session_state():
            # Clear all session state variables
            for key in st.session_state.keys():
                del st.session_state[key]

        # Refresh button at the top of the page
        if st.button("Refresh Page"):
            reset_session_state()  # Clear session state variables
            st.stop()  # Prevent further execution of the script to simulate refresh


        # Access data from session state
        stock_df = st.session_state['stock_df']
        sentiment_df = st.session_state['sentiment_df']

        # Resample data
        interval_dict = {'1d': 'D', '1wk': '7D', '1mo': 'M', '3mo': '3M'}
        stock_resampled = stock_df['Close'].resample(interval_dict[interval]).last()
        sentiment_resampled = sentiment_df['numerical_sentiment'].resample(interval_dict[interval]).mean()

        # Create Plotly figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=stock_resampled.index,
            y=stock_resampled.values,
            mode='lines',
            name='Stock Price',
            line=dict(color='blue'),
            yaxis='y1'
        ))
        fig.add_trace(go.Bar(
            x=sentiment_resampled.index,
            y=sentiment_resampled.values,
            name='Sentiment',
            marker_color=['green' if val > 0 else 'red' for val in sentiment_resampled.values],
            opacity=0.7,
            yaxis='y2'
        ))
        fig.update_layout(
            title=f"{ticker} Stock Price and Sentiment",
            xaxis=dict(title='Date'),
            yaxis=dict(title='Stock Price', side='left'),
            yaxis2=dict(title='Sentiment', side='right', overlaying='y', showgrid=False),
            legend=dict(x=0, y=1)
        )
        st.plotly_chart(fig)









#----------------------------------
# After fetching and processing the stock and sentiment data in session state
if st.session_state['data_fetched']:
    # Access data from session state
    stock_df = st.session_state['stock_df']
    sentiment_df = st.session_state['sentiment_df']

    # Resample data
    interval_dict = {'1d': 'D', '1wk': '7D', '1mo': 'M', '3mo': '3M'}
    stock_resampled = stock_df['Close'].resample(interval_dict[interval]).last()
    sentiment_resampled = sentiment_df['numerical_sentiment'].resample(interval_dict[interval]).mean()

    # Calculate percentage change manually
    stock_resampled = stock_resampled.to_frame()
    stock_resampled['Percent Change'] = stock_resampled['Close'].diff() / stock_resampled['Close'].shift(1) * 100

    # Align sentiment data with stock data
    sentiment_resampled = sentiment_resampled.to_frame(name='numerical_sentiment')
    if interval == '1wk' and sentiment_resampled.index[0] != stock_resampled.index[0]:
        # Adjust sentiment dates to align with stock data
        date_difference = stock_resampled.index.min() - sentiment_resampled.index.min()
        sentiment_resampled.index += date_difference

    # Merge datasets
    merged_data = stock_resampled.reset_index().merge(
        sentiment_resampled.reset_index(),
        on='Date',
        how='inner'
    )

    # Add an option to show the table
    if st.checkbox("Show me the numbers", key='show_table'):
        # Add table for merged data
        st.write("Merged Data (Stock and Sentiment):")
        st.write(merged_data)


    # Scatter Plot: Sentiment vs Stock Price Change
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
    scatter_fig.update_layout(
        xaxis=dict(
            title='Sentiment Score',
            zeroline=True,
            zerolinecolor='black',
            showgrid=True,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='Stock Price Change (%)',
            zeroline=True,
            zerolinecolor='black',
            showgrid=True,
            gridcolor='lightgray'
        ),
    )
    st.plotly_chart(scatter_fig)

# Calculate percentage changes for sentiment and price
    merged_data['Sentiment Change'] = merged_data['numerical_sentiment'].pct_change() * 100
    merged_data['Price Change'] = merged_data['Close'].pct_change() * 100

    # Melt data for side-by-side bar chart
    bar_data = merged_data.melt(
        id_vars='Date',
        value_vars=['Sentiment Change', 'Price Change'],
        var_name='Metric',
        value_name='Change Percentage'
    )

    # Add a column for conditional colors
    def assign_color(row):
        if row['Metric'] == 'Sentiment Change':
            return 'red' if row['Change Percentage'] < 0 else 'lightgreen'
        elif row['Metric'] == 'Price Change':
            return 'blue' if row['Change Percentage'] < 0 else 'lightblue'

    bar_data['Color'] = bar_data.apply(assign_color, axis=1)

    # Side-by-Side Line Plot for Sentiment Change vs Price Change
    fig = make_subplots(
        rows=1, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.3,
        subplot_titles=[f"{ticker} Sentiment vs Stock Price Change"],
        specs=[[{'secondary_y': True}]]  # Enable secondary y-axis
    )

    # Add Sentiment Change bars (Primary Y-Axis)
    sentiment_data = bar_data[bar_data['Metric'] == 'Sentiment Change']
    fig.add_trace(
        go.Bar(
            x=sentiment_data['Date'],
            y=sentiment_data['Change Percentage'],
            name='Sentiment Change',
            marker=dict(color=sentiment_data['Color'])
        ),
        secondary_y=False  # Attach to the primary y-axis
    )

    # Add Price Change line plot (Secondary Y-Axis)
    price_data = bar_data[bar_data['Metric'] == 'Price Change']
    fig.add_trace(
        go.Scatter(
            x=price_data['Date'],
            y=price_data['Change Percentage'],
            name='Stock Price Change',
            mode='lines+markers',  # Display as a line with markers
            line=dict(color='purple'),  # Choose a color for the line
            marker=dict(color='purple')  # Choose a color for the markers
        ),
        secondary_y=True  # Attach to the secondary y-axis
    )

    # Update layout for dual axes
    fig.update_layout(
        title=f"{ticker} Sentiment vs Stock Price Change",
        xaxis_title='Date',
        yaxis=dict(
            title='Sentiment Change (%)',
            range=[-100, 100]  # Adjust based on sentiment data scale
        ),
        yaxis2=dict(
            title='Stock Price Change (%)',
            overlaying='y',  # Share the same x-axis
            side='right',    # Position the axis on the right
            range=[-10, 10]  # Adjust based on price data scale
        ),
        barmode='group',  # Bars are still grouped but line plot is overlaid
        bargap=0.2,       # Adjust gap between bars
        legend=dict(
                    x=0.5,  # Horizontal position (0 = left, 1 = right)
                    y=-0.3,  # Vertical position (negative values place it below the chart)
                    xanchor='center',  # Center align horizontally
                    yanchor='top',  # Align to the top vertically
                    orientation='h',  # Horizontal layout
                    bgcolor='rgba(255,255,255,0.5)',  # Semi-transparent background
                    bordercolor='gray',  # Optional: Add border
                    borderwidth=1  # Optional: Border thickness
                )
    )

    # Render the chart in Streamlit
    st.plotly_chart(fig)




# ------------------------------
    # Category selection and filtering
# Category selection and filtering with stock data
    if 'Real_Label' in sentiment_df.columns:
        categories = [category for category in sentiment_df['Real_Label'].unique() if category != 'Other.']
        categories.insert(0, 'Select a category')
        # categories = sentiment_df['Real_Label'].unique()
        selected_category = st.selectbox("Filter by Tweet Category:", options=categories, key='category_selection')

        if selected_category and selected_category != 'Select a category':
            # Filter sentiment data for the selected category
            filtered_sentiment = sentiment_df[sentiment_df['Real_Label'] == selected_category]
            category_counts = filtered_sentiment.resample(interval_dict[interval]).size()

            category_data = category_counts.to_frame(name='Tweet Counts')

            # Merge the dataframes using an outer join (keep all dates)
            combined_data = stock_resampled.merge(
                category_data,
                left_index=True,
                right_index=True,
                how='outer'
            )

            # Perform linear interpolation to fill missing stock prices
            combined_data['Close'] = combined_data['Close'].interpolate(method='linear',limit_direction = 'both')

            # Fill missing tweet counts with 0
            combined_data = combined_data.fillna(0)

            # Now, `combined_data` will have interpolated stock prices in a straight line



            # Plot the combined data
            fig = make_subplots(
                rows=1, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.3,
                specs=[[{'secondary_y': True}]]
            )

            # Add stock price line (primary y-axis)
            fig.add_trace(
                go.Scatter(
                    x=combined_data.index,
                    y=combined_data['Close'],
                    mode='lines',
                    name='Stock Price',
                    line=dict(color='blue'),
                    yaxis='y1'
                ),
                secondary_y=False
            )

            # Add tweet counts bar (secondary y-axis)
            fig.add_trace(
                go.Bar(
                    x=combined_data.index,
                    y=combined_data['Tweet Counts'],
                    name=f"Tweet Counts ({selected_category})",
                    marker_color='grey',
                    opacity=0.6,
                    yaxis='y2'
                ),
                secondary_y=True
            )

            # Customize layout
            fig.update_layout(
                title=f"Stock Price and Tweet Counts for {selected_category}",
                xaxis=dict(title='Date'),
                yaxis=dict(
                    title='Stock Price',
                    side='left'
                ),
                yaxis2=dict(
                    title='Tweet Counts',
                    side='right',
                    overlaying='y',
                    showgrid=False
                ),
                legend=dict(
                    x=0.5,  # Horizontal position (0 = left, 1 = right)
                    y=-0.3,  # Vertical position (negative values place it below the chart)
                    xanchor='center',  # Center align horizontally
                    yanchor='top',  # Align to the top vertically
                    orientation='h',  # Horizontal layout
                    bgcolor='rgba(255,255,255,0.5)',  # Semi-transparent background
                    bordercolor='gray',  # Optional: Add border
                    borderwidth=1  # Optional: Border thickness
                ),
                barmode='overlay'  # Ensure bars are slightly transparent and overlaid
            )

            # Display the combined chart
            st.plotly_chart(fig)
        else:
            st.info("Please select a category to display the graph showing volume of tweets in the selected category (and stock price) over time.")
    else:
        st.warning("Category data (Real_Label) is not available.")
params = {'ticker_symbol': ticker, 'start_date': start_date, 'end_date': end_date}
if st.button('Select random tweets'):
    tweet_data = requests.get(tweet_url, params=params).json()
    tweet_df = pd.DataFrame(tweet_data)
    st.write(tweet_df)
