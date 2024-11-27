import streamlit as st
import pandas as pd
import sys
import os
import requests

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


            # Display result or error
            if isinstance(data, str):  # If the function returns an error message
                st.error(data)
            else:
                # Ensure 'Date' is a datetime index
                data = pd.DataFrame(data)
                data['Date'] = pd.to_datetime(data['Date'], utc=True)  # Explicitly set UTC to avoid timezone warnings
                data.set_index('Date', inplace=True)
            #     # Resample the data to end of each month and pick the last closing price
                monthly_data = data['Close'].resample('M').last()

            #     # Create a new DataFrame for Streamlit
                chart_data = pd.DataFrame({
                    'Month-Year': monthly_data.index.strftime('%Y-%m'),  # Format as Month-Year
                    'Close': monthly_data.values
                })

            #     # Set 'Month-Year' as the index
                chart_data.set_index('Month-Year', inplace=True)

            #     # Plot the line chart
                st.line_chart(chart_data)
