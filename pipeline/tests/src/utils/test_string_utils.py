import unittest
from src.utils import (
    is_image_link,
    extract_urls,
    extract_and_replace_url,
    replace_latex_format
)

class TestStringUtils(unittest.TestCase):
    def setUp(self):
        self.image_links = [
            'http://tosv.byted.org/obj/codegraph/sandbox/temp/ws987dcaa4dba3400b91707f6825146f4e/1696533095597078758.png'
        ]

        self.raw_inputs = [
            'Ran code\nSTDOUT:\n0.04886713118710795',
            'Ran code\nSTDOUT:\n0.04886713118710795\nGenerated an image: http://tosv.byted.org/obj/codegraph/sandbox/temp/ws987dcaa4dba3400b91707f6825146f4e/1696533095597078758.png',
            'Ran code\nSTDOUT:\n0.04886713118710795\n Add here on purpose Generated an image: http://tosv.byted.org/obj/codegraph/sandbox/temp/ws987dcaa4dba3400b91707f6825146f4e/1696533095597078758.png',
            'Ran code\nSTDOUT:\n0.04886713118710795\nGenerated an image: http://tosv.byted.org/obj/codegraph/sandbox/temp/ws987dcaa4dba3400b91707f6825146f4e/1696533095597078758.png\nGenerated files on server: http://tosv.byted.org/obj/codegraph/sandbox/fake.csv',
        ]

        self.format_outputs = [
            '```python\nRan code\nSTDOUT:\n0.04886713118710795```\n',
            '```python\nRan code\nSTDOUT:\n0.04886713118710795\n```\n![The Image](http://tosv.byted.org/obj/codegraph/sandbox/temp/ws987dcaa4dba3400b91707f6825146f4e/1696533095597078758.png)',
            '```python\nRan code\nSTDOUT:\n0.04886713118710795\n Add here on purpose ```\n![The Image](http://tosv.byted.org/obj/codegraph/sandbox/temp/ws987dcaa4dba3400b91707f6825146f4e/1696533095597078758.png)',
            '```python\nRan code\nSTDOUT:\n0.04886713118710795\n\n```\n![The Image](http://tosv.byted.org/obj/codegraph/sandbox/temp/ws987dcaa4dba3400b91707f6825146f4e/1696533095597078758.png)\n[fake.csv](http://tosv.byted.org/obj/codegraph/sandbox/fake.csv)',
        ]

        self.extracted_urls = [
            [],
            ['http://tosv.byted.org/obj/codegraph/sandbox/temp/ws987dcaa4dba3400b91707f6825146f4e/1696533095597078758.png'],
            ['http://tosv.byted.org/obj/codegraph/sandbox/temp/ws987dcaa4dba3400b91707f6825146f4e/1696533095597078758.png'],
            ['http://tosv.byted.org/obj/codegraph/sandbox/temp/ws987dcaa4dba3400b91707f6825146f4e/1696533095597078758.png', 'http://tosv.byted.org/obj/codegraph/sandbox/fake.csv']
        ]

        self.raw_latex_input = [
            'for people who earn $10,000 or $100,000 in each country:\n\n\\[\n\\begin{array}{|c|c|}\n\\hline\n\\textbf{native-country} & \\textbf{hours-per-week} \\\\\n\\hline\n?\\ & 45.55 \\\\\n Cambodia & 40.00 \\\\\n Canada & 45.64 \\\\\n... &... \\\\\n United-States & 45.51 \\\\\n Vietnam & 39.20 \\\\\n Yugoslavia & 49.50 \\\\\n\\hline\n\\end{array}\n\\]\n\n(Note: The country labeled "?" is likely a placeholder for countries with missing or unknown native-country values.)\n\nPlease note that this dataset contains non-binary values for the native-country column.'
        ]
        self.raw_latex_output = [
            'for people who earn $10,000 or $100,000 in each country:\n\n$$\n\\begin{array}{|c|c|}\n\\hline\n\\textbf{native-country} & \\textbf{hours-per-week} \\\\\n\\hline\n?\\ & 45.55 \\\\\n Cambodia & 40.00 \\\\\n Canada & 45.64 \\\\\n... &... \\\\\n United-States & 45.51 \\\\\n Vietnam & 39.20 \\\\\n Yugoslavia & 49.50 \\\\\n\\hline\n\\end{array}\n$$\n\n(Note: The country labeled "?" is likely a placeholder for countries with missing or unknown native-country values.)\n\nPlease note that this dataset contains non-binary values for the native-country column.'
        ]

    def test_is_image_link(self):
        for link in self.image_links:
            assert is_image_link(link) == True
    
    def test_extract_urls(self):
        for input_text, expected_matched_urls in zip(self.raw_inputs, self.extracted_urls):
            matched_urls = extract_urls(input_text)
            assert len(matched_urls) == len(expected_matched_urls)
            for url, expect_url in zip(matched_urls, expected_matched_urls):
                assert url == expect_url
    
    def test_extract_and_replace(self):
        for input_text, expected_output_text in zip(self.raw_inputs, self.format_outputs):
            real_output = extract_and_replace_url(input_text)
            if expected_output_text != real_output:
                print(f'real_output: {real_output}\nexpected_output: {expected_output_text}')
            assert expected_output_text == real_output
    
    def test_replace_latex_format(self):
        for input_text, expected_output_text in zip(self.raw_latex_input, self.raw_latex_output):
            real_output = replace_latex_format(input_text)
            assert expected_output_text == real_output


if __name__ == '__main__':
    unittest.main()
