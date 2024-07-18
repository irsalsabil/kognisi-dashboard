import streamlit as st
import pandas as pd
from fetch_data import fetch_data_mykg, fetch_data_id, fetch_data_discovery, fetch_data_capture, fetch_data_offplatform, fetch_data_sap

@st.cache_data
def finalize_data():
    # Fetch data from both MyKG, ID, Discovery, Capture databases
    df_mykg = fetch_data_mykg()
    df_id = fetch_data_id()
    df_discovery = fetch_data_discovery()
    df_capture = fetch_data_capture()
    df_offplatform = fetch_data_offplatform()

    # Combine the data from both MyKG, ID, Discovery, Capture databases
    df_combined_mysql = pd.concat([df_mykg, df_id, df_discovery, df_capture, df_offplatform], ignore_index=True)

    # Define the columns to be selected from the SAP Google Sheet
    selected_columns = ['name_sap','email', 'nik', 'unit', 'subunit', 'admin_hr', 'layer', 'generation', 'gender', 'division', 'department']  # Adjust as needed

    # Fetch data from SAP with selected columns
    df_sap = fetch_data_sap(selected_columns)

    # Ensure email columns are consistent: trim spaces and convert to lowercase
    df_combined_mysql['email'] = df_combined_mysql['email'].str.strip().str.lower()
    df_sap['email'] = df_sap['email'].str.strip().str.lower()

    # Ensure nik columns are strings and pad with leading zeros to ensure 6 digits
    df_combined_mysql['nik'] = df_combined_mysql['nik'].astype(str).str.zfill(6)
    df_sap['nik'] = df_sap['nik'].astype(str).str.zfill(6)

    # Create dictionaries from df_sap for quick lookup
    email_to_nik = dict(zip(df_sap['email'], df_sap['nik']))

    # Define a function to perform the lookup
    def lookup_nik(row):
        # Check by nik
        if row['nik'] in df_sap['nik'].values:
            return row['nik']
        
        # Check by email if nik lookup fails
        nik_from_email = email_to_nik.get(row['email'])
        if nik_from_email is not None:
            return nik_from_email
        
        # Return email if neither lookup succeeds
        return row['email']

    # Convert last_update to timestamp then extract the date
    if 'last_updated' in df_combined_mysql.columns:
        df_combined_mysql['last_updated'] = pd.to_datetime(df_combined_mysql['last_updated'], errors='coerce').dt.date

    # Filter out rows where 'last_updated' is NaT
    df_combined_mysql = df_combined_mysql.dropna(subset=['last_updated'])

    # Apply the lookup function to each row
    df_combined_mysql['count AL'] = df_combined_mysql.apply(lookup_nik, axis=1)

    # Ensure the 'count AL' column is string
    df_combined_mysql['count AL'] = df_combined_mysql['count AL'].astype(str)

    # Merge data from combined MySQL and SAP based on 'count AL' and 'nik'
    merged_df = pd.merge(df_combined_mysql, df_sap, left_on='count AL', right_on='nik', how='left', indicator=True)

    # Add a new column to label each row as 'internal' or 'external'
    merged_df['status'] = merged_df['_merge'].apply(lambda x: 'Internal' if x == 'both' else 'External')

    # Drop the _merge column as it's no longer needed
    merged_df.drop(columns=['_merge'], inplace=True)

    # Perform a right join to include all rows from df_sap
    right_merged_df = pd.merge(df_combined_mysql, df_sap, left_on='count AL', right_on='nik', how='right', indicator=True)

    # Add a new column to label each row as 'Active' or 'Passive'
    right_merged_df['status'] = right_merged_df['_merge'].apply(lambda x: 'Active' if x == 'both' else 'Passive')

    # Drop the _merge column as it's no longer needed
    right_merged_df.drop(columns=['_merge'], inplace=True)

    # Return the dataframes
    return merged_df, df_combined_mysql, df_sap, right_merged_df