import pandas as pd
import streamlit as st
import altair as alt
from data_processing import finalize_data, finalize_data_clel
import datetime

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Kognisi Learners',
    page_icon=':bar_chart:',  # This is an emoji shortcode. Could be a URL too.
)

# Return data from data_processing
merged_df, df_combined_mysql, df_sap, right_merged_df = finalize_data()
df_clel = finalize_data_clel()

# Add logo and title above sidebar
st.logo('kognisi_logo.png')

# Set the title that appears at the top of the page.
st.markdown('''
# :bar_chart: Kognisi Learners

Under the term Kognisi Learners, there are several metrics, including:
1. **Active Learners:** users who have accessed at least one content in one platform
2. **Collaborative Learners:** active learners who also teach at least one learning content
3. **Exponential Learner:** active learners who teach more than one learning content
''')

# Add some spacing
st.markdown('''

''')

# Sidebar: Add a selectbox for unit filter
#st.sidebar.markdown('### Learner Filter')
#learner_list = ['All'] + list(merged_df['status'].unique())
#selected_learner = st.sidebar.selectbox('Select Learner:', learner_list)

#if selected_learner != 'All':
#    merged_df = merged_df[merged_df['status'] == selected_learner]

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

# Active Learners section
st.header('Active Learners', divider='gray')

# Calculate the distinct counts of the count AL column
total_count = filtered_df['count AL'].nunique()
internal_count = filtered_df[filtered_df['status'] == 'Internal']['count AL'].nunique()
external_count = filtered_df[filtered_df['status'] == 'External']['count AL'].nunique()

# Display metrics column
col1, col2, col3 = st.columns(3)
col1.metric("Overall", total_count)
col2.metric("Internal", internal_count)
col3.metric("External", external_count)

# Platform Distribution
st.subheader('Platform Distribution', divider='gray')

# Group by platform and status, and count unique count ALs
platform_counts = filtered_df.groupby(['platform', 'status'])['count AL'].nunique().reset_index()
platform_counts.columns = ['platform', 'status', 'learners']

# Create Altair bar chart with internal and external status
chart = alt.Chart(platform_counts).mark_bar().encode(
    x=alt.X('platform', sort='-y', axis=alt.Axis(title='Platform')),
    y=alt.Y('learners', axis=alt.Axis(title='Active Learners')),
    color=alt.Color('status', scale=alt.Scale(domain=['Internal', 'External'], range=['#1f77b4', '#ff7f0e'])),
    tooltip=['platform', 'status', 'learners']
).properties(
    width=alt.Step(80)  # Adjust width as needed
)

# Display the chart using Streamlit
st.altair_chart(chart, use_container_width=True)

# Add some spacing
st.markdown('''

''')

# Collaborative & Exponential Learners section
st.header('Collaborative & Exponential Learners Trend 2024', divider='gray')

# Identify columns to keep: id_instructor and columns starting with 'EL/CL'
columns_to_keep = ['id_instructor'] + [col for col in df_clel.columns if col.startswith('EL/CL')]
df_clel = df_clel[columns_to_keep]

# Melt the DataFrame to long format
df_melted = df_clel.melt(id_vars=['id_instructor'], var_name='month', value_name='value')

# Rename the month columns to be more readable
df_melted['month'] = df_melted['month'].str.replace('EL/CL ', '')

# Count unique IDs for each value per month
count_data = df_melted.groupby(['month', 'value']).agg({'id_instructor': pd.Series.nunique}).reset_index()
count_data.rename(columns={'id_instructor': 'unique_count'}, inplace=True)

# Filter only EL and CL values
count_data = count_data[count_data['value'].isin(['EL', 'CL'])]

# Define a list of months in order
standard_months = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']

# Identify months present in the data
present_months = count_data['month'].unique()

# Combine standard months with any new months found in the data
month_order = [month for month in standard_months if month in present_months] + \
              [month for month in present_months if month not in standard_months]

# Ensure the month is categorical and in the specified order
count_data['month'] = pd.Categorical(count_data['month'], categories=month_order, ordered=True)
count_data = count_data.sort_values(by='month')

# Create the chart using Altair
chart = alt.Chart(count_data).mark_bar().encode(
    x=alt.X('month', sort=None, axis=alt.Axis(title='Month')),
    y=alt.Y('unique_count', axis=alt.Axis(title='Count')),
    color=alt.Color('value:N', scale=alt.Scale(domain=['CL', 'EL'], range=['#ADD8E6', '#40E0D0'])),  # Light Blue and Turquoise Green
    order=alt.Order('value:N', sort='ascending'),
    tooltip=['month', 'value', 'unique_count']
).properties(
    width=alt.Step(80)  # Adjust width as needed
)

st.altair_chart(chart, use_container_width=True)


# Update Data
st.divider()
st.markdown('''
_This app is using data cache for performance optimization, you can reload the data by clicking the button below then press 'R' on keyboard or refresh the page._
''')
if st.button("Update Data"):
    # Clear values from *all* all in-memory and on-disk data caches:
    st.cache_resource.clear()
    st.cache_data.clear()