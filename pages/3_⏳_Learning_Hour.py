import streamlit as st
import pandas as pd
import altair as alt
from data_processing import finalize_data
import datetime
import numpy as np

# Set the title and favicon for the browser's tab bar
st.set_page_config(page_title='Learning Hours', page_icon=':hourglass:')

# Add logo and title above the sidebar
st.logo('kognisi_logo.png')

# Fetch the data
merged_df, df_combined_mysql, df_sap, right_merged_df = finalize_data()

# Set the title that appears at the top of the page
st.markdown('''
            # :hourglass: Learning Hours
            
            This page provides insights into how many employees achieved the target learning hours per unit.
            ''')

# Sidebar: Unit filter
st.sidebar.markdown('### Unit Filter')
unit_list = ['All'] + list(df_sap['unit'].unique())
selected_unit = st.sidebar.selectbox('Select Unit:', unit_list)

if selected_unit != 'All':
    df_sap = df_sap[df_sap['unit'] == selected_unit]

penugasan_list = ['All'] + list(df_sap['penugasan'].unique())
selected_penugasan = st.sidebar.selectbox('Select Penugasan:', penugasan_list)

if selected_penugasan != 'All':
    df_sap = df_sap[df_sap['penugasan'] == selected_penugasan]

# If 'GOMAN' is selected, show additional filter for 'Admin GOMAN'
if selected_unit == 'GOMAN':
    admin_goman_list = ['All'] + list(df_sap['admin_goman'].unique())
    selected_admin_goman = st.sidebar.selectbox('Select Admin GOMAN:', admin_goman_list)

    # Filter the DataFrame based on the selected 'Admin GOMAN'
    if selected_admin_goman != 'All':
        df_sap = df_sap[df_sap['admin_goman'] == selected_admin_goman]

# If 'GOMED' is selected, show additional filter for 'Subunit GOMED'
if selected_unit == 'GOMED':
    subunit_list = ['All'] + list(df_sap['subunit'].unique())
    selected_subunit = st.sidebar.selectbox('Select Subunit:', subunit_list)

    # Filter the DataFrame based on the selected 'Penugasan GOMED'
    if selected_subunit != 'All':
        df_sap = df_sap[df_sap['subunit'] == selected_subunit]

selected_division = st.sidebar.multiselect('Select Division:', list(df_sap['division'].unique()), default=[])
if selected_division:
    df_sap = df_sap[df_sap['division'].isin(selected_division)]

selected_layer = st.sidebar.multiselect('Select Layer:', list(df_sap['layer'].unique()), default=[])
if selected_division:
    df_sap = df_sap[df_sap['layer'].isin(selected_division)]

selected_region = st.sidebar.multiselect('Select Region:', list(df_sap['region'].unique()), default=[])
if selected_region:
    df_sap = df_sap[df_sap['region'].isin(selected_region)]

# Sidebar: Breakdown variable
st.sidebar.markdown('### Breakdown Variable')
breakdown_variable = st.sidebar.selectbox('Select Breakdown Variable:', 
                                          ['unit', 'subunit', 'layer', 'generation', 'gender', 'division', 'department', 'admin_goman'])

# Create date filter for last_updated
min_value = df_combined_mysql['last_updated'].min()
max_value = df_combined_mysql['last_updated'].max()

# Initialize session state for date filters if not already present
if 'from_date' not in st.session_state:
    st.session_state.from_date = min_value
if 'to_date' not in st.session_state:
    st.session_state.to_date = max_value

# Default date range
from_date = st.session_state.from_date
to_date = st.session_state.to_date

# Create columns for buttons
st.write("**Choose the data period:**")
col1, col2, col3 = st.columns(3)

# Create buttons for shortcut filters in a single line
with col1:
    if st.button('Lifetime'):
        from_date = min_value
        to_date = max_value
        st.session_state.from_date = from_date
        st.session_state.to_date = to_date

