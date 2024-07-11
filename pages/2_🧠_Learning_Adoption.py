import streamlit as st
import pandas as pd
import altair as alt
from data_processing import finalize_data

# Set the title and favicon for the Browser's tab bar.
st.set_page_config(
    page_title='Learning Adoption',
    page_icon=':brain:',  # This is an emoji shortcode. Could be a URL too.
)

# Add logo and title above sidebar
st.logo('kognisi_logo.png')

# Fetch the data
merged_df, df_combined_mysql, df_sap = finalize_data()

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

# Calculate Active Learners
active_learners = merged_df[merged_df['status'] == 'Internal']
active_counts = active_learners.groupby(breakdown_variable)['count AL'].nunique().reset_index()
active_counts.columns = [breakdown_variable, 'Active Learners']

# Calculate Passive Learners
# Group df_sap by the selected breakdown variable and count unique 'nik'
all_nik_in_sap = df_sap.groupby(breakdown_variable)['nik'].nunique().reset_index()
all_nik_in_sap.columns = [breakdown_variable, 'all_nik_count']

# Merge to get passive counts by the selected breakdown variable
passive_counts = pd.merge(all_nik_in_sap, active_counts, on=breakdown_variable, how='left').fillna(0)
passive_counts['Passive Learners'] = passive_counts['all_nik_count'] - passive_counts['Active Learners']
passive_counts.drop(columns=['all_nik_count', 'Active Learners'], inplace=True)

# Merge the counts to have a complete dataset for the chart
final_counts = pd.merge(active_counts, passive_counts, on=breakdown_variable, how= 'outer').fillna(0)

# Normalize counts for 100% stacked bar chart
final_counts['Active Learners (%)'] = final_counts['Active Learners'] / (final_counts['Active Learners'] + final_counts['Passive Learners']) * 100
final_counts['Passive Learners (%)'] = final_counts['Passive Learners'] / (final_counts['Active Learners'] + final_counts['Passive Learners']) * 100

# Sort units based on the total learners
#final_counts = final_counts.sort_values(by=breakdown_variable, ascending=False)

# Transform data for Altair
melted_counts = final_counts.melt(
    id_vars=breakdown_variable,
    value_vars=['Active Learners', 'Passive Learners'],
    var_name='Learner Type',
    value_name='Count'
)

melted_percentage = final_counts.melt(
    id_vars=breakdown_variable,
    value_vars=['Active Learners (%)', 'Passive Learners (%)'],
    var_name='Learner Type',
    value_name='Percent'
)

# Combine counts and percentage into a single DataFrame
melted_counts['Percent'] = melted_percentage['Percent']

# Set the title that appears at the top of the page.
st.markdown('''
# :brain: Learning Adoption

This page provides insights into the adoption of Kognisi learning platforms.
''')

# Display the calculated overall learning adoption
st.header('Overall Learning Adoption', divider='gray')

# Calculate overall learning adoption
total_active_learners = final_counts['Active Learners'].sum()
total_learners = final_counts['Active Learners'].sum() + final_counts['Passive Learners'].sum()
overall_adoption = (total_active_learners / total_learners) * 100

# Display metrics column
col1, col2, col3 = st.columns(3)
col1.metric("Active Learners", int(total_active_learners))
col2.metric("Active Employees", int(total_learners))
col3.metric("Learning Adoption", f"{overall_adoption:.2f}%")

# Display the calculated percentage as a bar chart
st.header(f'Learning Adoption by {breakdown_variable.capitalize()}', divider='gray')

# Create the base chart with Active and Passive Learners
base = alt.Chart(melted_counts).mark_bar().encode(
    x=alt.X(f'{breakdown_variable}:N', sort='-y', axis=alt.Axis(title=breakdown_variable.capitalize())),
    y=alt.Y('Percent:Q', axis=alt.Axis(title='Learning Adoption (%)'), scale=alt.Scale(domain=[0, 100])),
    color=alt.Color('Learner Type:N', scale=alt.Scale(domain=['Active Learners', 'Passive Learners'], range=['#ff7f0e', '#1f77b4'])),
    order=alt.Order('Learner Type:N', sort='ascending'),    # Ensure active is plotted first
    tooltip=[
        alt.Tooltip(f'{breakdown_variable}:N', title=breakdown_variable.capitalize()),
        alt.Tooltip('Learner Type:N', title='Learner Type'),
        alt.Tooltip('Count:Q', title='Count'),
        alt.Tooltip('Percent:Q', title='Percentage', format='.1f')
    ]
).properties(
    width=alt.Step(40)   # Adjust width as needed
)

# Add the Learning Adoption line chart
line = alt.Chart(final_counts).mark_line(color='green').encode(
    x=f'{breakdown_variable}:N',
    y=alt.Y('Active Learners (%):Q', axis=alt.Axis(title='Learning Adoption (%)'), scale=alt.Scale(domain=[0, 100])),  # Removing the title and setting the scale
    tooltip=[
        alt.Tooltip(f'{breakdown_variable}:N', title=breakdown_variable.capitalize()),
        alt.Tooltip('Active Learners (%):Q', title='Learning Adoption', format='.1f')
    ]
)

# Combine the charts
combo_chart = alt.layer(base, line).resolve_scale(
    y='shared'  # Use shared scale for both charts
).properties(
    width=alt.Step(40)  # Adjust width as needed
)

# Display the chart using Streamlit
st.altair_chart(combo_chart, use_container_width=True)