import streamlit as st
from time import sleep
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

@st.cache_resource()
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

    required_columns = ["name", "email", "universitas", "major", "whatsapp", "linkedin", "instagram", "cv", "code", "portofolio", "Status"]
    df_talent = df_talent[required_columns]

    return df_talent


def update_status(index, new_status):
    secret_info = st.secrets["sheets"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('Talent Pool Database')
    sheet = spreadsheet.sheet1

    # Find the status column index
    status_col = len(sheet.row_values(1)) + 1
    sheet.update_cell(1, status_col, "Status")  # Add header if not present
    sheet.update_cell(index + 2, status_col, new_status)  # Update row


st.set_page_config(layout="wide")
df_talent = fetch_data_talent()
st.header('Talent Pool Database', divider="blue")

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
editable_columns = ["name", "email", "universitas", "major", "whatsapp", "Status"]

# Pagination setup
page_size = 10  # Number of rows per page
total_pages = (len(filtered_df) // page_size) + (1 if len(filtered_df) % page_size != 0 else 0)
page_number = st.selectbox("Select Page", list(range(1, total_pages + 1)))

# Get the data for the current page
start_idx = (page_number - 1) * page_size
end_idx = start_idx + page_size
page_data = filtered_df.iloc[start_idx:end_idx]

statuses = ["Accepted", "Waiting", "Rejected"]

# Editable table layout
st.subheader("Editable Table")

for index, row in page_data.iterrows():
    cols = st.columns(len(editable_columns) + 2)  # +2 for LinkedIn and CV buttons
    row_index = row["name"]  # Use name as the row identifier

    # Display columns with editable fields
    for i, col_name in enumerate(editable_columns):
        if col_name == "Status":
            # Editable status dropdown
            current_status = row[col_name]
            new_status = cols[i].selectbox(f"Status for {row_index}", statuses, index=statuses.index(current_status), key=f"status_{index}")
            if new_status != current_status:
                update_status(index, new_status)
                st.success(f"Status updated for {row_index} to {new_status}")
                sleep(1)
        else:
            # Display other fields as text
            cols[i].write(row[col_name])

    # LinkedIn button
    if pd.notnull(row["linkedin"]):
        if cols[-2].button("🔗 LinkedIn", key=f"linkedin_{index}"):
            st.markdown(f"[View LinkedIn Profile]({row['linkedin']})", unsafe_allow_html=True)

    # CV button
    if pd.notnull(row["cv"]):
        if cols[-1].button("📄 CV", key=f"cv_{index}"):
            st.markdown(f"[Download CV]({row['cv']})", unsafe_allow_html=True)

