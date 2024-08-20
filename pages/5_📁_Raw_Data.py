import streamlit as st
import pandas as pd
from data_processing import finalize_data

# Set the title and favicon for the Browser's tab bar.
st.set_page_config(
    page_title='Raw Data',
    page_icon=':file_folder:',  # This is an emoji shortcode. Could be a URL too.
)

# Add logo and title above sidebar
st.logo('kognisi_logo.png')

# Fetch the data
merged_df, df_combined_mysql, df_sap, right_merged_df = finalize_data()

# Filter the DataFrame for 'Active' status and sort by 'last_updated' descending
#merged_df = merged_df.sort_values(by='last_updated', ascending=False)

# Create date filter for last_updated
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

# Sidebar: Add a selectbox for unit filter
st.sidebar.markdown('### Unit Filter')
unit_list = ['All'] + list(merged_df['unit'].unique())
selected_unit = st.sidebar.selectbox('Select Unit:', unit_list)

if selected_unit != 'All':
    merged_df = merged_df[merged_df['unit'] == selected_unit]

subunit_list = list(merged_df['subunit'].unique())
selected_subunit = st.sidebar.multiselect('Select Subunit:', subunit_list, default=[])

if selected_subunit:
    merged_df = merged_df[merged_df['subunit'].isin(selected_subunit)]

adminhr_list = list(merged_df['admin_hr'].unique())
selected_adminhr = st.sidebar.multiselect('Select Admin for HR:', adminhr_list, default=[])

if selected_adminhr:
    merged_df = merged_df[merged_df['admin_hr'].isin(selected_adminhr)]

division_list = list(merged_df['division'].unique())
selected_division = st.sidebar.multiselect('Select Division:', adminhr_list, default=[])

if selected_division:
    merged_df = merged_df[merged_df['division'].isin(selected_division)]

# Sidebar: Add a selectbox for title filter
st.sidebar.markdown('### Title Filter')
title_list = list(merged_df['title'].unique())
selected_title = st.sidebar.multiselect('Select Title:', title_list, default=[])

if selected_title:
    merged_df = merged_df[merged_df['title'].isin(selected_title)]

# Sidebar: Add a selectbox for title filter
st.sidebar.markdown('### Learner Filter')
name_list = list(merged_df['name'].unique())
selected_name = st.sidebar.multiselect('Select Name:', name_list, default=[])

if selected_name:
    merged_df = merged_df[merged_df['name'].isin(selected_name)]

nik_list = list(merged_df['count AL'].unique())
selected_nik = st.sidebar.multiselect('Select NIK:', nik_list, default=[])

if selected_nik:
    merged_df = merged_df[merged_df['count AL'].isin(selected_nik)]

# Process merged_df
merged_df.drop(['name_sap', 'email_y', 'nik_x', 'nik_y', 'layer', 'generation', 'gender', 'department', 'status'], axis=1, inplace=True)

# Display the raw data
st.header('Raw Data', divider='gray')

# Display dataframe
st.dataframe(merged_df)

# Update Data
st.divider()
st.markdown('''
_This app is using data cache for performance optimization, you can reload the data by clicking the button below then press 'R' on keyboard or refresh the page._
''')
if st.button("Update Data"):
    # Clear values from *all* all in-memory and on-disk data caches:
    st.cache_resource.clear()
    st.cache_data.clear()