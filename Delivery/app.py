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
os.makedirs('data/delivery_data', exist_ok=True)

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_to_excel(data, filename, sheet_name='Sheet1'):
    filepath = f'data/delivery_data/{filename}'
    try:
        if os.path.exists(filepath):
            df = pd.read_excel(filepath)
            df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        else:
            df = pd.DataFrame([data])
        df.to_excel(filepath, index=False)
    except Exception as e:
        print(f"Error saving to {filename}: {e}")

def get_user_deliveries(delivery_id):
    try:
        df = pd.read_excel('data/delivery_data/Delivery_assigned.xlsx')
        return df[df['DeliveryID'] == delivery_id].to_dict('records')
    except:
        return []

def get_user_history(delivery_id):
    try:
        df = pd.read_excel('data/delivery_data/DeliveryHistory.xlsx')
        return df[df['DeliveryID'] == delivery_id].to_dict('records')
    except:
        return []

def get_user_earnings(delivery_id):
    try:
        df = pd.read_excel('data/delivery_data/DeliveryEarnings.xlsx')
        return df[df['DeliveryID'] == delivery_id].to_dict('records')
    except:
        return []

def get_user_feedback(delivery_id):
    try:
        df = pd.read_excel('data/delivery_data/delivery_feedback.xlsx')
        return df[df['DeliveryID'] == delivery_id].to_dict('records')
    except:
        return []

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        phone = request.form['phone']
        aadhaar = request.form['aadhaar']
        address = request.form['address']
        email = request.form['email']
        password = request.form['password']
        vehicle_type = request.form['vehicle_type']
        vehicle_number = request.form['vehicle_number']
        
        # Handle file uploads
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
        
        # Generate Delivery ID
        delivery_id = f"D{str(uuid.uuid4().int)[:8]}"
        
        # Save to Excel
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
        
        save_to_excel(user_data, 'delivery_users.xlsx')
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            df = pd.read_excel('data/delivery_data/delivery_users.xlsx')
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
    if 'delivery_id' not in session:
        return redirect(url_for('login'))
    
    delivery_id = session['delivery_id']
    
    # Get assigned deliveries
    deliveries = get_user_deliveries(delivery_id)
    
    # Calculate stats
    total_deliveries = len(deliveries)
    completed_deliveries = len([d for d in deliveries if d.get('Status') == 'Delivered'])
    pending_deliveries = total_deliveries - completed_deliveries
    
    # Get recent history (last 5)
    history = get_user_history(delivery_id)[-5:]
    
    # Get earnings
    earnings = get_user_earnings(delivery_id)
    total_earnings = sum(e.get('Earnings', 0) for e in earnings)
    
    # Get feedback
    feedback = get_user_feedback(delivery_id)
    
    return render_template('dashboard.html', 
                         deliveries=deliveries,
                         total_deliveries=total_deliveries,
                         completed_deliveries=completed_deliveries,
                         pending_deliveries=pending_deliveries,
                         history=history,
                         earnings=earnings,
                         total_earnings=total_earnings,
                         feedback=feedback)

@app.route('/deliveries')
def deliveries():
    if 'delivery_id' not in session:
        return redirect(url_for('login'))
    
    delivery_id = session['delivery_id']
    deliveries = get_user_deliveries(delivery_id)
    
    return render_template('deliveries.html', deliveries=deliveries)

@app.route('/update_status/<order_id>', methods=['GET', 'POST'])
def update_status(order_id):
    if 'delivery_id' not in session:
        return redirect(url_for('login'))
    
    delivery_id = session['delivery_id']
    
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
        
        # Update Delivery_assigned.xlsx
        try:
            df = pd.read_excel('data/delivery_data/Delivery_assigned.xlsx')
            df.loc[df['OrderID'] == order_id, 'Status'] = status
            df.to_excel('data/delivery_data/Delivery_assigned.xlsx', index=False)
        except Exception as e:
            print(f"Error updating status: {e}")
        
        # Add to DeliveryHistory if delivered
        if status == 'Delivered':
            history_data = {
                "OrderID": order_id,
                "DeliveryID": delivery_id,
                "DeliveredDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Proof": proof,
                "Remarks": remarks
            }
            save_to_excel(history_data, 'DeliveryHistory.xlsx')
        
        # Add to Update_delivery_status.xlsx
        update_data = {
            "OrderID": order_id,
            "DeliveryID": delivery_id,
            "StatusUpdate": status,
            "UpdateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Remarks": remarks
        }
        save_to_excel(update_data, 'Update_delivery_status.xlsx')
        
        flash('Delivery status updated successfully!', 'success')
        return redirect(url_for('deliveries'))
    
    # Get order details
    try:
        df = pd.read_excel('data/delivery_data/Delivery_assigned.xlsx')
        order = df[df['OrderID'] == order_id].iloc[0].to_dict()
    except:
        order = None
    
    return render_template('update_status.html', order=order)

@app.route('/earnings')
def earnings():
    if 'delivery_id' not in session:
        return redirect(url_for('login'))
    
    delivery_id = session['delivery_id']
    earnings = get_user_earnings(delivery_id)
    total_earnings = sum(e.get('Earnings', 0) for e in earnings)
    
    return render_template('earnings.html', earnings=earnings, total_earnings=total_earnings)

@app.route('/feedback')
def feedback():
    if 'delivery_id' not in session:
        return redirect(url_for('login'))
    
    delivery_id = session['delivery_id']
    feedback = get_user_feedback(delivery_id)
    
    return render_template('feedback.html', feedback=feedback)

@app.route('/emergency', methods=['POST'])
def emergency():
    if 'delivery_id' not in session:
        return redirect(url_for('login'))
    
    # In a real app, this would trigger notifications to admin
    flash('Emergency alert sent to support team! Help is on the way.', 'warning')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)