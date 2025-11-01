from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import threading
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# File to store appointments
APPOINTMENTS_FILE = 'appointments.json'

def load_appointments():
    """Load appointments from JSON file"""
    if not os.path.exists(APPOINTMENTS_FILE):
        return []
    
    try:
        with open(APPOINTMENTS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_appointments(appointments):
    """Save appointments to JSON file"""
    with open(APPOINTMENTS_FILE, 'w') as f:
        json.dump(appointments, f, indent=2)

def send_reminder_email(appointment):
    """Send reminder email for appointment (simulated for demo)"""
    try:
        # In a real implementation, you would use actual SMTP credentials
        # For demo purposes, we'll just print to console and simulate success
        
        print(f"🔔 SENDING REMINDER EMAIL:")
        print(f"   To: {appointment['contact']}")
        print(f"   Subject: Appointment Reminder - Dental Center Texas")
        print(f"   Message: Your dental appointment is scheduled for {appointment['date']} at {appointment['time']}")
        print(f"   Reminder sent successfully! 📧")
        
        return True
    except Exception as e:
        print(f"Error sending reminder: {e}")
        return False

def schedule_reminders():
    """Background thread to check for appointments needing reminders"""
    while True:
        try:
            appointments = load_appointments()
            current_time = datetime.now()
            
            for appointment in appointments:
                appointment_date = datetime.strptime(appointment['date'], '%Y-%m-%d')
                
                # Check if appointment is exactly 1 day away
                reminder_time = appointment_date - timedelta(days=1)
                
                if (not appointment.get('reminder_sent') and 
                    current_time.date() == reminder_time.date() and
                    current_time.hour == 9):  # Send at 9 AM
                    
                    print(f"Scheduling reminder for {appointment['name']}...")
                    if send_reminder_email(appointment):
                        appointment['reminder_sent'] = True
                        save_appointments(appointments)
            
        except Exception as e:
            print(f"Error in reminder scheduler: {e}")
        
        # Check every hour
        time.sleep(3600)

@app.route('/check', methods=['POST'])
def check_availability():
    """Check if a time slot is available"""
    try:
        data = request.get_json()
        date = data.get('date')
        time = data.get('time')
        
        if not date or not time:
            return jsonify({'error': 'Date and time are required'}), 400
        
        appointments = load_appointments()
        
        # Check if slot is already booked
        for appointment in appointments:
            if appointment['date'] == date and appointment['time'] == time:
                return jsonify({'available': False})
        
        return jsonify({'available': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/book', methods=['POST'])
def book_appointment():
    """Book a new appointment"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('contact'):
            return jsonify({'error': 'Contact information is required'}), 400
        if not data.get('date') or not data.get('time'):
            return jsonify({'error': 'Date and time are required'}), 400
        
        # Generate appointment ID
        appointments = load_appointments()
        appointment_id = len(appointments) + 1
        
        # Create appointment object
        appointment = {
            'id': appointment_id,
            'name': data.get('name', ''),
            'contact': data['contact'],
            'date': data['date'],
            'time': data['time'],
            'status': 'confirmed',
            'created_at': datetime.now().isoformat(),
            'reminder_sent': False
        }
        
        # Double-check availability
        for existing_appointment in appointments:
            if (existing_appointment['date'] == appointment['date'] and 
                existing_appointment['time'] == appointment['time']):
                return jsonify({'error': 'Time slot no longer available'}), 409
        
        # Save appointment
        appointments.append(appointment)
        save_appointments(appointments)
        
        print(f"✅ New appointment booked: {appointment}")
        
        # Schedule demo reminder (after 10 seconds)
        def send_demo_reminder():
            time.sleep(10)
            send_reminder_email(appointment)
        
        reminder_thread = threading.Thread(target=send_demo_reminder)
        reminder_thread.daemon = True
        reminder_thread.start()
        
        return jsonify({
            'success': True,
            'appointment_id': appointment_id,
            'message': 'Appointment booked successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cancel', methods=['POST'])
def cancel_appointment():
    """Cancel an appointment by contact information"""
    try:
        data = request.get_json()
        contact = data.get('contact')
        
        if not contact:
            return jsonify({'error': 'Contact information is required'}), 400
        
        appointments = load_appointments()
        
        # Find and remove appointment
        for i, appointment in enumerate(appointments):
            if appointment['contact'] == contact:
                cancelled_appointment = appointments.pop(i)
                save_appointments(appointments)
                
                print(f"❌ Appointment cancelled: {cancelled_appointment}")
                
                return jsonify({
                    'success': True,
                    'message': 'Appointment cancelled successfully'
                })
        
        return jsonify({'success': False, 'message': 'No appointment found'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/appointments', methods=['GET'])
def get_appointments():
    """Get all appointments (for admin purposes)"""
    try:
        appointments = load_appointments()
        return jsonify({'appointments': appointments})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Ensure appointments file exists
    if not os.path.exists(APPOINTMENTS_FILE):
        save_appointments([])
    
    # Start reminder scheduler in background thread
    reminder_thread = threading.Thread(target=schedule_reminders)
    reminder_thread.daemon = True
    reminder_thread.start()
    
    print("🚀 SmartBooker Backend Server Starting...")
    print("📅 Appointment Booking System Ready!")
    print("🔔 Reminder System Activated!")
    print("🌐 Server running on http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)