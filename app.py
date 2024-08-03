from flask import Flask, request, render_template
import os
from uuid import uuid4
import paramiko
from waitress import serve

app = Flask(__name__)

# SFTP server configuration
SFTP_HOST = 'teams.buildtheearth.net'
SFTP_PORT = 2022  # Custom port for SFTP
SFTP_USER = ''
SFTP_PASS = ''
SFTP_UPLOAD_DIR = '/plugins/Essentials/warps'  # Specify the directory on the SFTP server

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    print(request.form)  # Print the form data for debugging

    if 'coordinates' not in request.form:
        return "Error: 'coordinates' field is missing!", 400

    # Retrieve form data
    name = request.form['name']
    coordinates = request.form['coordinates']

    # Parse the coordinates
    try:
        x, y, z = map(float, coordinates.split(','))
    except ValueError:
        return "Error: Please enter valid coordinates in the format x, y, z."

    # Default values
    world_id = str(uuid4())
    world_name = "world"
    yaw = 0
    pitch = 0
    lastowner = str(uuid4())

    # Sanitize the name to make it a safe file name
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_')).rstrip()

    # Define the file name using the sanitized name
    file_name = f"{safe_name.replace(' ', '_')}.yml"
    file_path = os.path.join('submissions', file_name)

    # Write the data to a new text file
    with open(file_path, 'w') as f:
        f.write(f"world: {world_id}\n")
        f.write(f"world-name: {world_name}\n")
        f.write(f"x: {x}\n")
        f.write(f"y: {y}\n")
        f.write(f"z: {z}\n")
        f.write(f"yaw: {yaw}\n")
        f.write(f"pitch: {pitch}\n")
        f.write(f"name: {safe_name.replace(' ', '_')}\n")
        f.write(f"lastowner: {lastowner}\n")

    # Upload the file to the SFTP server
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASS)

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.chdir(SFTP_UPLOAD_DIR)  # Change to the target directory on the SFTP server

        sftp.put(file_path, os.path.join(SFTP_UPLOAD_DIR, file_name))
        sftp.close()
        transport.close()

        print(f"File {file_name} uploaded successfully to {SFTP_UPLOAD_DIR} on {SFTP_HOST}.")
    except Exception as e:
        return f"Failed to upload the file to SFTP: {e}"

    return f"Data submitted successfully, saved as {file_name}, and uploaded to SFTP!"

if __name__ == '__main__':
    if not os.path.exists('submissions'):
        os.makedirs('submissions')
    
    # Use Waitress to serve the app
    serve(app, host='0.0.0.0', port=8080)
