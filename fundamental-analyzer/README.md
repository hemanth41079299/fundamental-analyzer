# Fundamental Analyzer

Fundamental Analyzer is a local Streamlit equity research platform. It combines rule-based company analysis with a persistent SQLite portfolio tracker and a broker-style portfolio dashboard.

## Features

- PDF upload and label-based metric extraction
- Company search using `yfinance`
- Editable default and custom rule frameworks by market-cap bucket
- Rule evaluation, scorecard, risk scan, suggestion layer, valuation analysis, earnings quality checks, red flag detection, narration, and thesis generation
- Financial trend charts with Plotly
- Portfolio CSV analyzer and Screener CSV bulk analysis
- Persistent portfolio manager backed by SQLite
- Local authentication with hashed passwords
- Secure PDF uploads with user-scoped storage
- Audit logging for key account and portfolio actions
- Company research history stored locally as JSON

## Workspaces

The app has two top-level workspaces in the sidebar.

### Company Analysis

Use this workspace to:

- upload a PDF report
- search a listed company by ticker
- analyze one-off portfolio CSV files
- analyze Screener export CSV files
- edit rule profiles

### Portfolio Manager

Use this workspace to maintain a personal investment ledger over time.

Sections:

1. Dashboard
2. Transactions
3. Holdings
4. Cash
5. Watchlist
6. Allocation
7. History
8. Import / Export

The Portfolio Manager dashboard is an original implementation inspired by modern broker dashboards. It follows a similar information architecture, but it does not copy any third-party branding or proprietary styling.

## Portfolio Tracking Model

Portfolio data is stored locally in SQLite at:

`data/portfolio.db`

Tables:

- `transactions`
- `watchlist`
- `cash_ledger`
- `portfolio_snapshots`

No broker sync is used. All entries are manual or imported from CSV.

## Authentication

The app includes a local authentication layer backed by the same SQLite database.

Supported account features:

- register with name, email, and password
- login with email and password
- logout
- change password from the settings page

Passwords are stored as bcrypt hashes through `passlib`. Plain text passwords are not stored.
Passwords are truncated to bcrypt's 72-byte limit before hashing and verification.

Public pages:

- Login
- Register

Protected pages:

- Company Analysis
- Portfolio Manager dashboard
- Portfolio transactions
- Holdings
- Cash
- Watchlist
- Allocation
- Portfolio history
- Import / Export
- Rules editor
- Upload-based analysis
- Company research history
- Settings

If a user is not logged in, protected views are not rendered.

## Upload Security And Audit Logging

Uploaded PDF files are validated for:

- file type
- file size
- unsafe filenames

Accepted uploads are stored under a user-specific folder inside `uploads/`.

The app also records audit events for key actions such as:

- register
- login
- logout
- PDF upload
- add transaction
- save rules
- save snapshot

## Portfolio Workflow

### Transactions

Add `BUY` and `SELL` transactions with:

- date
- ticker
- company name
- quantity
- price
- charges
- notes

Validation rules:

- date required
- ticker required
- quantity must be greater than `0`
- price must be greater than `0`
- charges cannot be negative
- `SELL` quantity cannot exceed available holdings

### Holdings Calculation

Holdings are computed dynamically from the transaction ledger using the average-cost method.

For each holding, the app calculates:

- total bought quantity
- total sold quantity
- net quantity
- average buy price
- invested amount
- realized P&L
- current market price
- current value
- unrealized P&L

Formulas used:

- `Net Quantity = Total Buy Quantity - Total Sell Quantity`
- `Average Buy Price = Remaining Cost Basis / Net Quantity`
- `Invested Amount = Net Quantity x Average Buy Price`
- `Current Value = Net Quantity x LTP`
- `Unrealized P&L = Current Value - Invested Amount`

Realized P&L uses the average-cost method, not FIFO.

For sell transactions:

- `Realized P&L = (Sell Price - Average Cost At Sale) x Quantity Sold - Charges`

Charges are included in the cost basis to keep the model simple.

## Portfolio Dashboard Layout

The default landing page inside Portfolio Manager is the dashboard.

Dashboard sections:

