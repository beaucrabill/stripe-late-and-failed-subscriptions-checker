# Stripe Late Payments Tracker

This project is designed to track late payments from Stripe and update a Google Sheet with the information.

## Prerequisites

Before you can use this script, you need to set up a few things:

1. A Stripe account with API access
2. A Google Cloud account with a service account
3. A Google Sheet to store the late payment information

## Setup

### Google Cloud Service Account

1. Set up a Google service account. You can read more about this process [here](https://cloud.google.com/iam/docs/service-account-creds).
2. Once you have a service account, you will need to add the service account email to your Google Sheet with full edit access. In your credentials file, it should look like this:
   ```json
   "client_email": "app-name@app-name.iam.gserviceaccount.com"
   ```

### Configuration

1. Create a `config.json` file in the root directory with the following structure:
   ```json
   {
     "stripe_api_key": "your_stripe_api_key_here",
     "spreadsheet_id": "your_spreadsheet_id_here",
     "sheet_id": "your_sheet_id_here",
     "google_cloud_creds_path": "creds.json"
   }
   ```
2. Create a `creds.json` file with your Google Cloud service account credentials.

**Note:** Both `config.json` and `creds.json` are ignored by git for security reasons. Never commit these files to your repository.

## Usage

Run the script with:

```
python main.py
```

This will fetch late payment information from Stripe and update your Google Sheet.

## Rate Limits

Please be aware of Stripe's rate limits when using this script. You can read more about Stripe's rate limits [here](https://docs.stripe.com/rate-limits).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
