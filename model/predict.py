import tensorflow as tf
import numpy as np
import sys
import json

def load_model(model_path):
    print(f"Loading model from {model_path}")
    model = tf.keras.models.load_model(model_path)
    return model

def predict(model, preprocessed_image_path):
    print(f"Loading preprocessed image from {preprocessed_image_path}")
    image_array = np.load(preprocessed_image_path)
    predictions = model.predict(image_array)
    return predictions

def get_ranked_predictions(predictions):
    ranked_predictions = []
    for prediction in predictions:
        sorted_indices = np.argsort(prediction)[::-1]
        ranked_prediction = {rank + 1: {'class_index': int(i), 'probability': float(prediction[i])} for rank, i in enumerate(sorted_indices)}
        ranked_predictions.append(ranked_prediction)
    return ranked_predictions

if __name__ == '__main__':
    model_path = 'model_data/my_best_model.h5'
    preprocessed_image_path = sys.argv[1]
    output_path = sys.argv[2]

    print(f"Model path: {model_path}")
    print(f"Preprocessed image path: {preprocessed_image_path}")
    print(f"Output path: {output_path}")

    model = load_model(model_path)
    predictions = predict(model, preprocessed_image_path)
    
    # 예측 결과의 순위를 계산
    ranked_predictions = get_ranked_predictions(predictions)
    
    # 예측 결과를 JSON 파일로 저장
    with open(output_path, 'w') as f:
        json.dump(ranked_predictions, f)
    
    print(f"Ranked predictions saved to {output_path}")
