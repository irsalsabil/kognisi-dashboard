import pandas as pd
from fetch_data import fetch_data_mykg, fetch_data_discovery, fetch_data_sap

def finalize_data():
    # Fetch data from both MyKG and Discovery databases
    df_mykg = fetch_data_mykg()
    df_discovery = fetch_data_discovery()

    # Combine the data from both MyKG and Discovery databases
    df_combined_mysql = pd.concat([df_mykg, df_discovery], ignore_index=True)

    # Define the columns to be selected from the SAP Google Sheet
    selected_columns = ['email', 'nik', 'unit', 'subunit', 'layer', 'division', 'position']  # Replace with actual column names you need

    # Fetch data from SAP with selected columns
    df_sap = fetch_data_sap(selected_columns)

    # Ensure email columns are consistent: trim spaces and convert to lowercase
    df_combined_mysql['email'] = df_combined_mysql['email'].str.strip().str.lower()
    df_sap['email'] = df_sap['email'].str.strip().str.lower()

    # Merge data from combined MySQL and SAP based on email
    merged_df = pd.merge(df_combined_mysql, df_sap, on='email', how='left', indicator=True)

    # Add a new column to label each row as 'internal' or 'external'
    merged_df['status'] = merged_df['_merge'].apply(lambda x: 'Internal' if x == 'both' else 'External')

    # Drop the _merge column as it's no longer needed
    merged_df.drop(columns=['_merge'], inplace=True)
    
    # Convert last_update to timestamp then extract the date
    merged_df['last_updated'] = pd.to_datetime(merged_df['last_updated'], errors='coerce').dt.date

    return merged_df, df_combined_mysql, df_sap