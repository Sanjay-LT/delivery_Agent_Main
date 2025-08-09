import pandas as pd
import random
from datetime import datetime, timedelta

# Generate fake deliveries data
num_deliveries = 10
delivery_ids = [f"D{1000+i}" for i in range(num_deliveries)]
statuses = ["Completed", "Pending"]
addresses = [
    "12 MG Road, Chennai, TN",
    "45 Anna Salai, Chennai, TN",
    "78 Gandhi Street, Coimbatore, TN",
    "23 Marina Road, Chennai, TN",
    "90 Park Avenue, Madurai, TN",
    "34 Hill View, Salem, TN",
    "56 Green Street, Trichy, TN",
    "11 Lake Road, Chennai, TN",
    "67 River Side, Erode, TN",
    "88 Flower Street, Vellore, TN"
]
customers = [
    "Ravi Kumar", "Sita Devi", "Arun Prasad", "Priya Sharma", "Manoj Babu",
    "Kavya Nair", "Ramesh R", "Deepa K", "Suresh V", "Lakshmi Menon"
]

# Generate delivery data
deliveries_data = []
earnings_data = []
feedback_data = []

for i in range(num_deliveries):
    date_assigned = datetime.now() - timedelta(days=random.randint(1, 30))
    status = random.choice(statuses)
    earning = round(random.uniform(50, 200), 2) if status == "Completed" else 0.0
    
    deliveries_data.append({
        "Delivery ID": delivery_ids[i],
        "Customer Name": customers[i],
        "Address": addresses[i],
        "Status": status,
        "Date Assigned": date_assigned.strftime("%Y-%m-%d"),
        "Date Completed": (date_assigned + timedelta(days=random.randint(1, 3))).strftime("%Y-%m-%d") if status == "Completed" else "",
        "Earnings (₹)": earning
    })
    
    earnings_data.append({
        "Delivery ID": delivery_ids[i],
        "Date": date_assigned.strftime("%Y-%m-%d"),
        "Amount (₹)": earning
    })
    
    feedback_data.append({
        "Delivery ID": delivery_ids[i],
        "Customer Name": customers[i],
        "Feedback": random.choice([
            "Great service!", "On time delivery.", "Very polite.", 
            "Package was slightly damaged.", "Fast and efficient."
        ]) if status == "Completed" else ""
    })

# Convert to DataFrames
df_deliveries = pd.DataFrame(deliveries_data)
df_earnings = pd.DataFrame(earnings_data)
df_feedback = pd.DataFrame(feedback_data)

# Save to Excel file with multiple sheets
output_path = "data/nomii_delivery_fake_data.xlsx"
with pd.ExcelWriter(output_path) as writer:
    df_deliveries.to_excel(writer, sheet_name="Deliveries", index=False)
    df_earnings.to_excel(writer, sheet_name="Earnings", index=False)
    df_feedback.to_excel(writer, sheet_name="Feedback", index=False)

output_path