1. Header with last updated timestamp and portfolio status summary
2. KPI row for invested amount, current value, unrealized P&L, realized P&L, cash balance, and total net worth
3. Large portfolio performance chart using snapshot history
4. Account overview and allocation visuals
5. Styled holdings table with suggestion and risk labels
6. Portfolio insights cards
7. Research widgets based on the existing analysis engine

Dashboard actions:

- `Refresh Prices`
- `Save Snapshot`
- `Download Holdings CSV`

If the portfolio is empty, the dashboard shows a clean empty state with quick actions for transactions, import, and watchlist management.

### Cash Ledger

The cash ledger stores manual:

- `DEPOSIT`
- `WITHDRAWAL`

Cash balance is:

- `Total Deposits - Total Withdrawals`

Cash is included in portfolio net worth and asset allocation.

### Watchlist

The watchlist is separate from actual holdings.

It supports:

- adding tickers
- storing company names
- saving notes
- removing entries

Duplicate tickers are blocked.

### Portfolio Snapshots

Snapshots can be saved manually from the History section.

Each snapshot stores:

- invested amount
- portfolio value
- unrealized P&L
- realized P&L
- cash balance
- total net worth

The app also attempts to auto-save one snapshot per day when the Portfolio Manager workspace is opened.

## Allocation Analysis

The portfolio manager shows:

- stock-wise allocation
- sector-wise allocation
- asset allocation
- top holdings bar chart

Current asset classes:

- Equity
- Cash

Sector values are fetched from the existing web data service when available. If the sector is missing, the holding is grouped under `Unknown`.

## Import / Export

Import supported:

- transactions CSV
- watchlist CSV

Export supported:

- transactions CSV
- watchlist CSV
- holdings CSV
- portfolio snapshot summary CSV
- cash ledger CSV

Invalid CSV schema is rejected with a friendly error.

## Project Structure

```text
fundamental-analyzer/
├── app.py
├── requirements.txt
├── README.md
├── config/
├── core/
├── models/
├── services/
│   ├── bulk_analysis_service.py
│   ├── cash_service.py
│   ├── history_service.py
│   ├── holdings_service.py
│   ├── pdf_service.py
│   ├── portfolio_db.py
│   ├── portfolio_service.py
│   ├── portfolio_snapshot_service.py
│   ├── report_service.py
│   ├── rule_service.py
│   ├── transaction_service.py
│   ├── watchlist_service.py
│   └── web_data_service.py
├── ui/
│   ├── allocation_section.py
│   ├── bulk_analysis_section.py
│   ├── cash_ledger_section.py
│   ├── charts_section.py
│   ├── earnings_quality_section.py
│   ├── holdings_table.py
│   ├── history_section.py
│   ├── import_export_section.py
│   ├── metrics_table.py
│   ├── narration_section.py
│   ├── portfolio_dashboard.py
│   ├── portfolio_history_section.py
│   ├── portfolio_section.py
│   ├── red_flags_section.py
│   ├── results_section.py
│   ├── rules_editor.py
│   ├── suggestion_section.py
│   ├── transaction_form.py
│   ├── upload_section.py
│   ├── valuation_section.py
│   └── watchlist_section.py
├── data/
│   ├── company_history/
│   ├── examples/
│   └── portfolio.db
├── uploads/
├── outputs/
└── tests/
```

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

The app usually opens on [http://localhost:8501](http://localhost:8501).

## Example Files

- Portfolio sample: [portfolio_example.csv](/Users/hemanthkumar/Desktop/equity analysis/fundamental-analyzer/data/examples/portfolio_example.csv)
- Screener sample: [screener_example.csv](/Users/hemanthkumar/Desktop/equity analysis/fundamental-analyzer/data/examples/screener_example.csv)

## Notes

- `sqlite3` is part of the Python standard library, so no extra database package is required.
- `yfinance` and `plotly` must be installed for company search and charts.
- If live market data is unavailable, holdings are still shown and market-dependent fields stay blank instead of failing.
- This is a personal portfolio tracking tool. It does not sync with a broker or exchange account.
- The portfolio dashboard visual structure is inspired by modern broker dashboards, but the implementation and styling are original to this project.

## Tests

```bash
python3 -m pytest
```