with col2:
    if st.button('This Year'):
        current_year = datetime.datetime.now().year
        from_date = datetime.date(current_year, 1, 1)
        to_date = datetime.datetime.now().date()
        st.session_state.from_date = from_date
        st.session_state.to_date = to_date

with col3:
    if st.button('This Month'):
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month
        from_date = datetime.date(current_year, current_month, 1)
        to_date = datetime.datetime.now().date()
        st.session_state.from_date = from_date
        st.session_state.to_date = to_date

# Allow manual date input as well
from_date, to_date = st.date_input(
    '**Or pick the date manually:**',
    value=[from_date, to_date],
    min_value=min_value,
    max_value=max_value,
    format="YYYY-MM-DD"
)

# Update session state with manually picked dates
st.session_state.from_date = from_date
st.session_state.to_date = to_date

# Filter the data based on the selected date range
df_combined_mysql = df_combined_mysql[
    (df_combined_mysql['last_updated'] <= to_date) & (df_combined_mysql['last_updated'] >= from_date)
]

# Calculate months in range and dynamic target learning hours
def calculate_months(start_date, end_date):
    return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1

months_in_range = calculate_months(pd.to_datetime(from_date), pd.to_datetime(to_date))
#target_hours = months_in_range

# Dictionary to store target multipliers for each unit
unit_targets = {
    'GOMAN': 0.5,
    # Add more units and their multipliers as needed
}

# Function to get target hours based on unit
def get_target_hours(unit, months_in_range):
    return unit_targets.get(unit, 1) * months_in_range  # Default to 1 if unit not found

# Merge with SAP data
learning_hours = pd.merge(df_combined_mysql, df_sap, left_on='count AL', right_on='nik', how='right')

# Convert duration from seconds to hours and sum the duration hours
learning_hours['duration_hours'] = learning_hours['duration'] / 3600
learning_hours['duration_hours'] = learning_hours['duration_hours'].astype(float)
learning_hours['total_hours'] = learning_hours.groupby('count AL')['duration_hours'].transform('sum')

# Calculate target hours for each employee based on their unit
learning_hours['target_hours'] = learning_hours['unit'].apply(lambda x: get_target_hours(x, months_in_range))

# Determine whether each employee achieved the target
learning_hours['achieved_target'] = np.where(
    learning_hours['total_hours'].isna(), 'Inactive',
    np.where(learning_hours['total_hours'] >= learning_hours['target_hours'], 'Achieved', 'Not Achieved')
)

# Aggregate data by unit
unit_achievement = learning_hours.pivot_table(index=breakdown_variable, values='nik_y', columns='achieved_target', 
                                              aggfunc='nunique', fill_value=0).reset_index()

# Normalize counts for 100% stacked bar chart
unit_achievement['Achieved (%)'] = unit_achievement['Achieved'] / (unit_achievement['Achieved'] + unit_achievement['Not Achieved'] + unit_achievement['Inactive']) * 100
unit_achievement['Not Achieved (%)'] = unit_achievement['Not Achieved'] / (unit_achievement['Achieved'] + unit_achievement['Not Achieved'] + unit_achievement['Inactive']) * 100
unit_achievement['Inactive (%)'] = unit_achievement['Inactive'] / (unit_achievement['Achieved'] + unit_achievement['Not Achieved'] + unit_achievement['Inactive']) * 100

# Transform data for Altair
melted_counts = unit_achievement.melt(
    id_vars=breakdown_variable,
    value_vars=['Achieved', 'Not Achieved', 'Inactive'],
    var_name='Achievement',
    value_name='Count'
)

melted_percentage = unit_achievement.melt(
    id_vars=breakdown_variable,
    value_vars=['Achieved (%)', 'Not Achieved (%)', 'Inactive (%)'],
    var_name='Achievement',
    value_name='Percent'
)

# Combine counts and percentage into a single DataFrame
melted_counts['Percent'] = melted_percentage['Percent']

