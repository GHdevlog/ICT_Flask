import sys
from PIL import Image
import numpy as np

def preprocess_image(image_path):
    image = Image.open(image_path)
    image = image.resize((224, 224))
    image_array = np.array(image) / 255.0
    image_array = image_array.reshape((1, 224, 224, 3))
    return image_array

if __name__ == '__main__':
    image_path = sys.argv[1]
    preprocessed_image = preprocess_image(image_path)
    np.save('preprocessed_image.npy', preprocessed_image)
