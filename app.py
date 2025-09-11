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
    show_columns = ["code", "timestamp", "name", "universitas", "major", "pekerjaan", 
                    "linkedin", "cv", "status", "select_unit", "user"]
    
    for col in show_columns:
        if col not in df_talent.columns:
            df_talent[col] = ""  

    return df_talent[show_columns]

def update_sheet(index, column_name, new_value):
    secret_info = st.secrets["sheets"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('Talent Pool Database')
    sheet = spreadsheet.sheet1

    headers = sheet.row_values(1)  
    if column_name not in headers:
        st.error(f"No '{column_name}' column found in the spreadsheet.")
        return

    column_index = headers.index(column_name) + 1 
    sheet.update_cell(index + 2, column_index, new_value) 


st.set_page_config(layout="wide")
# CSS styling
st.markdown(
    """
    <style>
    div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] {
        font-size: 13px;  /* kecilin font */
    }
    .header-row {
        font-weight: bold;
        background-color: #f0f2f6;
        padding: 6px 0;
        border-bottom: 1px solid #ddd;
    }
    </style>
    """,
    unsafe_allow_html=True
)

df_talent = fetch_data_talent()
st.header('Talent Pool Database', divider="blue")

# ========== 🔹 Summary Section ==========
with st.expander("🔎Summary", expanded=True):
    col1, col2, col3 = st.columns(3)
    col1.dataframe(df_talent.groupby("code")["name"].count().reset_index().rename(columns={"name": "count"}))
    col2.dataframe(df_talent.groupby("universitas")["name"].count().reset_index().rename(columns={"name": "count"}))
    col3.dataframe(df_talent.groupby("major")["name"].count().reset_index().rename(columns={"name": "count"}))

# ========== 🔹 Filter Section ==========
filter_columns = ['name', 'code', 'universitas', 'major']
selected_filters = {}

col1, col2, col3, col4 = st.columns(4)
cols = [col1, col2, col3, col4]
for idx, col in enumerate(cols):
    if idx < len(filter_columns):
        selected_filters[filter_columns[idx]] = col.selectbox(
            f"Filter by {filter_columns[idx]}",
            ['All'] + sorted(df_talent[filter_columns[idx]].unique().tolist()),
            key=filter_columns[idx]
        )

filtered_df = df_talent.copy()
for col, selected_value in selected_filters.items():
    if selected_value != 'All':
        filtered_df = filtered_df[filtered_df[col] == selected_value]

# ========== 🔹 Talent List ==========
st.markdown("✨ **Talent List**")


statuses = ["Open to Work", "Process in Unit", "Offering", "Hired"]
unit_options = [
    "GOMAN", "GORP", "DYANDRA", "KG PRO", "CHR", "CORCOMM", "CORCOMP", "CFL", "CORSEC", "CITIS",
    "GOHR", "HARKOM", "GRID", "TRIBUN", "KOMPAS.COM", "RADIO", 
    "KONTAN", "KOMPAS TV", "TRANSITO", "YMN"
]

# 🔹 Show header row
header_cols = st.columns(10)
headers = ["Code", "Timestamp", "Name", "Universitas", "Major", "Pekerjaan",
           "Status", "Select Unit", "User", "Links"]

for i, h in enumerate(headers):
    header_cols[i].markdown(f"<div class='header-row'>{h}</div>", unsafe_allow_html=True)
st.divider()

for index, row in filtered_df.iterrows():
    with st.container():
        cols = st.columns(10)

        cols[0].write(row["code"])
        cols[1].write(row["timestamp"])
        cols[2].write(row["name"])
        cols[3].write(row["universitas"])
        cols[4].write(row["major"])
        cols[5].write(row["pekerjaan"])

        # Editable status
        current_status = row["status"] if row["status"] in statuses else "Open to Work"
        new_status = cols[6].selectbox(
            "Status",
            statuses,
            index=statuses.index(current_status),
            key=f"status_{index}"
        )
        if new_status != current_status:
            update_sheet(index, "status", new_status)
            st.success(f"Status updated for {row['name']} → {new_status}")
            sleep(1)

        # Editable unit
        current_unit = row["select_unit"] if row["select_unit"] in unit_options else ""
        new_unit = cols[7].selectbox(
            "Select Unit",
            [""] + unit_options,
            index=unit_options.index(current_unit) + 1 if current_unit else 0,
            key=f"unit_{index}"
        )
        if new_unit != current_unit:
            update_sheet(index, "select_unit", new_unit)
            st.success(f"Unit updated for {row['name']} → {new_unit}")
            sleep(1)

        # Editable user
        current_user = row["user"]
        new_user = cols[8].text_input(
            "User",
            value=current_user,
            key=f"user_{index}"
        )
        if new_user != current_user:
            update_sheet(index, "user", new_user)
            st.success(f"User updated for {row['name']} → {new_user}")
            sleep(1)

        # LinkedIn + CV button
        btn_col = cols[9]
        if pd.notnull(row["linkedin"]) and row["linkedin"] != "":
            btn_col.link_button("🔗 LinkedIn", row["linkedin"])
        if pd.notnull(row["cv"]) and row["cv"] != "":
            btn_col.link_button("📄 CV", row["cv"])
