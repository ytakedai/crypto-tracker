# README

### Steps
1. For Coinbase or Coinbase Pro, generate reports (down below) and paste them in folder `reports`.
1. For manual entry, fill out trade data in a csv file (or multiple) in folder `reports`, with the first row being `Timestamp,Transaction Type,Asset,Size,Price,Fees`
1. Set value for `YEAR` var in `runner.py`
1. Set `FILTER_YEAR` to `True`/`False` depending on if you want a detailed report on a specific year or overall
1. Run script using `python3 runner.py`

### Python Libraries (Mac OS)
- pandas
  1. Install [pip](https://www.geeksforgeeks.org/how-to-install-pip-in-macos/) if you haven't already
  1. Install pandas: `pip install pandas`

## Report Generation

### Coinbase
1. Proceed to https://www.coinbase.com/reports and click on `Generate Report`.
1. Click on `Generate Report` for CSV report.

### Coinbase Pro
1. Proceed to https://pro.coinbase.com/profile/statements and click on `Generate > Fills`
1. Move `Start Date` to earliest date of your first trade or earlier
1. Change format to `CSV`
1. Click on `Generate Report`