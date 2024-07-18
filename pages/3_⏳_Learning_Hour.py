import streamlit as st
import pandas as pd
import altair as alt
from data_processing import finalize_data
import datetime

# Set the tilte and favicon for the Browser's tab bar
st.set_page_config(
    page_title='Learning Hours',
    page_icon=':hourglass:', # This is an emoji shortcode. Could be uRL too.
)

# Add logo and title above side bar
st.logo('kognisi_logo.png')

# Fetch the data
merged_df, df_combined_mysql, df_sap, right_merged_df = finalize_data()

# Set the title that appears at the top of the page
st.markdown('''
            # :hourglass: Learning Hours
            
            This page provides insights into how many employees achieved the target learning hours per unit.
            ''')

# Sidebar: Add a selectbox for unit filter
st.sidebar.markdown('### Unit Filter')
unit_list = ['All'] + list(df_sap['unit'].unique())
selected_unit = st.sidebar.selectbox('Select Unit:', unit_list)

if selected_unit != 'All':
    df_sap = df_sap[df_sap['unit'] == selected_unit]
    merged_df = merged_df[merged_df['unit'] == selected_unit]

subunit_list = list(df_sap['subunit'].unique())
selected_subunit = st.sidebar.multiselect('Select Subunit:', subunit_list, default=[])

if selected_subunit:
    df_sap = df_sap[df_sap['subunit'].isin(selected_subunit)]
    merged_df = merged_df[merged_df['subunit'].isin(selected_subunit)]

adminhr_list = list(df_sap['admin_hr'].unique())
selected_adminhr = st.sidebar.multiselect('Select Admin for HR:', adminhr_list, default=[])

if selected_adminhr:
    df_sap = df_sap[df_sap['admin_hr'].isin(selected_adminhr)]
    merged_df = merged_df[merged_df['admin_hr'].isin(selected_adminhr)]

# Sidebar: Add a selectbox for breakdown variable
st.sidebar.markdown ('### Breakdown Variable')
breakdown_variable = st.sidebar.selectbox('Select Breakdown Variable:', ['unit', 'subunit', 'admin_hr', 'layer', 'generation', 'gender', 'division', 'department'])

# Create date filter for last_updated
min_value = df_combined_mysql['last_updated'].min()
max_value = df_combined_mysql['last_updated'].max()

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
df_combined_mysql = df_combined_mysql[
    (df_combined_mysql['last_updated'] <= to_date) & (df_combined_mysql['last_updated'] >= from_date)
]

# Calculate the number of months in the selected date range
def calculate_months(start_date, end_date):
    return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1

months_in_range = calculate_months(pd.to_datetime(from_date), pd.to_datetime(to_date))

# Define the dynamic target learning hours based on the selected date range
target_hours = months_in_range  # Target is 1 hour per month

# Convert duration from seconds to hours
df_combined_mysql['duration_hours'] = df_combined_mysql['duration'] / 3600

# Calculate total learning hours per employee from MySQL data
learning_hours = df_combined_mysql.groupby('count AL')['duration_hours'].sum().reset_index()
learning_hours.columns = ['count AL', 'total_hours']

# Determine whether each employee achieved the target
learning_hours['achieved_target'] = learning_hours['total_hours'] >= target_hours

# Merge with SAP data to get unit information
learning_hours = pd.merge(learning_hours, df_sap, left_on='count AL', right_on='nik', how='left')

# Exclude rows with N/A in the unit column
learning_hours = learning_hours[learning_hours['unit'].notna()]

# Aggregate data by unit
unit_achievement = learning_hours.pivot_table(
    index=breakdown_variable,
    columns='achieved_target',
    aggfunc='size',
    fill_value=0
).reset_index()

# Ensure both columns exist in the pivot table
if True not in unit_achievement.columns:
    unit_achievement[True] = 0
if False not in unit_achievement.columns:
    unit_achievement[False] = 0

# Rename columns
unit_achievement.columns = [breakdown_variable] + ['Not Achieved', 'Achieved']  # Renaming False then True (alphabetically)

# Calculate total employees per breakdown_variable from SAP data
total_sap = df_sap.groupby(breakdown_variable)['nik'].nunique().reset_index()
total_sap.columns = [breakdown_variable, 'Total SAP']

# Merge the total_sap with unit_achievement on breakdown_variable
unit_achievement = pd.merge(unit_achievement, total_sap, on=breakdown_variable, how='left')

# Add Passive Learners Column
unit_achievement['Passive Learners'] = unit_achievement['Total SAP'] - unit_achievement['Not Achieved'] - unit_achievement['Achieved']

# Normalize counts for 100% stacked bar chart
unit_achievement['Achieved (%)'] = (unit_achievement['Achieved'] / unit_achievement['Total SAP']) * 100
unit_achievement['Not Achieved (%)'] = (unit_achievement['Not Achieved'] / unit_achievement['Total SAP']) * 100
unit_achievement['Passive Learners (%)'] = (unit_achievement ['Passive Learners'] / unit_achievement['Total SAP']) * 100

# Transform data for Altair
melted_counts = unit_achievement.melt(
    id_vars=breakdown_variable,
    value_vars=['Achieved', 'Not Achieved', 'Passive Learners'],
    var_name='Achievement',
    value_name='Count'
)

melted_percentage = unit_achievement.melt(
    id_vars=breakdown_variable,
    value_vars=['Achieved (%)', 'Not Achieved (%)', 'Passive Learners (%)'],
    var_name='Achievement',
    value_name='Percent'
)

# Combine counts and percentage into a single DataFrame
melted_counts['Percent'] = melted_percentage['Percent']

# Display unit_achievement
st.write('## Disclaimer:')
st.markdown(f'The target learning hours from {from_date.strftime("%B %Y")} to {to_date.strftime("%B %Y")} is {target_hours} hour(s) per employee.')

# Calculate summary statistics
total_employees = df_sap['nik'].nunique()
achieved_employees = learning_hours[learning_hours['achieved_target']]['count AL'].nunique()
percent_achieved = (achieved_employees / total_employees) * 100
average_hours = learning_hours['total_hours'].mean()

st.write('## Summary:')
st.markdown(f'- **Total Employees**: {total_employees}')
st.markdown(f'- **Employees Achieved Target**: {achieved_employees} ({percent_achieved:.2f}%)')
st.markdown(f'- **Avg. Hours per Employee**: {average_hours:.1f}')


# Display the calculated data as a horizontal 100% stacked bar chart
st.header(f'Learning Hours Achievement by {breakdown_variable.capitalize()}', divider='gray')

# Create the 100% stacked bar chart
chart = alt.Chart(melted_counts).mark_bar().encode(
    y=alt.Y(f'{breakdown_variable}:N', sort=None, axis=alt.Axis(title=breakdown_variable.capitalize())),
    x=alt.X('Percent:Q', axis=alt.Axis(title='Percentage'), scale=alt.Scale(domain=[0, 100])),
    color=alt.Color('Achievement:N', scale=alt.Scale(domain=['Achieved', 'Not Achieved', 'Passive Learners'], range=['#1f77b4', '#ff7f0e', '#808080'])),
    order=alt.Order('Achievement:N', sort='ascending'),    # Ensure active is plotted first    
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

if st.button("Reload Data"):
    # Clear values from *all* all in-memory and on-disk data caches:
    st.cache_resource.clear()
    st.cache_data.clear()