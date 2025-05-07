from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime
import os

app = Flask(__name__)

# Database configuration - assumes Service Connector has set these variables
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.environ.get('AZURE_POSTGRESQL_USER')}:{os.environ.get('AZURE_POSTGRESQL_PASSWORD')}@{os.environ.get('AZURE_POSTGRESQL_HOST')}/{os.environ.get('AZURE_POSTGRESQL_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Image data model
class ImageData(db.Model):
    __tablename__ = 'image_data'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    red_pixels = db.Column(db.Integer, nullable=False)
    green_pixels = db.Column(db.Integer, nullable=False)
    blue_pixels = db.Column(db.Integer, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'username': self.username,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'red_pixels': self.red_pixels,
            'green_pixels': self.green_pixels,
            'blue_pixels': self.blue_pixels
        }

# API endpoint to receive data from Scala application
@app.route('/api/upload', methods=['POST'])
def upload_data():
    try:
        data = request.json
        
        # Parse timestamp
        timestamp = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
        
        # Create new record
        new_image_data = ImageData(
            filename=data['filename'],
            username=data['username'],
            timestamp=timestamp,
            red_pixels=data['red_pixels'],
            green_pixels=data['green_pixels'],
            blue_pixels=data['blue_pixels']
        )
        
        # Save to database
        db.session.add(new_image_data)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Data received and saved successfully',
            'id': new_image_data.id
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 400

# Web interface to view data
@app.route('/')
def index():
    sort_by = request.args.get('sort_by', 'timestamp')
    order = request.args.get('order', 'desc')
    username_filter = request.args.get('username', '')
    
    query = ImageData.query
    
    # Apply username filter if provided
    if username_filter:
        query = query.filter(ImageData.username.ilike(f'%{username_filter}%'))
    
    # Apply sorting
    if order == 'desc':
        query = query.order_by(desc(getattr(ImageData, sort_by)))
    else:
        query = query.order_by(getattr(ImageData, sort_by))
        
    image_data = query.all()
    
    return render_template(
        'index.html', 
        image_data=image_data, 
        current_sort=sort_by, 
        current_order=order,
        username_filter=username_filter
    )

# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
