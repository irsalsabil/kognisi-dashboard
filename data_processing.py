import streamlit as st
import pandas as pd
from fetch_data import fetch_data_mykg, fetch_data_mykg_i, fetch_data_id, fetch_data_discovery, fetch_data_capture, fetch_data_offplatform, fetch_data_sap, fetch_data_clel

@st.cache_data(ttl=86400)
def fetch_combined_data():
    # Combine data from multiple sources in a single function
    df_mykg = fetch_data_mykg()
    df_mykg_i = fetch_data_mykg_i()
    df_id = fetch_data_id()
    df_discovery = fetch_data_discovery()
    df_capture = fetch_data_capture()
    df_offplatform = fetch_data_offplatform()
    df_combined_mysql = pd.concat([df_mykg, df_mykg_i, df_id, df_discovery, df_capture, df_offplatform], ignore_index=True)

    # Clean email and nik columns efficiently
    df_combined_mysql['email'] = df_combined_mysql['email'].str.strip().str.lower()
    #df_combined_mysql['nik'] = df_combined_mysql['nik'].astype(str).str.zfill(6)
    df_combined_mysql['nik'] = df_combined_mysql['nik'].astype(str)
    df_combined_mysql['nik'] = df_combined_mysql['nik'].str.replace('.0', '', regex=False).str.zfill(6)
    df_combined_mysql['duration'] = df_combined_mysql['duration'].apply(lambda x: int(float(x)) if pd.notnull(x) else None)


    return df_combined_mysql

def clean_sap_data(df_sap):
    df_sap['email'] = df_sap['email'].str.strip().str.lower()
    df_sap['nik'] = df_sap['nik'].astype(str).str.zfill(6)
    return df_sap

def lookup_nik(df_combined_mysql, df_sap):
    # Create email-to-nik mapping dictionary
    email_to_nik = dict(zip(df_sap['email'], df_sap['nik']))

    # Use vectorized operations for the lookup
    nik_match = df_combined_mysql['nik'].isin(df_sap['nik'])
    email_match = df_combined_mysql['email'].map(email_to_nik).notna()
    df_combined_mysql.loc[nik_match, 'count AL'] = df_combined_mysql.loc[nik_match, 'nik']
    df_combined_mysql.loc[~nik_match & email_match, 'count AL'] = df_combined_mysql.loc[~nik_match & email_match, 'email'].map(email_to_nik)
    df_combined_mysql.loc[~nik_match & ~email_match, 'count AL'] = df_combined_mysql.loc[~nik_match & ~email_match, 'email']

    return df_combined_mysql['count AL']

@st.cache_data(ttl=86400)
def finalize_data():
    # Fetch combined data from MySQL sources
    df_combined_mysql = fetch_combined_data()

    # Fetch SAP data with selected columns
    selected_columns = ['name_sap', 'email', 'nik', 'unit', 'subunit', 'admin_hr', 'layer', 'generation', 'gender', 'division', 'department']
    df_sap = fetch_data_sap(selected_columns)
    df_sap = clean_sap_data(df_sap)

    # Apply lookup function to each row
    df_combined_mysql['count AL'] = lookup_nik(df_combined_mysql, df_sap).astype(str)

    # Convert and filter last_updated column
    if 'last_updated' in df_combined_mysql.columns:
        df_combined_mysql['last_updated'] = pd.to_datetime(df_combined_mysql['last_updated'], errors='coerce').dt.date
        df_combined_mysql = df_combined_mysql.dropna(subset=['last_updated'])

    # Merge combined MySQL data with SAP data
    merged_df = pd.merge(df_combined_mysql, df_sap, left_on='count AL', right_on='nik', how='left', indicator=True)
    merged_df['status'] = merged_df['_merge'].apply(lambda x: 'Internal' if x == 'both' else 'External')
    merged_df.drop(columns=['_merge'], inplace=True)

    # Right join to include all rows from df_sap
    right_merged_df = pd.merge(df_combined_mysql, df_sap, left_on='count AL', right_on='nik', how='right', indicator=True)
    right_merged_df['status'] = right_merged_df['_merge'].apply(lambda x: 'Active' if x == 'both' else 'Passive')
    right_merged_df.drop(columns=['_merge'], inplace=True)

    return merged_df, df_combined_mysql, df_sap, right_merged_df

@st.cache_data(ttl=86400)
def finalize_data_clel():
    # Fetch data from CL EL
    df_clel = fetch_data_clel()

    return df_clel
