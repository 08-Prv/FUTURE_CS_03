from flask import Flask, request, jsonify, send_file, render_template
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import hashlib
import os
from io import BytesIO
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BLOCK_SIZE = 16
KEY_STORE = {}  # stored_name -> {key, hash, original}
NAME_MAP = {}   # original_name -> stored_name (UUID prefixed)


def get_sha256(data):
    return hashlib.sha256(data).hexdigest()


def encrypt_file(data, key):
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(pad(data, BLOCK_SIZE))


def decrypt_file(data, key):
    iv = data[:16]
    ciphertext = data[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), BLOCK_SIZE)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    original_name = file.filename
    data = file.read()
    key = get_random_bytes(32)
    encrypted = encrypt_file(data, key)
    file_hash = get_sha256(data)

    # Save with UUID prefix
    stored_name = f"{uuid.uuid4().hex}_{original_name}"
    path = os.path.join(UPLOAD_FOLDER, stored_name)

    with open(path, 'wb') as f:
        f.write(encrypted)

    # Store key and mapping
    KEY_STORE[stored_name] = {'key': key, 'hash': file_hash, 'original': original_name}
    NAME_MAP[original_name] = stored_name

    return jsonify({"message": "File uploaded successfully.", "filename": original_name}), 200


@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    stored_name = NAME_MAP.get(filename)
    if not stored_name:
        return jsonify({"error": "File not found"}), 404

    path = os.path.join(UPLOAD_FOLDER, stored_name)

    try:
        with open(path, 'rb') as f:
            encrypted = f.read()

        key_data = KEY_STORE.get(stored_name)
        if not key_data:
            return jsonify({"error": "Encryption key missing"}), 403

        decrypted = decrypt_file(encrypted, key_data['key'])
        if get_sha256(decrypted) != key_data['hash']:
            return jsonify({"error": "File integrity compromised"}), 400

        return send_file(BytesIO(decrypted), as_attachment=True, download_name=key_data['original'])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/files', methods=['GET'])
def list_files():
    return jsonify({"files": list(NAME_MAP.keys())}), 200


@app.route('/delete/<filename>', methods=['DELETE'])
def delete(filename):
    stored_name = NAME_MAP.get(filename)
    if not stored_name:
        return jsonify({"error": "File not found"}), 404

    path = os.path.join(UPLOAD_FOLDER, stored_name)
    if os.path.exists(path):
        os.remove(path)

    KEY_STORE.pop(stored_name, None)
    NAME_MAP.pop(filename, None)
    return jsonify({"message": "File deleted"}), 200


@app.route('/modify/<filename>', methods=['PUT'])
def modify(filename):
    stored_name = NAME_MAP.get(filename)
    if not stored_name:
        return jsonify({"error": "Original file not found"}), 404

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    new_file = request.files['file']
    data = new_file.read()
    key = get_random_bytes(32)
    encrypted = encrypt_file(data, key)
    file_hash = get_sha256(data)

    path = os.path.join(UPLOAD_FOLDER, stored_name)
    with open(path, 'wb') as f:
        f.write(encrypted)

    KEY_STORE[stored_name] = {'key': key, 'hash': file_hash, 'original': filename}
    return jsonify({"message": "File modified and re-encrypted"}), 200


if __name__ == '__main__':
    app.run(debug=True)
