import os
import random
import re
import string
from urllib.parse import urlparse


def is_image_link(url):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    if any(url.endswith(ext) for ext in image_extensions):
        return True

    return False


def extract_filename_from_url(url):
    parsed_url = urlparse(url)
    return os.path.basename(parsed_url.path)


def clean_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)


# Generate a random string of specified length
def generate_random_string(length=12):
    characters = string.ascii_letters + string.digits  # both upper and lowercase letters and digits
    return ''.join(random.choice(characters) for i in range(length))


def extract_urls(text):
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    all_matched_urls = re.findall(url_pattern, text)
    return all_matched_urls


def replace_latex_format(s):
    # replace \\(...\\) format
    s = re.sub(r'\\\((.*?)\\\)', r'$$\1$$', s, flags=re.DOTALL)

    # replace \\[...\\] format
    s = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', s, flags=re.DOTALL)

    return s


def extract_and_replace_url(text):
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    all_matched_urls = re.findall(url_pattern, text)
    # print(f"matched_urls: {all_matched_urls}")
    text = text.replace("Generated an image: ", "")
    text = text.replace("Generated files on server: ", "")

    new_urls = []
    for extracted_url in all_matched_urls:
        if is_image_link(extracted_url):
            new_url = f'![The Image]({extracted_url})'
        else:
            filename = extract_filename_from_url(extracted_url)
            new_url = f'[{filename}]({extracted_url})'

        new_urls.append(new_url)
        text = text.replace(extracted_url, "")

    text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

    return f'```python\n{text}```' + "\n" + "\n".join(new_urls)


def contains_chinese(input_context: str) -> bool:
    for char in input_context:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False
