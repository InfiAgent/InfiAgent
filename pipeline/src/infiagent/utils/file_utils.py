import csv
import io
import logging
import os
import shutil

import chardet

from .logger import get_logger

root_directory = os.path.abspath(__file__)
while 'infiagent' not in os.path.basename(root_directory):
    root_directory = os.path.dirname(root_directory)

TEMP_FILE_UPLOAD_DIR = f"{root_directory}/tmp/upload_files/"
MAX_INPUT_FILE_SIZE = 1024 * 1024 * 1024
SAMPLE_FILE_SIZE = 2048
CSV_DEFAULT_DELIMITER = ","
CSV_DELIMITERS = [',', '\t', ';', '|', ' ']

logger = get_logger()


def clear_files(upload_file_dir):
    for filename in os.listdir(upload_file_dir):
        file_path = os.path.join(upload_file_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Error: %s' % (file_path, e))
    shutil.rmtree(upload_file_dir)


def upload_files(uploaded_files, sandbox_id):
    uploaded_files_list = []

    if not uploaded_files:
        logging.info("No file upload")
        return uploaded_files_list
    else:
        logging.info("Got {} files to upload.".format(len(uploaded_files)))

    FILE_DIR = os.path.join(TEMP_FILE_UPLOAD_DIR, sandbox_id)
    if os.path.exists(FILE_DIR):
        clear_files(FILE_DIR)
    else:
        # if the demo_folder directory is not present then create it.
        os.makedirs(FILE_DIR)

    for uploaded_file in uploaded_files:
        # 获取文件的基本信息
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
        logging.info(file_details)

        uploaded_files_list.append(_process_files(uploaded_file, FILE_DIR))

    logging.info("All files saved to disk.")

    return uploaded_files_list


def _process_files(uploaded_file, output_dir):
    # Check if file size is more than 1 GB
    if uploaded_file.size > MAX_INPUT_FILE_SIZE:
        raise ValueError(f"File {uploaded_file.name} is larger than 1 GB")

    # Check if the file is a CSV and if the delimiter meets requirement
    if uploaded_file.name.endswith('.csv'):
        return _process_local_csv_file(uploaded_file, output_dir)
    else:
        new_file_path = os.path.join(output_dir, uploaded_file.name)
        with open(new_file_path, 'wb') as new_file:
            new_file.write(uploaded_file.getvalue())
        return new_file_path


def _process_local_csv_file(uploaded_file, output_dir):
    """
    Process the uploaded file to convert the delimiter if needed and save the content in the output directory.

    Args:
    - uploaded_file: File-like object of the uploaded file
    - output_dir (str): Directory where the processed file should be saved

    Returns:
    - str: The path to the saved file
    """
    # Decode the content of the uploaded file
    file_content = uploaded_file.read()
    content_stream = io.BytesIO(file_content)

    # Process the content stream
    converted_file_stream, converted = convert_delimiter_to_comma(content_stream)

    # Construct the output path
    new_file_path = os.path.join(output_dir, uploaded_file.name)

    # Write the processed content to the output path
    with open(new_file_path, 'wb') as file:
        file.write(converted_file_stream.getvalue())

    return new_file_path


def convert_delimiter_to_comma(content_stream: io.BytesIO) -> (io.BytesIO, bool):
    """
    Detects the delimiter of a CSV content stream and converts it to comma if it's not already.

    Args:
    - content_stream (io.BytesIO): Stream containing CSV content

    Returns:
    - tuple: New content stream with updated delimiter, flag indicating if conversion was done
    """
    sample = content_stream.read(SAMPLE_FILE_SIZE)
    content_stream.seek(0)

    # Use chardet to detect the encoding
    detected = chardet.detect(sample)
    encoding = detected.get('encoding', 'utf-8') or 'utf-8'
    decoded_sample = sample.decode(encoding, errors='replace')

    sniffer = csv.Sniffer()
    try:
        delimiter = sniffer.sniff(decoded_sample, delimiters=''.join(CSV_DELIMITERS)).delimiter
    except (csv.Error, UnicodeDecodeError) as e:
        logger.warning("Unable to confidently determine the delimiter for the CSV content. Return original file. "
                       "error: {}".format(str(e)))
        return content_stream, False

    if delimiter == CSV_DEFAULT_DELIMITER:
        logger.info("Original CSV file delimiter is ',', no need to convert.")
        return content_stream, False

    logger.info("Original CSV file delimiter is '{}', converting it to ','.".format(delimiter))
    reader = csv.reader(content_stream.getvalue().decode('utf-8').splitlines(), delimiter=delimiter)
    temp_output = io.StringIO()  # Temporary StringIO to hold string representation
    writer = csv.writer(temp_output, delimiter=CSV_DEFAULT_DELIMITER, lineterminator='\n')

    for row in reader:
        writer.writerow(row)

    # Convert StringIO value to bytes and write to BytesIO stream
    output_stream = io.BytesIO()
    output_stream.write(temp_output.getvalue().encode('utf-8'))
    output_stream.seek(0)
    return output_stream, True


def get_file_name_and_path(input_file: str):
    file_name = input_file.split("/")[-1]
    tos_path = input_file.replace(file_name, "")
    return file_name, tos_path