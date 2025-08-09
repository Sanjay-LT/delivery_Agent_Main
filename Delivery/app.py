from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import pandas as pd
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_to_excel(data, filename, sheet_name='Sheet1'):
    filepath = f'data/{filename}'
    try:
        if os.path.exists(filepath):
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        else:
            df = pd.DataFrame([data])
        with pd.ExcelWriter(filepath, engine='openpyxl', mode='a' if os.path.exists(filepath) else 'w') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    except Exception as e:
        print(f"Error saving to {filename}: {e}")

def get_user_deliveries(delivery_id):
    try:
        df = pd.read_excel('data/nomii_delivery_fake_data.xlsx', sheet_name='Deliveries')
        return df[df['Delivery ID'] == delivery_id].to_dict('records')
    except Exception as e:
        print(f"Error reading deliveries: {e}")
        return []

def get_user_earnings(delivery_id):
    try:
        df = pd.read_excel('data/nomii_delivery_fake_data.xlsx', sheet_name='Earnings')
        return df[df['Delivery ID'] == delivery_id].to_dict('records')
    except Exception as e:
        print(f"Error reading earnings: {e}")
        return []

def get_user_feedback(delivery_id):
    try:
        df = pd.read_excel('data/nomii_delivery_fake_data.xlsx', sheet_name='Feedback')
        df = df[(df['Delivery ID'] == delivery_id) & (df['Feedback'] != '')]
        return df.to_dict('records')
    except Exception as e:
        print(f"Error reading feedback: {e}")
        return []

