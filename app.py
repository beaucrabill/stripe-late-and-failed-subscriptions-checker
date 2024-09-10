import os
import sys
from datetime import datetime, timezone
from google.oauth2 import service_account

# Get the directory of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Try to import required libraries
try:
    import stripe
    from googleapiclient.discovery import build
except ImportError as e:
    print(f"Failed to import required libraries: {e}")
    print("Make sure you've activated the virtual environment:")
    print("source /root/late_payments_venv/bin/activate")
    print("Then run: pip install stripe google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# Load configuration
def load_config():
    config_path = os.path.join(SCRIPT_DIR, 'config.json')
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    import json
    with open(config_path, 'r') as config_file:
        return json.load(config_file)

config = load_config()

# Stripe API Key
stripe.api_key = os.getenv('STRIPE_API_KEY') or config.get('stripe_api_key')
if not stripe.api_key:
    raise ValueError("Stripe API key is not set")

# Google Sheets configuration
SPREADSHEET_ID = config.get('spreadsheet_id')
SHEET_ID = config.get('sheet_id')

def get_google_service():
    creds_path = os.path.join(SCRIPT_DIR, config.get('google_cloud_creds_path', 'creds.json'))
    creds = service_account.Credentials.from_service_account_file(
        creds_path, 
        scopes=['https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive.file']
    )
    return build('sheets', 'v4', credentials=creds)

def update_google_sheet(sheets_service, spreadsheet_id, sheet_id, values):
    spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_name = next(sheet['properties']['title'] for sheet in spreadsheet['sheets'] 
                      if sheet['properties']['sheetId'] == int(sheet_id))
    
    now = datetime.now(timezone.utc)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Add "Last Updated At" and "Days Overdue" columns
    values[0].extend(["Last Updated At", "Days Overdue"])
    for row in values[1:]:
        row.append(now_str)
        if row[-2] and row[-2] != 'N/A':  # Check if Original Due Date exists and is not 'N/A'
            original_due_date = datetime.fromtimestamp(row[-2], timezone.utc)
            row[-2] = original_due_date.strftime("%Y-%m-%d %H:%M:%S UTC")  # Format Original Due Date
            days_overdue = (now - original_due_date).days
            row.append(str(days_overdue))
        else:
            row.append('N/A')  # If no valid Original Due Date, set Days Overdue to 'N/A'

    body = {
        'values': values
    }
    result = sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=f"'{sheet_name}'!A1",
        valueInputOption='USER_ENTERED', body=body).execute()
    print(f"{result.get('updatedCells')} cells updated in sheet '{sheet_name}'.")

def fetch_stripe_data():
    late_subscriptions = [['Subscription ID', 'Status', 'Customer ID', 'Customer Email', 'Amount Due', 'Currency', 'Original Due Date']]
    total_subscriptions = 0

    subscriptions = stripe.Subscription.list(status='all', limit=100)

    for subscription in subscriptions.auto_paging_iter():
        total_subscriptions += 1
        if subscription.status in ['past_due', 'unpaid']:
            latest_invoice_id = subscription.latest_invoice
            if latest_invoice_id:
                latest_invoice = stripe.Invoice.retrieve(latest_invoice_id)
                amount_due = latest_invoice.amount_due / 100
                original_due_date = latest_invoice.created  # Use the invoice creation date
            else:
                amount_due = 'N/A'
                original_due_date = None

            customer = stripe.Customer.retrieve(subscription.customer)
            customer_email = customer.email if customer.email else 'N/A'

            late_subscriptions.append([
                subscription.id,
                subscription.status,
                subscription.customer,
                customer_email,
                amount_due,
                subscription.currency.upper(),
                original_due_date  # This is now the correct original due date
            ])
        
        if total_subscriptions % 10 == 0:
            print(f"Processed {total_subscriptions} subscriptions...")

    print(f"Processed a total of {total_subscriptions} subscriptions.")
    print(f"Found {len(late_subscriptions) - 1} late subscriptions.")
    
    return late_subscriptions

def main():
    try:
        sheets_service = get_google_service()

        print("Fetching data from Stripe...")
        late_subscriptions = fetch_stripe_data()

        print("Updating Google Sheet...")
        update_google_sheet(sheets_service, SPREADSHEET_ID, SHEET_ID, late_subscriptions)

        print("Process completed successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()