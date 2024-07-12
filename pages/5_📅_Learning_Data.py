# Leaderboard.py
import streamlit as st
import pandas as pd
from data_processing import finalize_data

# Set the title and favicon for the Browser's tab bar.
st.set_page_config(
    page_title='Learning Data',
    page_icon=':calendar:',  # This is an emoji shortcode. Could be a URL too.
)

# Add logo and title above sidebar
st.logo('kognisi_logo.png')

# Fetch the data
merged_df, df_combined_mysql, df_sap = finalize_data()

print(merged_df['last_updated'].apply(type).value_counts())

if st.button("Reload Data"):
    # Clear values from *all* all in-memory and on-disk data caches:
    st.cache_resource.clear()
    st.cache_data.clear()