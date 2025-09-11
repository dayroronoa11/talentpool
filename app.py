import streamlit as st
from time import sleep
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def fetch_data_talent():
    secret_info = st.secrets["sheets"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('Talent Pool Database')
    sheet = spreadsheet.sheet1
    
    data = sheet.get_all_records()

    if not data:
        st.error("No data found in the sheet.")
        return pd.DataFrame()

    df_talent = pd.DataFrame(data)
    show_columns = ["code", "name", "universitas", "major", "pekerjaan", "posisi", "timestamp", "linkedin", "cv", "unit", "user"]
    for col in show_columns:
        if col not in df_talent.columns:
            df_talent[col] = ""  # kalau belum ada, tambahin kolom kosong

    return df_talent[show_columns]

def update_sheet(index, column_name, new_value):
    secret_info = st.secrets["sheets"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('Talent Pool Database')
    sheet = spreadsheet.sheet1

    # Find the column index for the target column
    headers = sheet.row_values(1)  
    if column_name not in headers:
        st.error(f"No '{column_name}' column found in the spreadsheet.")
        return

    column_index = headers.index(column_name) + 1 

    # Update the corresponding cell
    sheet.update_cell(index + 2, column_index, new_value) 


st.set_page_config(layout="wide")
df_talent = fetch_data_talent()
st.header('Talent Pool Database', divider="blue")

# ========== 🔹 Summary Section ==========
with st.expander("🔎Summary", expanded=True):
    col1, col2, col3 = st.columns(3)
    col1.dataframe(df_talent.groupby("code")["name"].count().reset_index().rename(columns={"name": "count"}))
    col2.dataframe(df_talent.groupby("universitas")["name"].count().reset_index().rename(columns={"name": "count"}))
    col3.dataframe(df_talent.groupby("major")["name"].count().reset_index().rename(columns={"name": "count"}))
# Filter selection with 4 columns for better layout
filter_columns = ['name', 'code', 'universitas', 'major']
selected_filters = {}

# Create four columns for filter selection
filter_columns_len = len(filter_columns)
col1, col2, col3, col4 = st.columns(4)
cols = [col1, col2, col3, col4]
for idx, col in enumerate(cols):
    if idx < filter_columns_len:
        selected_filters[filter_columns[idx]] = col.selectbox(f"Filter by {filter_columns[idx]}", ['All'] + sorted(df_talent[filter_columns[idx]].unique().tolist()), key=filter_columns[idx])

# Apply filters
filtered_df = df_talent
for col, selected_value in selected_filters.items():
    if selected_value != 'All':
        filtered_df = filtered_df[filtered_df[col] == selected_value]



st.write("Talent List")
show_columns = ["code", "name", "universitas", "major", "pekerjaan", "posisi", "timestamp", "linkedin", "cv", "unit", "user"]
statuses = ["Open to Work", "Process in Unit", "Offering", "Hired"]
unit_options = [
    "GOMAN", "GORP", "DYANDRA", "KG PRO", "CHR", "CORCOMM", "CORCOMP", "CFL", "CORSEC", "CITIS",
    "GOHR - AMARIS", "GOHR - GWS", "GOHR - KAMPI", "GOHR - KAYANA", "GOHR - SAMAYA", "GOHR - SANTIKA",
    "GOHR - SANTIKA PREMIERE", "GOHR - THE ANVAYA", "KG MEDIA - HARKOM", "KG MEDIA - GRID", 
    "KG MEDIA - TRIBUN", "KG MEDIA - KOMPAS.COM", "KG MEDIA - RADIO", "KG MEDIA - KONTAN", 
    "KG MEDIA - KOMPAS TV", "KG MEDIA - TRANSITO", "YMN - UMN", "YMN - DIGITAL", "YMN - POLITEKNIK"
]



# 🔹 Loop row by row
for index, row in df_talent.iterrows():
    st.markdown(f"**Row {index+1}**", unsafe_allow_html=True)  # judul tiap row
    cols = st.columns(len(df_talent.columns))

    for i, col_name in enumerate(df_talent.columns):
        if col_name == "unit":
            current_unit = row[col_name] if row[col_name] in unit_options else ""
            new_unit = cols[i].selectbox(
                f"{col_name} - {row['name']}",
                [""] + unit_options,
                index=unit_options.index(current_unit) + 1 if current_unit else 0,
                key=f"unit_{index}"
            )
            if new_unit != current_unit:
                update_sheet(index, "unit", new_unit)
                st.success(f"Unit updated for {row['name']} → {new_unit}")
                sleep(1)

        elif col_name == "user":
            current_user = row[col_name]
            new_user = cols[i].text_input(
                f"{col_name} - {row['name']}",
                value=current_user,
                key=f"user_{index}"
            )
            if new_user != current_user:
                update_sheet(index, "user", new_user)
                st.success(f"User updated for {row['name']} → {new_user}")
                sleep(1)

        elif col_name in ["linkedin", "cv"]:
            if pd.notnull(row[col_name]) and row[col_name] != "":
                cols[i].markdown(f"[{col_name.capitalize()}]({row[col_name]})", unsafe_allow_html=True)
            else:
                cols[i].write("-")
        else:
            cols[i].write(row[col_name])
    

    # Display hyperlinks for LinkedIn and CV
    links = []
    if pd.notnull(row["linkedin"]):
        links.append(f"[LinkedIn]({row['linkedin']})")
    if pd.notnull(row["cv"]):
        links.append(f"[CV]({row['cv']})")

    cols[-1].markdown(" | ".join(links), unsafe_allow_html=True)
