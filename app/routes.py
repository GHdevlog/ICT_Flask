from flask import Blueprint, render_template, request, jsonify, send_from_directory
import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.utils import secure_filename
import subprocess

# Firebase Admin 초기화
cred = credentials.Certificate('ict-flutter-app-firebase-adminsdk-4utx6-db54eaf7e4.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/upload_images', methods=['POST'])
def upload_images():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files part'})
    
    files = request.files.getlist('files[]')
    if len(files) == 0:
        return jsonify({'error': 'No selected files'})

    user_id = request.form.get('user_id')
    pet_id = request.form.get('pet_id')
    
    if not user_id or not pet_id:
        return jsonify({'error': 'User ID and Pet ID are required'})

    upload_folder = f'user_imgs/{user_id}/{pet_id}'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    file_urls = []
    for file in files:
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            # 변경된 URL 형식에 맞게 경로 설정
            file_url = f'/images/{user_id}/{pet_id}/{filename}'
            file_urls.append(file_url)

    # Firestore에 사진 URL 저장
    pet_ref = db.collection('users').document(user_id).collection('pets').document(pet_id)

    # 문서가 존재하는지 확인하고 없으면 생성
    if not pet_ref.get().exists:
        pet_ref.set({'photos': file_urls})
    else:
        pet_ref.update({'photos': firestore.ArrayUnion(file_urls)})

    return jsonify({'message': f'{len(file_urls)} files successfully uploaded', 'file_urls': file_urls})

@main.route('/uploads/<path:filename>', methods=['GET'])
def get_file(filename):
    return send_from_directory(os.path.dirname(filename), os.path.basename(filename))

@main.route('/upload_videos', methods=['POST'])
def upload_videos():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files part'})
    
    files = request.files.getlist('files[]')
    if len(files) == 0:
        return jsonify({'error': 'No selected files'})

    user_id = request.form.get('user_id')
    pet_id = request.form.get('pet_id')
    
    if not user_id or not pet_id:
        return jsonify({'error': 'User ID and Pet ID are required'})

    upload_folder = f'user_videos/{user_id}/{pet_id}'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    file_urls = []
    for file in files:
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            # 변경된 URL 형식에 맞게 경로 설정
            file_url = f'/videos/{user_id}/{pet_id}/{filename}'
            file_urls.append(file_url)

    # Firestore에 비디오 URL 저장
    pet_ref = db.collection('users').document(user_id).collection('pets').document(pet_id)

    # 문서가 존재하는지 확인하고 없으면 생성
    if not pet_ref.get().exists:
        pet_ref.set({'videos': file_urls})
    else:
        pet_ref.update({'videos': firestore.ArrayUnion(file_urls)})

    return jsonify({'message': f'{len(file_urls)} files successfully uploaded', 'file_urls': file_urls})


# 이미지 제공
@main.route('/images/<user_id>/<pet_id>/<filename>')
def serve_image(user_id, pet_id, filename):
    
    # 절대 경로로 변환
    directory = os.path.join(os.getcwd(), 'user_imgs', user_id, pet_id)
    file_path = os.path.join(directory, filename)

    # 파일 경로를 출력
    print(f"Serving image from absolute path: {file_path}")

    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        return jsonify({'error': 'File not found'}), 404

    return send_from_directory(directory, filename)

# 동영상 제공
@main.route('/videos/<user_id>/<pet_id>/<filename>')
def serve_video(user_id, pet_id, filename):
    
    # 동영상 파일이 저장된 절대 경로로 변환
    directory = os.path.join(os.getcwd(), 'user_videos', user_id, pet_id)
    file_path = os.path.join(directory, filename)

    # 파일 경로를 출력
    print(f"Serving video from absolute path: {file_path}")

    if not os.path.exists(file_path):
        print(f"Video file does not exist: {file_path}")
        return jsonify({'error': 'Video file not found'}), 404

    # 동영상 파일 서빙
    return send_from_directory(directory, filename)


