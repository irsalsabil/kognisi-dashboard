import streamlit as st
import pandas as pd
import pymysql
from sshtunnel import SSHTunnelForwarder
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Function to connect to MyKG via SSH tunnel and fetch data
def fetch_data_mykg():
    try:
        private_key_path = st.secrets["ssh"]["private_key_path"]

        with open(private_key_path, 'r') as key_file:
            private_key_content = key_file.read()

        with SSHTunnelForwarder(
            (st.secrets["ssh"]["host"], st.secrets["ssh"]["port"]),
            ssh_username=st.secrets["ssh"]["username"],
            ssh_pkey=private_key_path,
            ssh_private_key_password=st.secrets["ssh"].get("private_key_passphrase"),
            remote_bind_address=(st.secrets["mykg"]["host"], st.secrets["mykg"]["port"])
        ) as tunnel:
            connection_kwargs = {
                'host': '127.0.0.1',
                'port': tunnel.local_bind_port if tunnel.is_active else st.secrets["mykg"]["port"],
                'user': st.secrets["mykg"]["user"],
                'password': st.secrets["mykg"]["password"],
                'database': st.secrets["mykg"]["database"],
                'cursorclass': pymysql.cursors.DictCursor,
            }
            conn = pymysql.connect(**connection_kwargs)

            with open('query_mykg.sql', 'r') as sql_file:
                query = sql_file.read()

            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"An error occurred while fetching data from MyKG: {e}")
        return pd.DataFrame()

# Function to connect to Discovery directly and fetch data
def fetch_data_discovery():
    try:
        connection_kwargs = {
            'host': st.secrets["discovery"]["host"],
            'port': st.secrets["discovery"]["port"],
            'user': st.secrets["discovery"]["user"],
            'password': st.secrets["discovery"]["password"],
            'database': st.secrets["discovery"]["database"],
            'cursorclass': pymysql.cursors.DictCursor,
        }
        conn = pymysql.connect(**connection_kwargs)

        with open('query_discovery.sql', 'r') as sql_file:
            query = sql_file.read()

        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"An error occurred while fetching data from Discovery: {e}")
        return pd.DataFrame()

# Function to fetch data from SAP with selected columns
def fetch_data_sap(selected_columns):
    creds_path = st.secrets["sap"]["json_keyfile"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('0. Active Employee - Monthly Updated')
    sheet = spreadsheet.sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df[selected_columns]