# Display unit_achievement
#st.write('## Disclaimer:')
#st.markdown(f'The target learning hours from {from_date.strftime("%B %Y")} to {to_date.strftime("%B %Y")} is {target_hours} hour(s) per employee.')

# Calculate unique learning hours per 'nik_y'
unique_learning_hours = learning_hours.drop_duplicates(subset=['nik_y'])

# Calculate summary statistics
total_employees = df_sap['nik'].nunique()
achieved_employees = unit_achievement['Achieved'].sum()
percent_achieved = (achieved_employees / total_employees) * 100

# Calculate average hours per active employee (with total_hours >= 0) and per all employees based on unique 'nik_y'
average_hours_active = unique_learning_hours[unique_learning_hours['total_hours'] >= 0]['total_hours'].mean()
average_hours_all = unique_learning_hours['total_hours'].sum() / total_employees

st.write('## Summary:')
st.markdown(f'- **Total Employees**: {total_employees}')
st.markdown(f'- **Employees Achieved Target**: {achieved_employees} ({percent_achieved:.2f}%)')
st.markdown(f'- **Avg. Hours per Active Employee**: {average_hours_active:.1f}')
st.markdown(f'- **Avg. Hours per All Employee**: {average_hours_all:.1f}')

# Display the calculated data as a horizontal 100% stacked bar chart
st.header(f'Learning Hours Achievement by {breakdown_variable.capitalize()}', divider='gray')

# Create the 100% stacked bar chart
chart = alt.Chart(melted_counts).mark_bar().encode(
    y=alt.Y(f'{breakdown_variable}:N', sort=None, axis=alt.Axis(title=breakdown_variable.capitalize())),
    x=alt.X('Percent:Q', axis=alt.Axis(title='Percentage'), scale=alt.Scale(domain=[0, 100])),
    color=alt.Color('Achievement:N', scale=alt.Scale(domain=['Achieved', 'Not Achieved', 'Inactive'], range=['#1f77b4', '#ff7f0e', '#808080'])),
    order=alt.Order('index:Q', sort='ascending'),    # Ensure active is plotted first    
    tooltip=[
        alt.Tooltip(f'{breakdown_variable}:N', title=breakdown_variable.capitalize()),
        alt.Tooltip('Achievement:N', title='Achievement'),
        alt.Tooltip('Count:Q', title='Count'),
        alt.Tooltip('Percent:Q', title='Percentage', format='.1f')
    ]
).properties(
    width=800  # Adjust width as needed
)

# Display the chart using Streamlit
st.altair_chart(chart, use_container_width=True)

# Display the raw data
st.header('Download Data', divider='gray')

# Define the columns to drop from df_combined_mysql
columns_drop = ['email_x', 'name', 'nik_x', 'title', 'last_updated', 'duration', 'type', 'platform', 'count AL', 'duration_hours']  # replace with actual columns to drop
unique_LH = learning_hours.drop(columns=columns_drop, errors='ignore').drop_duplicates()

# Section for Achieved Learners
with st.expander("Achieved"):
    achieved_df = unique_LH[unique_LH['achieved_target'] == 'Achieved']
    achieved_df.index = range(1, len(achieved_df) + 1)
    st.dataframe(achieved_df)

# Section for Not Acvhieved Learners
with st.expander("Not Achieved"):
    nachived_df = unique_LH[unique_LH['achieved_target'] == 'Not Achieved']
    nachived_df.index = range(1, len(nachived_df) + 1)
    st.dataframe(nachived_df)

# Section for Inactive
with st.expander("Inactive"):
    inactive_df = unique_LH[unique_LH['achieved_target'] == 'Inactive']
    inactive_df.index = range(1, len(inactive_df) + 1)
    st.dataframe(inactive_df)

# Update Data
st.divider()
st.markdown('''
_This app is using data cache for performance optimization, you can reload the data by clicking the button below then press 'R' on keyboard or refresh the page._
''')
if st.button("Update Data"):
    # Clear values from *all* all in-memory and on-disk data caches:
    st.cache_resource.clear()
    st.cache_data.clear()