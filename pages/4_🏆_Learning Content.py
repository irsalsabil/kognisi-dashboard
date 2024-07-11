# Leaderboard.py
import streamlit as st
import pandas as pd
from data_processing import finalize_data

# Set the title and favicon for the Browser's tab bar.
st.set_page_config(
    page_title='Top Contents',
    page_icon=':trophy:',  # This is an emoji shortcode. Could be a URL too.
)

# Add logo and title above sidebar
st.logo('kognisi_logo.png')

# Fetch the data
merged_df, df_combined_mysql, df_sap = finalize_data()

# Sidebar: Add a selectbox for unit filter
st.sidebar.markdown('### Unit Filter')
unit_list = ['All'] + list(df_sap['unit'].unique())
selected_unit = st.sidebar.selectbox('Select Unit:', unit_list)

# Apply unit filter id a specific unit is selected
if selected_unit != 'All':
    df_sap = df_sap[df_sap['unit'] == selected_unit]
    merged_df = merged_df[merged_df['unit'] == selected_unit]

# Sidebar: Add a selectbox for type filter
st.sidebar.markdown('### Type Filter')
type_list = ['All'] + list(merged_df['type'].unique())  # Replace 'type' with the actual column name
selected_type = st.sidebar.selectbox('Select Type:', type_list)

# Apply type filter if a specific type is selected
if selected_type != 'All':
    merged_df = merged_df[merged_df['type'] == selected_type]

# Set the title of the page
st.markdown('''
# :trophy: Top Contents

This page shows the leaderboard of 10 learning contents with most learners.
''')

# Create date filter for end_date
min_value = merged_df['last_updated'].min()
max_value = merged_df['last_updated'].max()

# Add a date input widget to filter the date range
from_date, to_date = st.date_input(
    'Choose a period of date',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value],
    format="YYYY-MM-DD"
)

# Filter the data based on the selected date range
filtered_df = merged_df[
    (merged_df['last_updated'] <= to_date) & (merged_df['last_updated'] >= from_date)
]

# Calculate the leaderboard data based on the filtered data
leaderboard = filtered_df.groupby('title')['count AL'].nunique().reset_index()
leaderboard.columns = ['Title', 'Learners']
leaderboard = leaderboard.sort_values(by='Learners', ascending=False).reset_index(drop=True)

# Select only the top 10 most-watched videos
leaderboard = leaderboard.head(10)

# Add ranking column starting from 1 to 10
leaderboard['Rank'] = leaderboard.index + 1

# Rearrange columns to show rank first
leaderboard = leaderboard[['Rank', 'Title', 'Learners']]

# Display the leaderboard table without index
st.table(leaderboard.set_index('Rank'))
