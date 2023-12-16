import csv
import io
import os
import unittest

from src.utils import upload_files, clear_files, convert_delimiter_to_comma


class UploadedFile:
    def __init__(self, name, data, type):
        self.name = name
        self._data = data
        self.type = type
        self.size = len(data)

    def getvalue(self):
        return self._data

    def read(self):
        return self._data


class TestFileUtils(unittest.TestCase):

    def setUp(self):
        # Setup code: create some sample files for testing
        self.sample_csv_file_comma = UploadedFile(name='sample_comma.csv',
                                                  data=b'col1,col2,col3\n1,2,3\n4,5,6', type='text/csv')
        self.sample_csv_file_semicolon = UploadedFile(name='sample_semicolon.csv',
                                                      data=b'col1;col2;col3\n1;2;3\n4;5;6', type='text/csv')
        self.sample_txt_file = UploadedFile(name='sample.txt', data=b'Sample text file content', type='text/plain')

    def test_upload_non_csv_file(self):
        # Test uploading a non-CSV file
        result = upload_files([self.sample_txt_file])
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].endswith('sample.txt'))

    def test_upload_csv_file_comma(self):
        # Test uploading a CSV file with comma as delimiter
        result = upload_files([self.sample_csv_file_comma])
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].endswith('sample_comma.csv'))

    def test_upload_csv_file_semicolon(self):
        # Test uploading a CSV file with semicolon as delimiter
        result = upload_files([self.sample_csv_file_semicolon])
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].endswith('sample_semicolon.csv'))

        # Check if the file has been converted to use comma as delimiter
        with open(result[0], 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            self.assertEqual(rows, [['col1', 'col2', 'col3'], ['1', '2', '3'], ['4', '5', '6']])

    def test_clear_stored_files(self):
        # Test clearing stored files
        upload_files([self.sample_txt_file, self.sample_csv_file_comma])
        clear_files("./tmp/upload_files/")
        self.assertEqual(len(os.listdir("./tmp/upload_files/")), 0)

    def test_comma_delimiter(self):
        content = "a,b,c\n1,2,3\n"

        # Encode the string to bytes
        byte_content = content.encode()
        bytes_stream = io.BytesIO(byte_content)

        new_stream, converted = convert_delimiter_to_comma(bytes_stream)
        self.assertEqual(converted, False)
        self.assertEqual(new_stream.getvalue().decode(), content)

    def test_semicolon_delimiter(self):
        content = "a;b;c\n1;2;3\n"
        expected_content = "a,b,c\n1,2,3\n"

        # Encode the string to bytes
        byte_content = content.encode()
        bytes_stream = io.BytesIO(byte_content)

        new_stream, converted = convert_delimiter_to_comma(bytes_stream)
        self.assertEqual(converted, True)
        self.assertEqual(new_stream.getvalue().decode(), expected_content)

    def test_tab_delimiter(self):
        content = "a\tb\tc\n1\t2\t3\n"
        expected_content = "a,b,c\n1,2,3\n"
        byte_content = content.encode()
        bytes_stream = io.BytesIO(byte_content)
        new_stream, converted = convert_delimiter_to_comma(bytes_stream)
        self.assertEqual(converted, True)
        string_content = new_stream.getvalue().decode()
        self.assertEqual(string_content, expected_content)

    def tearDown(self):
        # Cleanup code: remove any created files and directories
        clear_files("./tmp/upload_files/")


if __name__ == '__main__':
    unittest.main()
