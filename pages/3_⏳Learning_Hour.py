import streamlit as st
import pandas as pd
import altair as alt
from data_processing import finalize_data
from datetime import datetime

# Set the tilte and favicon for the Browser's tab bar
st.set_page_config(
    page_title='Learning Hours',
    page_icon=':hourglass:', # This is an emoji shortcode. Could be uRL too.
)

# Add logo and title above side bar
st.logo('kognisi_logo.png')

# Fetch the data
merged_df, df_combined_mysql, df_sap = finalize_data()

# Ensure email columns are consistent: trim spaces and convert to lowercase
df_combined_mysql['email'] = df_combined_mysql['email'].str.strip().str.lower()
df_sap['email'] = df_sap['email'].str.strip().str.lower()

# Define the dynamic target learning hours based on the current month
current_month = datetime.now().month
target_hours = current_month    # Target is 1 hour per month

# Convert duration from seconds to hours
df_combined_mysql['duration_hours'] = df_combined_mysql['duration'] / 3600

# Calculate total learning hours per employee from MySQL data
learning_hours = df_combined_mysql.groupby('email')['duration_hours'].sum().reset_index()
learning_hours.columns = ['email', 'total_hours']

# Determine whether each employee achieved the target
learning_hours['achieved_target'] = learning_hours['total_hours'] >= target_hours

# Sidebar: Add a selectbox for unit filter
st.sidebar.markdown('### Unit Filter')
unit_list = ['All'] + list(df_sap['unit'].unique())
selected_unit = st.sidebar.selectbox('Select Unit:', unit_list)

# Sidebar: Add a selectbox for breakdown variable
st.sidebar.markdown ('### Breakdown Variable')
breakdown_variable = st.sidebar.selectbox('Select Breakdown Variable:', ['unit', 'subunit', 'layer', 'division', 'position'])

# Apply unit filter id a specific unit is selected
if selected_unit != 'All':
    df_sap = df_sap[df_sap['unit'] == selected_unit]
    merged_df = merged_df[merged_df['unit'] == selected_unit]

# Merge with SAP data to get unit information
learning_hours = pd.merge(learning_hours, df_sap[['email', breakdown_variable]], on='email', how='left')

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
unit_achievement.columns = [breakdown_variable] + ['Not Achieved', 'Achieved']

# Calculate total employees per breakdown_variable from SAP data
total_sap = df_sap.groupby(breakdown_variable)['email'].nunique().reset_index()
total_sap.columns = [breakdown_variable, 'Total SAP']

# Merge the total_sap with unit_achievement on breakdown_variable
unit_achievement = pd.merge(unit_achievement, total_sap, on=breakdown_variable, how='left')

# Add Passive Learners Column
unit_achievement['Passive Learners'] = unit_achievement['Total SAP'] - unit_achievement['Not Achieved'] - unit_achievement['Achieved']

# Normalize counts for 100% stacked bar chart
unit_achievement['Not Achieved (%)'] = (unit_achievement['Not Achieved'] / unit_achievement['Total SAP']) * 100
unit_achievement['Achieved (%)'] = (unit_achievement['Achieved'] / unit_achievement['Total SAP']) * 100
unit_achievement['Passive Learners (%)'] = (unit_achievement ['Passive Learners'] / unit_achievement['Total SAP']) * 100

# Transform data for Altair
melted_counts = unit_achievement.melt(
    id_vars=breakdown_variable,
    value_vars=['Not Achieved', 'Achieved', 'Passive Learners'],
    var_name='Achievement',
    value_name='Count'
)

melted_percentage = unit_achievement.melt(
    id_vars=breakdown_variable,
    value_vars=['Not Achieved (%)', 'Achieved (%)', 'Passive Learners (%)'],
    var_name='Achievement',
    value_name='Percent'
)

# Combine counts and percentage into a single DataFrame
melted_counts['Percent'] = melted_percentage['Percent']

print(melted_counts)

# Set the title that appears at the top of the page
st.markdown('''
            # :hourglass: Learning Hours
            
            This page provides insights into how many employees achieved the target learning hours per unit.
            ''')

# Display unit_achievement
st.write('## Disclaimer:')
st.markdown(f'The target learning hours for this month ({datetime.now().strftime("%B")}) is {target_hours} hour(s) per employee.')

# Calculate summary statistics
total_employees = df_sap['nik'].nunique()
achieved_employees = learning_hours[learning_hours['achieved_target']]['email'].nunique()
percent_achieved = (achieved_employees / total_employees) * 100

st.write('## Summary:')
st.markdown(f'- **Total Employees**: {total_employees}')
st.markdown(f'- **Employees Achieved Target**: {achieved_employees} ({percent_achieved:.2f}%)')

# Display the calculated data as a horizontal 100% stacked bar chart
st.header(f'Learning Hours Achievement by {breakdown_variable.capitalize()}', divider='gray')

# Create the 100% stacked bar chart
chart = alt.Chart(melted_counts).mark_bar().encode(
    y=alt.Y(f'{breakdown_variable}:N', sort='-x', axis=alt.Axis(title=breakdown_variable.capitalize())),
    x=alt.X('Percent:Q', axis=alt.Axis(title='Percentage'), scale=alt.Scale(domain=[0, 100])),
    color=alt.Color('Achievement:N', scale=alt.Scale(domain=['Not Achieved', 'Achieved', 'Passive Learners'], range=['#ff7f0e', '#1f77b4', '#808080'])),
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