# 파일 조회 및 이미지 제공을 하나의 API로 통합
@main.route('/get_media', methods=['GET'])
def get_media():
    user_id = request.args.get('user_id')
    pet_id = request.args.get('pet_id')

    if not user_id or not pet_id:
        return jsonify({'error': 'User ID and Pet ID are required'}), 400

    # Firestore에서 해당 유저와 펫의 미디어 데이터를 조회
    pet_ref = db.collection('users').document(user_id).collection('pets').document(pet_id)
    pet_doc = pet_ref.get()

    if pet_doc.exists:
        # 사진과 비디오 데이터를 가져옴
        photos = pet_doc.to_dict().get('photos', [])
        videos = pet_doc.to_dict().get('videos', [])
        
        # 각 사진 및 비디오 URL에 실제 이미지 및 비디오 경로로 접근할 수 있는 URL을 추가
        server_url = request.host_url  # 서버의 기본 URL (예: http://192.168.100.113:5000/)
        photo_urls = [f"{server_url}images/{user_id}/{pet_id}/{os.path.basename(photo)}" for photo in photos]
        video_urls = [f"{server_url}videos/{user_id}/{pet_id}/{os.path.basename(video)}" for video in videos]

        return jsonify({'photos': photo_urls, 'videos': video_urls})
    else:
        return jsonify({'error': 'No media found for this pet'}), 404

# 모델을 통한 반려동물 예측
@main.route('/predict', methods=['POST'])
def predict():
    # 클라이언트 요청에서 'file' 키가 없는지 확인하고 에러 반환
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})  # 에러 메시지 반환: 파일이 존재하지 않음
    
    # 클라이언트가 업로드한 파일을 변수에 저장
    file = request.files['file']
    
    # 파일 이름이 없는 경우 (파일이 선택되지 않음) 에러 반환
    if file.filename == '':
        return jsonify({'error': 'No selected file'})  # 에러 메시지 반환: 선택된 파일이 없음

    # 업로드된 파일을 저장할 경로를 설정하고, 해당 경로에 파일을 저장
    file_path = os.path.join('uploads', file.filename)
    file.save(file_path)  # 업로드된 파일을 서버에 저장

    # 이미지 전처리 수행을 위한 명령어 준비 (conda 환경을 이용하여 전처리 실행)
    preprocess_command = ['conda', 'run', '-n', 'ict_preprocess', 'python', 'preprocessing/preprocess.py', file_path]
    # 전처리 명령어 실행 (서브 프로세스로 실행하고 출력 결과를 캡처)
    preprocess_result = subprocess.run(preprocess_command, capture_output=True, text=True)
    
    # 전처리 실행 결과가 실패한 경우 에러 반환
    if preprocess_result.returncode != 0:
        return jsonify({'error': 'Image preprocessing failed'})  # 전처리 실패 시 에러 메시지 반환

    # 전처리된 이미지를 모델로 예측하는 명령어 준비 (conda 환경에서 예측 스크립트 실행)
    output_path = os.path.join('outputs', 'predictions.json')  # 예측 결과가 저장될 파일 경로
    predict_command = ['conda', 'run', '-n', 'ict', 'python', 'model/predict.py', 'preprocessed_image.npy', output_path]
    # 예측 명령어 실행 (서브 프로세스로 실행하고 출력 결과를 캡처)
    result = subprocess.run(predict_command, capture_output=True, text=True)
    
    # 예측 실행 결과가 실패한 경우 에러 반환
    if result.returncode != 0:
        return jsonify({'error': 'Model prediction failed'})  # 예측 실패 시 에러 메시지 반환

    # 예측 결과 파일이 존재하는지 확인하고, 존재하지 않으면 에러 반환
    if not os.path.exists(output_path):
        return jsonify({'error': 'Prediction file not found'})  # 예측 결과 파일을 찾지 못한 경우 에러 메시지 반환

    # 예측 결과 파일을 읽고 JSON 형식으로 반환
    try:
        with open(output_path, 'r') as f:
            predictions = json.load(f)  # 예측 결과 파일을 읽고 JSON 파싱
    except Exception as e:
        # 파일을 읽는 과정에서 예외 발생 시 에러 메시지와 상세 내용 반환
        return jsonify({'error': 'Failed to read prediction results', 'details': str(e)})

    # 예측 결과를 클라이언트에 JSON 형식으로 반환
    return jsonify({'predictions': predictions})
