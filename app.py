import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI

client = OpenAI(api_key=st.secrets["openai_api_key"])


# Constants
EMBEDDING_MODEL = "text-embedding-ada-002"
GPT_MODEL = "gpt-4-1106-preview"

# Load the data
file_path = 'Enkät - Företagsklimat  (Svar).xlsx'
df = pd.read_excel(file_path)

# Reference the third column for scores
score_column = df.columns[2]  # Third column

# Display the dataframe
st.title('Företagsenkät Konkurrens')
st.write('Respondenternas svar kategoriserat per bransch respondenten upplever att kommunen tränger ut privat näringsliv.')

# Sort the DataFrame by the score column
df_sorted = df.sort_values(by=score_column)

# Create histogram for sorted total scores
fig_histogram_sorted = px.histogram(df_sorted, x=score_column, nbins=6, title='Total Poängdistribution',
                                    color_discrete_sequence=px.colors.sequential.Viridis_r)

# Update the layout for the sorted histogram
fig_histogram_sorted.update_layout(bargap=0.1)
fig_histogram_sorted.update_xaxes(title='Anser att kommunen tränger undan privat verksamhet. 1 = hög utsträckning, 6 = inte alls', type='category')

# Display the sorted histogram
st.plotly_chart(fig_histogram_sorted)

# Calculate total mean, standard deviation, and number of responses
total_mean = df[score_column].mean()
total_std_dev = df[score_column].std()
total_number_of_responses = df[score_column].count()

# Display the calculated values
st.write(f"Totalt medelvärde: {total_mean:.2f}")
st.write(f"Total standardavvikelse: {total_std_dev:.2f}")
st.write(f"Totalt antal svar: {total_number_of_responses}")

# List of sectors
sectors = ['Besöksnäring', 'Bygg', 'Fastigheter', 'Handel', 'Industri', 'Information',
        'Jordbruk, skog, fiske', 'Personliga tjänster', 'Skola, utbildning',
        'Tjänster till företag', 'Transport', 'Vård & omsorg', 'Upplever inte att det sker', 'Other']
# Collect data for score table
score_data = []
# Identify responses that don't belong to predefined sectors
other_responses = df[~df['Inom vilken bransch/vilka branscher upplever du att detta sker? '].str.contains('|'.join(sectors))]
# Create a new category 'Other' and include responses in it
df.loc[~df['Inom vilken bransch/vilka branscher upplever du att detta sker? '].str.contains('|'.join(sectors)), 'Inom vilken bransch/vilka branscher upplever du att detta sker? '] = 'Other'

for sector in sectors:
    sector_df = df[df['Inom vilken bransch/vilka branscher upplever du att detta sker? '].str.contains(sector)]
    avg_score = sector_df[score_column].mean()
    std_dev = sector_df[score_column].std()
    num_respondents = len(sector_df)
    score_data.append({'Sector': sector, 'Average Score': avg_score, 
                    'Standard Deviation': std_dev, 'Number of Respondents': num_respondents})

# Create DataFrame from collected data and sort by average score
score_table = pd.DataFrame(score_data).sort_values(by='Average Score', ascending=False)


# Prepare data for 100% stacked bar chart
stacked_data_percentage = []
stacked_data_count = []
sector_counts = {}

for sector in sectors:
    sector_df = df[df['Inom vilken bransch/vilka branscher upplever du att detta sker? '].str.contains(sector)]
    total_count = len(sector_df)
    sector_counts[sector] = total_count  # Store total count for each sector

    for score in range(1, 7):
        score_count = len(sector_df[sector_df[score_column] == score])
        percentage = (score_count / total_count) * 100 if total_count > 0 else 0
        stacked_data_percentage.append({'Sector': sector, 'Score': score, 'Percentage': percentage})
        stacked_data_count.append({'Sector': sector, 'Score': score, 'Count': score_count})

# Sorting sectors by total counts
sorted_sectors = sorted(sector_counts, key=sector_counts.get, reverse=True)

