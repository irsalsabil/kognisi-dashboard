import streamlit as st
import pandas as pd
import pymysql
from sshtunnel import SSHTunnelForwarder
import paramiko
from io import StringIO
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import toml

# Function to connect to MyKG via SSH tunnel and fetch data
@st.cache_resource(ttl=86400)
def fetch_data_mykg():
    try:
        # Load the private key content from secrets
        private_key_content = st.secrets["key_mykg"]["id_rsa_streamlit"]
        private_key_passphrase = st.secrets["ssh_mykg"].get("private_key_passphrase")
        
        # Create an RSA key object from the private key content
        private_key_file = StringIO(private_key_content)
        private_key = paramiko.RSAKey.from_private_key(private_key_file, password=private_key_passphrase)
        
        with SSHTunnelForwarder(
            (st.secrets["ssh_mykg"]["host"], st.secrets["ssh_mykg"]["port"]),
            ssh_username=st.secrets["ssh_mykg"]["username"],
            ssh_pkey=private_key,
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

# Function to connect to ID via SSH tunnel and fetch data
@st.cache_resource(ttl=86400)
def fetch_data_id():
    try:
        # Load the private key content from secrets for ID
        private_key_content = st.secrets["key_id"]["id_rsa_streamlit"]
        private_key_passphrase = st.secrets["ssh_id"].get("private_key_passphrase")
        
        # Create an RSA key object from the private key content for ID
        private_key_file = StringIO(private_key_content)
        private_key = paramiko.RSAKey.from_private_key(private_key_file, password=private_key_passphrase)

        with SSHTunnelForwarder(
            (st.secrets["ssh_id"]["host"], st.secrets["ssh_id"]["port"]),
            ssh_username=st.secrets["ssh_id"]["username"],
            ssh_pkey=private_key,
            remote_bind_address=(st.secrets["id"]["host"], st.secrets["id"]["port"]),
        ) as tunnel:
            connection_kwargs = {
                'host': '127.0.0.1',
                'port': tunnel.local_bind_port if tunnel.is_active else st.secrets["id"]["port"],
                'user': st.secrets["id"]["user"],
                'password': st.secrets["id"]["password"],
                'database': st.secrets["id"]["database"],
                'cursorclass': pymysql.cursors.DictCursor,
            }
            conn = pymysql.connect(**connection_kwargs)

            with open('query_id.sql', 'r') as sql_file:
                query = sql_file.read()

            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"An error occurred while fetching data from ID: {e}")
        return pd.DataFrame()

# Function to connect to Discovery directly and fetch data
@st.cache_resource(ttl=86400)
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

# Function to fetch data from Capture data
@st.cache_resource(ttl=86400)
def fetch_data_capture():
    secret_info = st.secrets["json_sap"]    #  Using the same service account as SAP
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('0. Data Capture - Monthly Updated')
    sheet = spreadsheet.sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# Function to fetch data from OutsidePlatform data
@st.cache_resource(ttl=86400)
def fetch_data_offplatform():
    secret_info = st.secrets["json_sap"]    #  Using the same service account as SAP
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('0. Data Outside Platform')
    sheet = spreadsheet.sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# Function to fetch data from SAP with selected columns
@st.cache_resource(ttl=86400)
def fetch_data_sap(selected_columns):
    secret_info = st.secrets["json_sap"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('0. Active Employee - Monthly Updated')
    sheet = spreadsheet.sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df[selected_columns]

# Function to fetch data from Collaborative & Exponential
@st.cache_resource(ttl=86400)
def fetch_data_clel():
    secret_info = st.secrets["json_sap"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('0. Collaborative & Exponential Learners - Monthly Updated')
    sheet = spreadsheet.sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df