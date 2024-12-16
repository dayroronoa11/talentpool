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
    expected_headers = ["name", "email", "universitas", "major", "whatsapp", "linkedin", "instagram", "cv", "code", "portofolio", "Status"]

    data = sheet.get_all_records(expected_headers=expected_headers)

    if not data:
        st.error("No data found in the sheet.")
        return pd.DataFrame()

    df_talent = pd.DataFrame(data)

    # Ensure the DataFrame only contains the required columns
    df_talent = df_talent[expected_headers]

    return df_talent

def update_status(index, new_status):
    secret_info = st.secrets["sheets"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_info, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('Talent Pool Database')
    sheet = spreadsheet.sheet1

    # Find the column index for "Status"
    headers = sheet.row_values(1)  # Get the header row
    if "Status" not in headers:
        st.error("No 'Status' column found in the spreadsheet.")
        return

    status_col = headers.index("Status") + 1  # Convert to 1-based index

    # Update the corresponding cell
    sheet.update_cell(index + 2, status_col, new_status)  # `index + 2` accounts for header and zero-indexing


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

# Status options
statuses = ["Open to Work", "Process in Unit", "Offering", "Hired"]

# Editable table layout
st.subheader("Editable Table")

# Add a download button for the filtered data
if not filtered_df.empty:
    # Convert the filtered DataFrame to CSV
    csv_data = filtered_df.to_csv(index=False)
    
    # Add the download button
    st.download_button(
        label="📥 Download Filtered Data",
        data=csv_data,
        file_name="filtered_talent_data.csv",
        mime="text/csv",
    )
else:
    st.info("No data available to download.")


for index, row in filtered_df.iterrows():
    cols = st.columns(len(editable_columns) + 1)  # +1 for the links column
    row_index = row["name"]  # Use name as the row identifier

    # Display columns with editable fields
    for i, col_name in enumerate(editable_columns):
        if col_name == "Status":
            # Editable status dropdown
            current_status = row[col_name]

            # Ensure current_status is valid or set it to a default status if invalid
            if current_status not in statuses:
                current_status = "Open to Work"  # Default status

            new_status = cols[i].selectbox(f"Status for {row_index}", statuses, index=statuses.index(current_status), key=f"status_{index}")
            if new_status != current_status:
                update_status(index, new_status)
                st.success(f"Status updated for {row_index} to {new_status}")
                sleep(1)
        else:
            # Display other fields as text
            cols[i].write(row[col_name])

    # Display hyperlinks for LinkedIn and CV
    links = []
    if pd.notnull(row["linkedin"]):
        links.append(f"[LinkedIn]({row['linkedin']})")
    if pd.notnull(row["cv"]):
        links.append(f"[CV]({row['cv']})")

    cols[-1].markdown(" | ".join(links), unsafe_allow_html=True)
