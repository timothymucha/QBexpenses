
import streamlit as st
import pandas as pd
import csv
from io import StringIO
from datetime import datetime

def map_category_to_account(category):
    category = str(category).strip().lower()
    if category == "express adjustments":
        return "Cost of Goods Sold:Coffee House"
    elif category == "events charges":
        return "Cost of Goods Sold:Event Sales"
    elif category == "salaries" or "salary advance" in category:
        return "Staffing Costs:Payroll Expenses"
    elif category == "licences":
        return "Business Licenses and Permits"
    elif category == "paper cups" or "naivas" in category:
        return "Miscellenious expenses"
    elif category == "pastries":
        return "Cost of Goods Sold:Coffee House"
    elif category == "airtime":
        return "Utilities"
    elif category == "ice-cream" or category == "sauce":
        return "Cost of Goods Sold:Coffee House"
    else:
        return "Ask My Accountant"

def map_payment_account(payment_type):
    payment_type = str(payment_type).strip().lower()
    if payment_type == "mpesa":
        return "MPesa"
    elif payment_type == "cash":
        return "Cash in Drawer"
    elif payment_type == "visa card":
        return "Visa"
    else:
        return "Undeposited Funds"

def parse_amount(value):
    try:
        return float(str(value).replace("Ksh", "").replace(",", "").replace(" ", "").strip())
    except:
        return 0.0

def convert_to_iif(df):
    output = StringIO()
    writer = csv.writer(output, delimiter='\t', lineterminator='\n')
    writer.writerow(["!TRNS", "TRNSTYPE", "DATE", "ACCNT", "NAME", "AMOUNT", "DOCNUM", "MEMO"])
    writer.writerow(["!SPL", "TRNSTYPE", "DATE", "ACCNT", "NAME", "AMOUNT", "DOCNUM",
                     "MEMO", "QNTY", "PRICE", "CLASS", "TAXABLE", "INVITEM"])

    df = df[df['Amount'].notnull()]

    for i, row in df.iterrows():
        amount = parse_amount(row['Amount'])
        category = str(row.get('Category', '')).strip()
        is_adjustment = category.lower() == "express adjustments"

        # For "Express adjustments", only include negative (paid out) entries
        if is_adjustment and amount >= 0:
            continue

        category = row['Category']
        account = map_category_to_account(category)
        pay_account = map_payment_account(row.get('PAYMENT', ''))
        name = str(row.get('Column 1', '')).strip() or "Walk In"
        docnum_src = str(row.get('Tracking No', '')).strip()
        docnum = f"EXP-{docnum_src.replace(' ', '').replace('/', '-')}" if docnum_src else f"EXP-{i}"
        memo = str(category)
        try:
            date = pd.to_datetime(row['Date']).strftime('%m/%d/%Y')
        except:
            date = ""

        # TRNS row: Bank/Cash payment out
        writer.writerow(["TRNS", "CHECK", date, pay_account, name, amount, docnum, memo])

        # SPL row: Expense or COGS
        writer.writerow(["SPL", "CHECK", date, account, name, -amount, docnum, memo, "", "", "", "N", ""])

        writer.writerow(["ENDTRNS"])

    return output.getvalue()

st.title("Expense Listing to QuickBooks IIF Converter")
st.write("This tool converts your CSV Expense Listing into QuickBooks-compatible IIF format.")

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Preview:", df.head())

    if st.button("Convert and Download IIF"):
        iif_data = convert_to_iif(df)
        st.download_button("Download .iif File", iif_data, file_name="converted_expenses.iif", mime="text/plain")
