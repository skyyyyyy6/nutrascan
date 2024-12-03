import os
import base64
import logging
import time  
import requests
import numpy as np 
import tensorflow as tf
from flask import Flask, request, jsonify
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

# Initialize Flask app
app = Flask(__name__)

# L1ogging
logging.basicConfig(level=logging.INFO)

# FoodData Central API key
FD_CENTRAL_API_KEY = 'UJCW1Eb4sXlEaZhc5XbZ7S4iF71dCUIO1eHd62gS'

# Load the pre-trained CNN model
model = tf.keras.models.load_model('models/trained_model/fine_tuned_model.keras')

# Load the Food-101 class labels
with open('C:/Users/skyra/FoodAnalyzer/datasets/real_food101_dataset/food-101/meta/classes.txt') as f:
    food101_labels = [line.strip() for line in f.readlines()]

# Path for the images folder
IMAGES_FOLDER = os.path.join(os.path.dirname(__file__), 'images')
if not os.path.exists(IMAGES_FOLDER):
    os.makedirs(IMAGES_FOLDER)

def process_image(food_name):
    """Query FoodData Central API for nutritional information based on food name."""
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={food_name}&api_key={FD_CENTRAL_API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        search_results = response.json()

        if 'foods' not in search_results or not search_results['foods']:
            logging.warning("No food items found for the given name.")
            return {"error": "No food items found"}

        fdc_id = search_results['foods'][0]['fdcId']
        nutrition_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={FD_CENTRAL_API_KEY}"
        
        nutrition_response = requests.get(nutrition_url)
        nutrition_response.raise_for_status()
        return nutrition_response.json()

    except requests.exceptions.HTTPError as err:
        logging.error(f"Error fetching nutrition info: {err}")
        return {"error": "Unable to fetch nutrition information"}

def predict_food(image_path):
    """Run the captured image through the CNN model to get food prediction."""
    start_time = time.time()

    try:
        img = image.load_img(image_path, target_size=(224, 224))
        logging.info("Image loaded successfully.")
    except Exception as e:
        logging.error("Error loading image: %s", str(e))
        raise

    x = image.img_to_array(img)
    x = preprocess_input(x)
    x = np.expand_dims(x, axis=0)

    preds = model.predict(x)

    class_index = np.argmax(preds, axis=1)[0]
    food_item = food101_labels[class_index]

    logging.info("Predicted food item: %s", food_item)
    logging.info("Total processing time: %s seconds", time.time() - start_time)

    return food_item

@app.route('/api/capture', methods=['POST'])
def capture_endpoint():
    logging.info("Received image capture request.")
    
    data = request.json
    image_base64 = data.get('image')

    if not image_base64:
        logging.warning("No image data received")
        return jsonify({"error": "Image data is required"}), 400

    if ',' in image_base64:
        image_base64 = image_base64.split(',')[1]

    os.makedirs(IMAGES_FOLDER, exist_ok=True)

    image_path = os.path.join(IMAGES_FOLDER, 'received_image.jpg')
    logging.info("Saving image to path: %s", image_path)

    try:
        with open(image_path, "wb") as img_file:
            img_file.write(base64.b64decode(image_base64))
        logging.info("Image saved successfully: %s", image_path)
    except Exception as e:
        logging.error("Error saving image: %s", str(e))
        return jsonify({"error": "Failed to save image"}), 500

    try:
        food_name = predict_food(image_path)
    except Exception as e:
        logging.error("Error predicting food: %s", str(e))
        return jsonify({"error": "Food prediction failed"}), 500

    result = process_image(food_name)

    if "error" in result:
        return jsonify(result), 500  

    return jsonify({"food_name": food_name, "nutrition_info": result})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
