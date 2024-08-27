from flask import Blueprint, render_template, request, jsonify, send_from_directory
import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.utils import secure_filename

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