def update_delivery_status(delivery_id, order_id, status, proof=None, remarks=None):
    try:
        df = pd.read_excel('data/nomii_delivery_fake_data.xlsx', sheet_name='Deliveries')
        df.loc[(df['Delivery ID'] == delivery_id) & (df.index == int(order_id[1:])), 'Status'] = status
        if status == 'Completed':
            df.loc[(df['Delivery ID'] == delivery_id) & (df.index == int(order_id[1:])), 'Date Completed'] = datetime.now().strftime("%Y-%m-%d")
        
        if status == 'Completed':
            earnings_df = pd.read_excel('data/nomii_delivery_fake_data.xlsx', sheet_name='Earnings')
            new_earning = {
                'Delivery ID': delivery_id,
                'Date': datetime.now().strftime("%Y-%m-%d"),
                'Amount (₹)': df.loc[(df['Delivery ID'] == delivery_id) & (df.index == int(order_id[1:])), 'Earnings (₹)'].values[0]
            }
            earnings_df = pd.concat([earnings_df, pd.DataFrame([new_earning])], ignore_index=True)
        
        if status == 'Completed':
            feedback_df = pd.read_excel('data/nomii_delivery_fake_data.xlsx', sheet_name='Feedback')
            new_feedback = {
                'Delivery ID': delivery_id,
                'Customer Name': df.loc[(df['Delivery ID'] == delivery_id) & (df.index == int(order_id[1:])), 'Customer Name'].values[0],
                'Feedback': remarks if remarks else 'No feedback provided'
            }
            feedback_df = pd.concat([feedback_df, pd.DataFrame([new_feedback])], ignore_index=True)
        
        with pd.ExcelWriter('data/nomii_delivery_fake_data.xlsx') as writer:
            df.to_excel(writer, sheet_name='Deliveries', index=False)
            if status == 'Completed':
                earnings_df.to_excel(writer, sheet_name='Earnings', index=False)
                feedback_df.to_excel(writer, sheet_name='Feedback', index=False)
            else:
                pd.DataFrame().to_excel(writer, sheet_name='Earnings')
                pd.DataFrame().to_excel(writer, sheet_name='Feedback')
        
        return True
    except Exception as e:
        print(f"Error updating delivery status: {e}")
        return False

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        aadhaar = request.form['aadhaar']
        address = request.form['address']
        email = request.form['email']
        password = request.form['password']
        vehicle_type = request.form['vehicle_type']
        vehicle_number = request.form['vehicle_number']
        
        id_proof = None
        photo = None
        
        if 'id_proof' in request.files:
            file = request.files['id_proof']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"id_proof_{uuid.uuid4().hex}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                id_proof = filename
        
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"photo_{uuid.uuid4().hex}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo = filename
        
        delivery_id = f"D{str(uuid.uuid4().int)[:4]}"
        
        user_data = {
            "DeliveryID": delivery_id,
            "Name": name,
            "Phone": phone,
            "Aadhaar": aadhaar,
            "Address": address,
            "Email": email,
            "Password": password,
            "VehicleType": vehicle_type,
            "VehicleNumber": vehicle_number,
            "IDProof": id_proof,
            "Photo": photo
        }
        
        save_to_excel(user_data, 'delivery_users.xlsx', sheet_name='Users')
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            df = pd.read_excel('data/delivery_users.xlsx', sheet_name='Users')
            user = df[(df['Email'] == email) & (df['Password'] == password)]
            
            if not user.empty:
                user_data = user.iloc[0].to_dict()
                session['delivery_id'] = user_data['DeliveryID']
                session['name'] = user_data['Name']
                session['email'] = user_data['Email']
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password', 'danger')
        except Exception as e:
            print(f"Login error: {e}")
            flash('Login failed. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    delivery_id = session.get('delivery_id', 'D0000')
    
    deliveries = get_user_deliveries(delivery_id)
    
    total_deliveries = len(deliveries)
    completed_deliveries = len([d for d in deliveries if d.get('Status') == 'Completed'])
    pending_deliveries = total_deliveries - completed_deliveries
    
    earnings = get_user_earnings(delivery_id)
    total_earnings = sum(float(e.get('Amount (₹)', 0)) for e in earnings)
    
    feedback = get_user_feedback(delivery_id)
    
    return render_template('dashboard.html', 
                         deliveries=deliveries,
                         total_deliveries=total_deliveries,
                         completed_deliveries=completed_deliveries,
                         pending_deliveries=pending_deliveries,
                         earnings=earnings,
                         total_earnings=total_earnings,
                         feedback=feedback)

@app.route('/deliveries')
def deliveries():
    delivery_id = session.get('delivery_id', 'D0000')
    deliveries = get_user_deliveries(delivery_id)
    return render_template('deliveries.html', deliveries=deliveries)

@app.route('/update_status/<order_id>', methods=['GET', 'POST'])
def update_status(order_id):
    delivery_id = session.get('delivery_id', 'D0000')
    
    if request.method == 'POST':
        status = request.form['status']
        remarks = request.form.get('remarks', '')
        proof = None
        
        if 'proof' in request.files:
            file = request.files['proof']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"proof_{uuid.uuid4().hex}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                proof = filename
        
        if update_delivery_status(delivery_id, order_id, status, proof, remarks):
            flash('Delivery status updated successfully!', 'success')
        else:
            flash('Failed to update delivery status', 'danger')
        
        return redirect(url_for('deliveries'))
    
    try:
        df = pd.read_excel('data/nomii_delivery_fake_data.xlsx', sheet_name='Deliveries')
        order = df[df.index == int(order_id[1:])].iloc[0].to_dict()
        order['OrderID'] = order_id
    except Exception as e:
        print(f"Error getting order details: {e}")
        order = None
    
    return render_template('update_status.html', order=order)

@app.route('/earnings')
def earnings():
    delivery_id = session.get('delivery_id', 'D0000')
    earnings = get_user_earnings(delivery_id)
    total_earnings = sum(float(e.get('Amount (₹)', 0)) for e in earnings)
    return render_template('earnings.html', earnings=earnings, total_earnings=total_earnings)

@app.route('/feedback')
def feedback():
    delivery_id = session.get('delivery_id', 'D0000')
    feedback = get_user_feedback(delivery_id)
    return render_template('feedback.html', feedback=feedback)

@app.route('/emergency', methods=['POST'])
def emergency():
    flash('Emergency alert sent to support team! Help is on the way.', 'warning')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