# Creating DataFrames
stacked_df_percentage = pd.DataFrame(stacked_data_percentage)
stacked_df_count = pd.DataFrame(stacked_data_count)
# Create 100% stacked bar chart sorted by total count
fig = px.bar(stacked_df_percentage, x='Sector', y='Percentage', color='Score', 
            color_continuous_scale=['red', 'orange', 'yellow', 'lightgreen', 'green'], 
            labels={'Percentage': '% of Responses'}, title='Sector-wise Score Distribution',
            category_orders={'Sector': sorted_sectors})
fig.update_layout(barmode='stack', coloraxis_colorbar=dict(title='Score'))
st.plotly_chart(fig)

# Create stacked bar chart with absolute numbers sorted by total count
fig2 = px.bar(stacked_df_count, x='Sector', y='Count', color='Score',
            color_continuous_scale=['red', 'orange', 'yellow', 'lightgreen', 'green'], 
            labels={'Count': 'Number of Responses'}, title='Sector-wise Score Distribution',
            category_orders={'Sector': sorted_sectors})
fig2.update_layout(barmode='stack', coloraxis_colorbar=dict(title='Score'))
st.plotly_chart(fig2)

# Using the same score_table DataFrame but sorting it according to the total counts in each sector
score_table_sorted = score_table.set_index('Sector').loc[sorted_sectors].reset_index()

# Create line chart for average scores
fig3 = px.line(score_table_sorted, x='Sector', y='Average Score', 
            title='Average Score per Sector', markers=True)
st.plotly_chart(fig3)


st.write(score_table)

# Note about the total number of respondents
total_respondents = len(df)
st.write(f"Total number of respondents: {total_respondents}. Note: One respondent can be reply for several sectors.")
with st.expander("Kategorin Other"):
    st.write(other_responses)



# Dropdown for selecting sector
st.subheader('Välj bransch')
sectors_with_all = ['Välj bransch','Alla'] + sectors  # Add 'All' option
selected_sector = st.selectbox('Inom vilken bransch/vilka branscher upplever du att detta sker?', sectors_with_all)

# Filter data for selected sector
if selected_sector == 'Alla':
    # Include all sectors
    sector_df = df.copy()
else:
    # Filter for a specific sector
    sector_df = df[df['Inom vilken bransch/vilka branscher upplever du att detta sker? '].str.contains(selected_sector)]
fig = px.histogram(sector_df, x=score_column, nbins=6, title=f'Histogram for {selected_sector}', 
                category_orders={score_column: [1, 2, 3, 4, 5, 6]})

# Update x-axis title
fig.update_xaxes(title='Anser att kommunen tränger undan privat verksamhet. 1 = hög utsträckning, 6 = inte alls', type='category')

st.plotly_chart(fig)


# Filter data for selected sector and respondents with score below 3
comments_df = sector_df[sector_df[score_column] < 3]

# Extract comments using the column index
comments_column = df.columns[5]  # Sixth column
comments = comments_df[comments_column].dropna().unique()

# Display comments in a textarea
comments_text = '\n'.join(comments)
# st.text_area("Comments for respondents with score below 3", comments_text, height=300)


instructions_prompt = f"""
    Kommentarer från företagare: {comments_text}
    Du är en hjälpsam assistent som sammanfattar kommentarer som beskriver när företagare anser att komunen
    har trängt undan privat verksamhet, eller om kommunen bör göra ändringar inom denna frågan. 
    Sammanfatta kommentarer från företagare i 1-4 bullet points. Utgå från kommentarerna. Om det inte finns kommentarer, skriv att det inte finns några kommentarer.
    """
st.subheader("Sammanfattning av kommentarer där betyg är 1 eller 2")  
# Stream the GPT-4 reply
with st.chat_message("assistant"):
    message_placeholder = st.empty()
    full_response = ""
    completion = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "system", "content": instructions_prompt}],
        stream=True,
        temperature=0.3
    )
    for chunk in completion:
        if chunk.choices[0].finish_reason == "stop": 
            message_placeholder.markdown(full_response)
            break
        full_response += chunk.choices[0].delta.content
        message_placeholder.markdown(full_response + "▌")