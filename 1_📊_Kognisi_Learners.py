import pandas as pd
import streamlit as st
import altair as alt
from data_processing import finalize_data

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Kognisi Learners',
    page_icon=':bar_chart:',  # This is an emoji shortcode. Could be a URL too.
)

# Return data from data_processing
merged_df, df_combined_mysql, df_sap = finalize_data()

# Add logo and title above sidebar
st.logo('kognisi_logo.png')

# Set the title that appears at the top of the page.
st.markdown('''
# :bar_chart: Kognisi Learners

Under the term Kognisi Learners, there are several metrics, including:
1. Active Learners: users who have accessed at least one content in one platform
2. Collaborative Learners: active learners who also teach at least one learning content
3. Exponential Learner: active learners who teach more than one learning content
''')

# Add some spacing
st.markdown('''

''')

# Active Learners section
st.header('Active Learners', divider='gray')

# Create date filter for end_date
min_value = merged_df['last_updated'].min()
max_value = merged_df['last_updated'].max()

from_date, to_date = st.date_input(
    'Choose a periode of date',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value],
    format="YYYY-MM-DD"
)

# Filter the data based on the selected date range
filtered_df = merged_df[
    (merged_df['last_updated'] <= to_date) & (merged_df['last_updated'] >= from_date)
]

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

# Group by platform and count unique count ALs
platform_counts = filtered_df.groupby('platform')['count AL'].nunique().reset_index()
platform_counts.columns = ['platform', 'unique_count AL_count']

# Create Altair bar chart
# st.title('Platform Distribution based on Unique count ALs')
chart = alt.Chart(platform_counts).mark_bar().encode(
    x=alt.X('platform', sort='-y', axis=alt.Axis(title='Platform')),
    y=alt.Y('unique_count AL_count', axis=alt.Axis(title='Active Learners')),
    tooltip=['platform', 'unique_count AL_count']
).properties(
    width=alt.Step(80)  # Adjust width as needed
)

# Display the chart using Streamlit
st.altair_chart(chart, use_container_width=True)

# Add some spacing
st.markdown('''

''')

# Collaborative Learners section
st.header('Collaborative Learners', divider='gray')
st.markdown('''Work in Progress''')

# Add some spacing
st.markdown('''

''')

# Exponential Learners section
st.header('Exponential Learners', divider='gray')
st.markdown('''Work in Progress''')