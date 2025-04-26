import os
import pandas as pd
from flask import Flask, request, jsonify, render_template
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')

# Initialize data variables
df = None
requester_category_counts = None

def load_data():
    global df, requester_category_counts
    try:
        excel_file = "Jan2023 to May2024 Data for Analysis 1.xlsx"
        logger.info(f"Attempting to load Excel file: {excel_file}")
        
        if not os.path.exists(excel_file):
            raise FileNotFoundError(f"Excel file '{excel_file}' not found")
            
        df = pd.read_excel(excel_file, sheet_name='Tabular Reports')
        logger.info(f"Successfully loaded Excel file. Shape: {df.shape}")
        
        # Check if required columns exist
        required_columns = ['Requester', 'Category']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
            
        requester_category_counts = df.groupby(['Requester', 'Category']).size().unstack(fill_value=0)
        logger.info("Successfully processed data")
        
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise

# Load data when the application starts
try:
    load_data()
except Exception as e:
    logger.error(f"Failed to initialize application: {str(e)}")
    raise

def predict_fail_category(requester_name, data):
    if requester_name not in data.index:
        logger.info(f"Requester '{requester_name}' not found in data")
        return {
            'Requester': requester_name,
            'Complaint Counts': None,
            'Most Likely to Fail First': None,
            'Number of Complaints': 0
        }

    requester_data = data.loc[requester_name]
    sorted_categories = requester_data.sort_values(ascending=False)
    most_failed_category = sorted_categories.idxmax()
    max_complaints = sorted_categories.max()

    logger.info(f"Prediction for {requester_name}: Most failed category is {most_failed_category} with {max_complaints} complaints")
    return {
        'Requester': requester_name,
        'Complaint Counts': sorted_categories.to_dict(),
        'Most Likely to Fail First': most_failed_category,
        'Number of Complaints': max_complaints
    }

@app.route('/')
def index():
    return render_template('search_form.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.route('/predict', methods=['GET'])
def predict():
    requester_name = request.args.get('requester')
    if not requester_name:
        return jsonify({'error': 'Please provide a requester name.'})

    try:
        prediction = predict_fail_category(requester_name, requester_category_counts)
        current_date = datetime.now().strftime("%B %d, %Y")
        return render_template('prediction_result.html', 
                             prediction=prediction,
                             current_date=current_date)
    except Exception as e:
        logger.error(f"Error making prediction: {str(e)}")
        return render_template('404.html', error=str(e)), 500

@app.route('/favicon.ico')
def favicon():
    return "", 204  # Prevents favicon 404 errors

if __name__ == '__main__':
    app.run(debug=True)
