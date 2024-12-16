import streamlit as st
import pandas as pd
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime, timedelta

# ------------------ Excel File Path ------------------
EXCEL_FILE = 'Daily_Metric_Tracking_Sheet (1).xlsx'  # Path to your Excel file

# ------------------ Watchdog for Auto-Reload ------------------
class ExcelFileHandler(FileSystemEventHandler):
    """Detects changes in the Excel file and reloads data."""
    def __init__(self, reload_callback):
        self.reload_callback = reload_callback

    def on_modified(self, event):
        if event.src_path.endswith(EXCEL_FILE):
            self.reload_callback()

def watch_file(callback):
    event_handler = ExcelFileHandler(callback)
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=False)
    observer.start()

# ------------------ Load and Process Data ------------------
@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=0)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return pd.DataFrame()

def calculate_metrics(df):
    """Calculate overall metrics for the dashboard."""
    metrics = {
        "Avg Minutes of Work": round(df["Minutes of Total Video Work Done (min)"].mean(), 2),
        "Words Translated": f"{df['Words Translated (nos.)'].sum():,}"
    }
    return metrics

def get_daily_comparison(df):
    """Fetch today's and yesterday's values for Minutes of Video Localized (Paid)."""
    try:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        today_minutes = df[df['Date'] == today]['Minutes of Video Localized (min) - Paid'].sum()
        yesterday_minutes = df[df['Date'] == yesterday]['Minutes of Video Localized (min) - Paid'].sum()
        
        return today_minutes, yesterday_minutes
    except Exception as e:
        st.error(f"Error calculating daily comparison: {e}")
        return 0, 0

def get_clients_on_date(df, date):
    """Fetch 'Total Number of Clients (nos.) - Platform Users' for a specific date."""
    try:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        total_clients = df[df['Date'] == date]['Total Number of Clients (nos.) - Platform Users'].sum()
        return total_clients
    except Exception as e:
        st.error(f"Error fetching clients onboarded: {e}")
        return 0

# ------------------ Streamlit UI ------------------
def main():
    st.set_page_config(page_title="Daily Metrics Dashboard", layout="wide")
    st.title("📊 Daily Metric Tracking Dashboard")

    if 'data' not in st.session_state:
        st.session_state['data'] = load_data()

    def reload_data():
        st.session_state['data'] = load_data()
        st.experimental_rerun()

    watch_file(reload_data)

    data = st.session_state['data']
    metrics = calculate_metrics(data)

    today_minutes, yesterday_minutes = get_daily_comparison(data)
    clients_today = get_clients_on_date(data, datetime.now().date())
    client_yesterday = get_clients_on_date(data, datetime.now().date() - timedelta(days=1))

    if today_minutes > yesterday_minutes:
        arrow = "⬆️"
        delta_color = "normal"
    else:
        arrow = "⬇️"
        delta_color = "inverse"

    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg Minutes of Work", metrics["Avg Minutes of Work"])
    col2.metric("Total Words Translated", metrics["Words Translated"])
    col3.metric("Minutes Localized (Paid)", f"{yesterday_minutes} min", f"{arrow} {abs(today_minutes - yesterday_minutes)}", delta_color=delta_color)
    col4.metric("Total Clients Onboarded", client_yesterday)

    st.subheader("📄 Detailed Data")
    st.dataframe(data)

    st.info("🔄 The dashboard updates automatically when changes are detected in the Excel file.")

if __name__ == "__main__":
    main()
