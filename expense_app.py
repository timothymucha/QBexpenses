import streamlit as st
import pandas as pd
import csv
from io import StringIO
from datetime import datetime

# Map categories to expense/COGS accounts
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

# Map payment type to bank account
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

# Parse amount to float
def parse_amount(value):
    try:
        return float(str(value).replace("Ksh", "").replace(",", "").replace(" ", "").strip())
    except:
        return 0.0

# Convert to QuickBooks-compatible IIF
def convert_to_iif(df):
    output = StringIO()
    writer = csv.writer(output, delimiter='\t', lineterminator='\n')

    # IIF headers
    writer.writerow(["!TRNS", "TRNSTYPE", "DATE", "ACCNT", "NAME", "AMOUNT", "DOCNUM", "MEMO"])
    writer.writerow(["!SPL", "TRNSTYPE", "DATE", "ACCNT", "NAME", "AMOUNT", "DOCNUM",
                     "MEMO", "QNTY", "PRICE", "CLASS", "TAXABLE", "INVITEM"])
    writer.writerow(["!ENDTRNS"])

    df = df[df['Amount'].notnull()]

    for i, row in df.iterrows():
        raw_amount = parse_amount(row['Amount'])
        category = str(row.get('Category', '')).strip()
        is_adjustment = category.lower() == "express adjustments"

        # For "Express adjustments", only include payouts (negatives from bank)
        if is_adjustment and raw_amount >= 0:
            continue

        # All are payouts from the bank, so treat amount as negative outflow
        amount = abs(raw_amount)

        account = map_category_to_account(category)
        pay_account = map_payment_account(row.get('PAYMENT', ''))
        name = str(row.get('Column 1', '')).strip() or "Walk In"
        docnum_src = str(row.get('Tracking No', '')).strip()
        docnum = f"EXP-{docnum_src.replace(' ', '').replace('/', '-')}" if docnum_src else f"EXP-{i}"
        memo = category

        try:
            date = pd.to_datetime(row['Date']).strftime('%m/%d/%Y')
        except:
            date = ""

        # TRNS = money going out of bank
        writer.writerow(["TRNS", "CHECK", date, pay_account, name, -amount, docnum, memo])

        # SPL = expense or COGS
        writer.writerow(["SPL", "CHECK", date, account, name, amount, docnum, memo, "", "", "", "N", ""])

        writer.writerow(["ENDTRNS"])

    return output.getvalue()

# Streamlit UI
st.set_page_config(page_title="Bank Statement to IIF", layout="centered")
st.title("🔁 Bank/Expense Statement to QuickBooks IIF")
st.markdown("""
This tool converts your uploaded expense or bank statement into **QuickBooks .IIF format** for import.

- Uses the correct accounts for categories like *Pastries*, *Salaries*, *Paper cups*, etc.  
- Filters **Express adjustments** to include only **payouts**  
- Payee defaults to **Column 1** or **"Walk In"**  
""")

uploaded_file = st.file_uploader("📤 Upload your CSV file", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File uploaded successfully!")
    st.dataframe(df.head(10))

    if st.button("🚀 Convert and Download IIF"):
        iif_data = convert_to_iif(df)
        st.download_button("📥 Download IIF File", iif_data, file_name="expenses_converted.iif", mime="text/plain")
