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
merged_df, df_combined_mysql, df_sap, right_merged_df = finalize_data()

# Sidebar: Add a selectbox for unit filter
st.sidebar.markdown('### Unit Filter')
unit_list = ['All'] + list(df_sap['unit'].unique())
selected_unit = st.sidebar.selectbox('Select Unit:', unit_list)

if selected_unit != 'All':
    df_sap = df_sap[df_sap['unit'] == selected_unit]
    merged_df = merged_df[merged_df['unit'] == selected_unit]

subunit_list = list(df_sap['subunit'].unique())
selected_subunit = st.sidebar.multiselect('Select Subunit:', subunit_list, default=[])

if selected_subunit:
    df_sap = df_sap[df_sap['subunit'].isin(selected_subunit)]
    merged_df = merged_df[merged_df['subunit'].isin(selected_subunit)]

adminhr_list = list(df_sap['admin_hr'].unique())
selected_adminhr = st.sidebar.multiselect('Select Admin for HR:', adminhr_list, default=[])

if selected_adminhr:
    df_sap = df_sap[df_sap['admin_hr'].isin(selected_adminhr)]
    merged_df = merged_df[merged_df['admin_hr'].isin(selected_adminhr)]

division_list = list(df_sap['division'].unique())
selected_division = st.sidebar.multiselect('Select Division:', adminhr_list, default=[])

if selected_division:
    df_sap = df_sap[df_sap['division'].isin(selected_division)]
    merged_df = merged_df[merged_df['division'].isin(selected_division)]

# Sidebar: Add a selectbox for type filter
st.sidebar.markdown('### Content Filter')
platform_list = ['All'] + list(merged_df['platform'].unique())  # Replace 'type' with the actual column name
selected_platform = st.sidebar.selectbox('Select Platform:', platform_list)

# Apply type filter if a specific type is selected
if selected_platform != 'All':
    merged_df = merged_df[merged_df['platform'] == selected_platform]

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

# Default date range
from_date = min_value
to_date = max_value

# Create columns for buttons
st.write("**Choose the data period:**")
col1, col2, col3 = st.columns(3)

# Create buttons for shortcut filters in a single line
with col1:
    if st.button('Lifetime'):
        from_date = min_value
        to_date = max_value

with col2:
    if st.button('This Year'):
        current_year = datetime.datetime.now().year
        from_date = datetime.date(current_year, 1, 1)
        to_date = datetime.datetime.now().date()

with col3:
    if st.button('This Month'):
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month
        from_date = datetime.date(current_year, current_month, 1)
        to_date = datetime.datetime.now().date()

# Allow manual date input as well
from_date, to_date = st.date_input(
    '**Or pick the date manually:**',
    value=[from_date, to_date],
    min_value=min_value,
    max_value=max_value,
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

# Update Data
st.divider()
st.markdown('''
_This app is using data cache for performance optimization, you can reload the data by clicking the button below then press 'R' on keyboard or refresh the page._
''')
if st.button("Update Data"):
    # Clear values from *all* all in-memory and on-disk data caches:
    st.cache_resource.clear()
    st.cache_data.clear()
