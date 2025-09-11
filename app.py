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

    # Specify expected headers in case there are duplicates in the actual sheet
    expected_headers = ["name", "email", "universitas", "major", "whatsapp", "linkedin", "instagram", "cv", "code", "portofolio", "Status", "select_unit"]

    data = sheet.get_all_records(expected_headers=expected_headers)

    if not data:
        st.error("No data found in the sheet.")
        return pd.DataFrame()

    df_talent = pd.DataFrame(data)

    # Ensure the DataFrame only contains the required columns
    df_talent = df_talent[expected_headers]

    return df_talent

def update_sheet(index, column_name, new_value):
    secret_info = st.secrets["sheets"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('Talent Pool Database')
    sheet = spreadsheet.sheet1

    # Find the column index for the target column
    headers = sheet.row_values(1)  # Get the header row
    if column_name not in headers:
        st.error(f"No '{column_name}' column found in the spreadsheet.")
        return

    column_index = headers.index(column_name) + 1  # Convert to 1-based index

    # Update the corresponding cell
    sheet.update_cell(index + 2, column_index, new_value)  # index + 2 accounts for header and zero-indexing


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

# Columns to display in the editable table
editable_columns = ["code","name", "universitas", "major", "Status", "select_unit"]

# Status options
statuses = ["Open to Work", "Process in Unit", "Offering", "Hired"]

# Select unit options
unit_options = [
    "GOMAN", "GORP", "DYANDRA", "KG PRO", "CHR", "CORCOMM", "CORCOMP", "CFL", "CORSEC", "CITIS",
    "GOHR - AMARIS", "GOHR - GWS", "GOHR - KAMPI", "GOHR - KAYANA", "GOHR - SAMAYA", "GOHR - SANTIKA",
    "GOHR - SANTIKA PREMIERE", "GOHR - THE ANVAYA", "KG MEDIA - HARKOM", "KG MEDIA - GRID", 
    "KG MEDIA - TRIBUN", "KG MEDIA - KOMPAS.COM", "KG MEDIA - RADIO", "KG MEDIA - KONTAN", 
    "KG MEDIA - KOMPAS TV", "KG MEDIA - TRANSITO", "YMN - UMN", "YMN - DIGITAL", "YMN - POLITEKNIK"
]

st.write("Talent List")

for index, row in filtered_df.iterrows():
    st.markdown(f"### 🎯 {row['name']} ({row['code']})")  # 🔹 Judul row
    
    cols = st.columns(len(editable_columns))
    row_index = row["name"]  

    for i, col_name in enumerate(editable_columns):
        if col_name == "Status":
            current_status = row[col_name]
            if current_status not in statuses:
                current_status = "Open to Work"  

            new_status = cols[i].selectbox(
                f"Status", statuses, 
                index=statuses.index(current_status), 
                key=f"status_{index}"
            )
            if new_status != current_status:
                update_sheet(index, "Status", new_status)
                st.success(f"Status updated for {row_index} to {new_status}")
                sleep(1)

        elif col_name == "select_unit":
            if row["Status"] in ["Process in Unit", "Offering", "Hired"]:
                current_unit = row[col_name] if row[col_name] in unit_options else None
                new_unit = cols[i].selectbox(
                    f"Unit", [""] + unit_options, 
                    index=unit_options.index(current_unit) + 1 if current_unit else 0, 
                    key=f"unit_{index}"
                )
                if new_unit != current_unit:
                    update_sheet(index, "select_unit", new_unit)
                    st.success(f"Unit updated for {row_index} to {new_unit}")
                    sleep(1)
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
