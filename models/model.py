import os
import json
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ModelCheckpoint
import matplotlib.pyplot as plt

# Directory to save the model
save_dir = 'models/trained_model'
os.makedirs(save_dir, exist_ok=True)

# Load pre-trained MobileNetV2 model
base_model = tf.keras.applications.MobileNetV2(
    weights='imagenet',
    include_top=False,
    input_shape=(224, 224, 3)
)

# Freeze base model layers
base_model.trainable = False

# Add new layers
model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(512, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(101, activation='softmax')
])

# Compile the model
model.compile(
    optimizer=optimizers.Adam(learning_rate=0.001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# Load the new dataset from real_food101_dataset
train_datagen = ImageDataGenerator(rescale=1./255, validation_split=0.2)

train_generator = train_datagen.flow_from_directory(
    'C:/Users/skyra/FoodAnalyzer/datasets/real_food101_dataset/food-101/images',
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical',
    subset='training'
)

validation_generator = train_datagen.flow_from_directory(
    'C:/Users/skyra/FoodAnalyzer/datasets/real_food101_dataset/food-101/images',
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical',
    subset='validation'
)

# Create a model checkpoint callback to save the best model 
checkpoint_path = os.path.join(save_dir, 'best_model.keras')
checkpoint_callback = ModelCheckpoint(
    filepath=checkpoint_path,
    save_weights_only=False, 
    monitor='val_accuracy',  # Monitor validation accuracy
    mode='max',               
    save_best_only=True,      
    verbose=1
)

# Train the model with the checkpoint callback
history = model.fit(
    train_generator,
    epochs=30,
    validation_data=validation_generator,
    callbacks=[checkpoint_callback]
)

# Save training history to a JSON file
with open(os.path.join(save_dir, 'initial_model_history.json'), 'w') as f:
    json.dump(history.history, f)

# Unfreeze some layers of the base model for fine-tuning
base_model.trainable = True
fine_tune_at = 100
for layer in base_model.layers[:fine_tune_at]:
    layer.trainable = False

# Recompile the model for fine-tuning
model.compile(
    optimizer=optimizers.Adam(learning_rate=0.0001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# Fine-tune the model with the checkpoint callback
history_fine_tune = model.fit(
    train_generator,
    epochs=30,
    validation_data=validation_generator,
    callbacks=[checkpoint_callback]
)

# Save fine-tuned training history
with open(os.path.join(save_dir, 'fine_tuned_model_history.json'), 'w') as f:
    json.dump(history_fine_tune.history, f)

# Load and inspect the best model saved by the checkpoint
loaded_model = tf.keras.models.load_model(checkpoint_path)
print('Best model loaded successfully.')