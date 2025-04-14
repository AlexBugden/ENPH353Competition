import string
import random
from random import randint
import cv2
import numpy as np
import os
from PIL import Image, ImageFont, ImageDraw
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from matplotlib import pyplot as plt

def convert_to_one_hot(SS):
    SS = np.eye(36)[SS.reshape(-1)]
    return SS

YY =  np.array([0])
convert_to_one_hot(YY)

A = [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
B = [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
C = [0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
D = [0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
E = [0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
F = [0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
G = [0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
H = [0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
I = [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
J = [0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
K = [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
L = [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
M = [0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
N = [0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
O = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
P = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0]
R = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0]
S = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0]
T = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0]
U = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0]
V = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0]
W = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0]
X = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0]
Y = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0]
Z = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0]
num2= [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0]
num5= [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0]
num8= [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0]
num9= [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1]

def check_character(char):
    if char == 'A': return A
    elif char == 'B': return B
    elif char == 'C': return C
    elif char == 'D': return D
    elif char == 'E': return E
    elif char == 'F': return F
    elif char == 'G': return G
    elif char == 'H': return H
    elif char == 'I': return I
    elif char == 'J': return J
    elif char == 'K': return K
    elif char == 'L': return L
    elif char == 'M': return M
    elif char == 'N': return N
    elif char == 'O': return O
    elif char == 'P': return P
    elif char == 'R': return R
    elif char == 'S': return S
    elif char == 'T': return T
    elif char == 'U': return U
    elif char == 'V': return V
    elif char == 'W': return W
    elif char == 'X': return X
    elif char == 'Y': return Y
    elif char == 'Z': return Z
    elif char == '2': return num2
    elif char == '5': return num5
    elif char == '8': return num8
    elif char == '9': return num9
    else: return None  # Handle unexpected characters

# Path to the directory containing images
image_dir = '/home/fizzer/letters'
image_files = [f for f in os.listdir(image_dir)]
image_files.sort()

# Data augmentation settings
datagen = ImageDataGenerator(
    rotation_range=15,
    zoom_range=[0.8, 1.2],
    brightness_range=[0.4, 1.0],
    shear_range=10
)

augset = []  # List to store all loaded images (original + augmented)

# Generate augmented images
for j in range(len(image_files)):
    image_path = os.path.join(image_dir, image_files[j])
    image = Image.open(image_path)
    image_array = np.expand_dims(image, 0)  # Add batch dimension

    # Generate augmented images (e.g., 150 per original image)
    aug_iter = datagen.flow(image_array, batch_size=1)
    for _ in range(130):  # Generate 150 augmented versions
        augmented_image = next(aug_iter)[0].astype('uint8')
        augset.append([augmented_image, check_character(image_files[j][3])])

print(f"Total images in augset: {len(augset)}")
np.random.shuffle(augset)

# Generate X and Y datasets
X_dataset_orig = np.array([cv2.resize(data[0], (256, 183)) for data in augset[:]])
Y_dataset = np.array([data[1] for data in augset])

# Normalize X (images) dataset
X_dataset = X_dataset_orig / 255.0
plt.imshow(X_dataset_orig[0])
Y_dataset[0]

from tensorflow.keras import layers
from tensorflow.keras import models
from tensorflow.keras import optimizers
from tensorflow.keras.utils import plot_model
from tensorflow.keras import backend
import math

VALIDATION_SPLIT = 0.2
split_index = math.ceil(X_dataset.shape[0] * (1 - VALIDATION_SPLIT))

X_train_dataset = X_dataset[:split_index]
Y_train_dataset = Y_dataset[:split_index]
X_val_dataset = X_dataset[split_index:]
Y_val_dataset = Y_dataset[split_index:]

print("X shape: " + str(X_dataset.shape))
print("Y shape: " + str(Y_dataset.shape))
print(f"Total examples: {X_dataset.shape[0]}\nTraining examples: {X_train_dataset.shape[0]}\nValidation examples: {X_val_dataset.shape[0]}")

def reset_weights(model):
    for ix, layer in enumerate(model.layers):
        if (hasattr(model.layers[ix], 'kernel_initializer') and
            hasattr(model.layers[ix], 'bias_initializer')):
            weight_initializer = model.layers[ix].kernel_initializer
            bias_initializer = model.layers[ix].bias_initializer
            old_weights, old_biases = model.layers[ix].get_weights()
            model.layers[ix].set_weights([
                weight_initializer(shape=old_weights.shape),
                bias_initializer(shape=len(old_biases))])

from tensorflow.keras import regularizers

# Define the convolutional model
conv_model = models.Sequential()

# Add layers to the model
conv_model.add(layers.Conv2D(32, (3, 3), activation='relu',
                             input_shape=(183, 256,  3)))
conv_model.add(layers.MaxPooling2D((2, 2)))
conv_model.add(layers.Conv2D(64, (3, 3), activation='relu'))
conv_model.add(layers.MaxPooling2D((2, 2)))
conv_model.add(layers.Conv2D(128, (3, 3), activation='relu'))
conv_model.add(layers.MaxPooling2D((2, 2)))
conv_model.add(layers.Conv2D(256, (3, 3), activation='relu'))
conv_model.add(layers.MaxPooling2D((2, 2)))
conv_model.add(layers.Flatten())
conv_model.add(layers.Dropout(0.5))
conv_model.add(layers.Dense(200, activation='relu',
               kernel_regularizer=regularizers.l2(0.001)))
conv_model.add(layers.Dense(29, activation='softmax'))

# Set the learning rate
LEARNING_RATE = 1e-4

# Compile the model
conv_model.compile(loss='categorical_crossentropy',
                   optimizer=optimizers.RMSprop(learning_rate=LEARNING_RATE),
                   metrics=['accuracy'])

from tensorflow.keras.callbacks import EarlyStopping

early_stopping = EarlyStopping(
    monitor='val_loss',
    patience=5,
    restore_best_weights=True
)

reset_weights(conv_model)

# Train the model
history_conv = conv_model.fit(
    X_train_dataset, Y_train_dataset,
    validation_data=(X_val_dataset, Y_val_dataset),
    epochs=40,
    batch_size=16,
    callbacks=[early_stopping]
)

conv_model.save('character_rec.keras')
