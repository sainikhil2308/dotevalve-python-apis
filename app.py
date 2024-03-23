from flask import Flask, request, jsonify, send_file
import argparse
import sys
from pathlib import Path

from src.entry import entry_point
from src.logger import logger

import os
import shutil
import json
import requests
from urllib.parse import urlparse
import cv2
import numpy as np
from ModifiedSauvola_Binarization  import SauvolaModBinarization

# from skimage.filters import threshold_sauvola

app = Flask(__name__)

def create_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)



def save_file_from_url(url, file_path):
    try:
        response = requests.get(url)
        # response = url
        image = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)  # Load image from response content

        # Apply Sauvola Binarization image enhancement
        enhanced_image = SauvolaModBinarization(image)

        file_name = os.path.basename(urlparse(url).path)
        file_path = os.path.join(file_path, file_name)

        # Save the enhanced binarized image
        cv2.imwrite(file_path, enhanced_image)

        print(f"File saved successfully at '{file_path}'.")
    except Exception as e:
        print(f"Error saving file: {str(e)}")

def parse_args_from_payload(payload):
    argparser = argparse.ArgumentParser()

    argparser.add_argument(
        "-i",
        "--inputDir",
        default=payload.get("input_paths", ["inputs"]),
        nargs="*",
        required=False,
        type=str,
        dest="input_paths",
        help="Specify an input directory.",
    )

    argparser.add_argument(
        "-d",
        "--debug",
        required=False,
        dest="debug",
        action="store_false",
        help="Enables debugging mode for showing detailed errors",
    )

    argparser.add_argument(
        "-o",
        "--outputDir",
        default=payload.get("output_dir", "outputs"),
        required=False,
        dest="output_dir",
        help="Specify an output directory.",
    )

    argparser.add_argument(
        "-a",
        "--autoAlign",
        required=False,
        dest="autoAlign",
        action="store_true",
        help="(experimental) Enables automatic template alignment - \
        use if the scans show slight misalignments.",
    )

    argparser.add_argument(
        "-l",
        "--setLayout",
        required=False,
        dest="setLayout",
        action="store_true",
        help="Set up OMR template layout - modify your json file and \
        run again until the template is set.",
    )

    args = vars(argparser.parse_args([]))  # Replace '[]' with actual arguments

    return args


@app.route('/', methods=['GET'])
def index():
    return "If You can see This message You are in Matrix. Escape it. They are using You"

@app.route('/outputs/<path:filename>')
def serve_output_file(filename):
    from flask import send_from_directory
    return send_from_directory('outputs/CheckedOMRs', filename)

@app.route('/omrchecker', methods=['POST'])
def omr_checker():
    payload = request.get_json()

    args = parse_args_from_payload(payload)

    url = payload['url']
    folder_name = payload['folder_name']
    template = payload['template']
    fileName = payload['fileName']


    # Specify the path of the parent folder

    # Check if the folder exists
    current_directory = os.getcwd()
    inputs_folder = os.path.join(current_directory, "inputs")
    outputs_folder = os.path.join(current_directory, "outputs")
    folder_path = os.path.join(inputs_folder, folder_name+"/")
    
    if os.path.exists(folder_path):
        # If the folder exists, delete it and its contents recursively
        shutil.rmtree(folder_path)
        print(f"Folder '{os.path.abspath(folder_path)}' deleted.")

    # Create the folder
    os.makedirs(folder_path)

    # Save the file from the URL into the created folder
    save_file_from_url(url, folder_path)

    # Print a message indicating that the folder has been created
    print(f"Folder '{folder_path}' created.")

    # Write the JSON object to the file
    with open(os.path.join(folder_path, "template.json"), 'w') as file:
        json.dump(template, file)

    file_name = 'template.json'

    try:
        with open(os.path.join(folder_path, "template.json"), 'w') as file:
            # Perform operations on the file here
            json.dump(template, file)

        print(f"File '{folder_path}' created successfully!")
        return send_file(r"C:\Users\nikhil\OneDrive\Desktop\dotevalu application\Deliverables_JustEvalve\justevalve_scanner_app\outputs", mimetype='image/png' ),200
    except OSError as e:
        print(f"An error occurred while creating file '{folder_path}': {e}")
        try:
            response_dict = entry_point_for_args(args)
            sorted_dict = {key[1:]: value for key, value in sorted(response_dict.items())}

            file_url = f"{request.url_root}outputs/{fileName}"
            return jsonify({"status": 200, "message": "success", 'data': sorted_dict, "file_url": file_url})

        except Exception as e:
            print(f"Error processing OMR: {str(e)}")
            return jsonify({"status": 400, 'message': "cannot Read Data From Image", "data": {}})

def entry_point_for_args(args):
    if args["debug"] is True:
        sys.tracebacklimit = 0
    for root in args["input_paths"]:
        return entry_point(Path(root), args)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)