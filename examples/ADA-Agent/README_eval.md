# Evaluation
In this section, we introduce the details of evaluation benchmark and evaluation pipeline. 

## Dataset construction

![workflow](./figures/workflow-eval.png)
We contruct the evaluation dataset with the following procedures:

- Files Collection
- Description Generation
- Concepts Determinations
- Open-ended Question Generation
- Constraints and Format Requirements Generation
- Ground Truth Gathering & Filtering
- Manual Check

We first collect some existing csv files from GitHub. We split the evaluation into different topics, like correlation analysis and generate the related query. Considering the high-performance of OpenAI ADA, we borrow its generated results as reference initialization for high-quality annotation. 

## Statistics

We split the dataset into validation set and test set. The validation dataset contains 400 questions with 72 csv files. It is open to public and the test set is used for avoiding data leakage. All the subsequent information is based on the validation set. Here're some examples of the generated questions:

![question_examples](./figures/question_examples.png)

We categorize CSV files within the dataset into nine distinct categories, determined by their respective domains:

- Finance and Economics

- Health and Medical
- Demographics and Social Science
- Marketing and Consumer Behavior
- Energy and Environmental Monitoring
- Transportation, Logistics, and Tourism
- Culture, Entertainment, and Media
- Scientific Research and Technology
- Other Categories

Below is the pie chart depicting the categorical distribution:

![domain](./figures/domain.png)

We conduct statistical analyses on the individual concepts associated with each question, accounting for scenarios where a question encompasses multiple concepts:

![domain](./figures/concept.png)

This table illustrates the distribution of questions based on the number of underlying concepts they encompass :

| num of concepts  | #1   | #2   | #3   | #4   | Total |
| ---------------- | ---- | ---- | ---- | ---- | ----- |
| num of questions | 244  | 143  | 12   | 1    | 400   |

This table presents statistical findings regarding our filtration process :

| #Unfiltered questions | #Filtered questions | #Unfiltered subquestions | #Filtered subquestions | Avg.  Sub-Questions per Question |
| --------------------- | ------------------- | ------------------------ | ---------------------- | -------------------------------- |
| 770                   | 400                 | 1442                     | 706                    | 1.76                             |

## Evaluation

We both provide open-ended evaluation and closed-form evaluation. Open-ended evaluation is designed for human evaluation and closed-form evaluation is for automatic evaluation. In closed-form evaluation, the model is required to generated the response in the specific way and we use the exact match to evaluate the performance. In open-ended evaluation, we do not require any constraints during generation. Considering that most models hardly follow the format requirements, we add a reformat step after the models respond with GPT-3.5-turbo-16k which formats the responses with the format requirements. Here's a figure illustrating this process:

![](./figures/case-study-eval-data.png)

## Dataset

Our evaluation dataset includes a validation dataset and a test dataset. We only keep validation dataset for public. If you want to evaluate your own models, you can send us an e-mail about the API interface. We will update your results on leaderboard.  

The validation dataset comprises two .jsonl files, with each line representing a JSON-format dictionary containing the following keys. Additionally, a directory of CSV files for the associated questions is located under `data/`:

1. questions: `data/da-dev-questions.jsonl`

- id: Unique identifier for each question.
- question: The data analysis question.
- concepts: The concepts involved in the question.
- constraints: Constraints on the question that narrow down the solution into a closed-form.
- format: Format requirements for the output.
- file_name: File name of the corresponding csv file.

2. labels: `data/da-dev-labels.jsonl`

- id: Unique identifier for each question.
- common_answers: A list of labels in the format: `[[answer_name1, answer1],[answer_name2, answer2], ...]` which are correspondi1ng to "@answer_name[answer]" in the format part of questions

3. tables: `data/da-dev-tables`

## Usage

For closed-form questions, we have provided an evaluation script designed for use on the validation set:
```python
python3 eval_closed_form.py \
--questions_file_path data/da-dev-questions.jsonl \
--labels_file_path data/da-dev-labels.jsonl \
--responses_file_path [YOUR_RESPONSES_FILE]
```
The response file should adhere to the .jsonl format, with each line containing a JSON dictionary that includes the 'id' and 'response' fields, formatted as follows:

```json
{"id":0, "response":"The response with @answer_name[answer] for question 0 from your model."}
{"id":1, "response":"The response with @answer_name[answer] for question 1 from your model."}
```

## Metrics

For closed-form questions, we have following metrics:

- **Proportional Accuracy by Subquestions (PASQ):**

$$
\text{PSAQ} = \frac{1}{N} \sum_{i=1}^{N} \left( \frac{1}{M_i} \sum_{j=1}^{M_i} I_{ij} \right)
$$

Here, $N$ is the total number of questions, $M_i$ is the number of subquestions for the i-th question, and $I_{ij}$ is the indicator function for the j-th subquestion of the i-th question.

- **Accuracy by Questions (ABQ):**

$$
\text{ABQ} = \frac{1}{N} \sum_{i=1}^{N} \left( \prod_{j=1}^{M_i} I_{ij} \right)
$$

In this expression, the product 
\($\prod_{j=1}^{M_i} I_{ij}$\) equals 1 if all subquestions of the \(i\)-th question are answered correctly, and 0 otherwise.

- **Uniform Accuracy by Subquestions (UASQ):**

$$
\text{UASQ} = \frac{1}{\sum_{i=1}^{N} M_i} \sum_{i=1}^{N} \sum_{j=1}^{M_i} I_{ij}
$$

Here, the total accuracy is the sum of the values of the indicator function across all subquestions, normalized by the total number of subquestions in the dataset.

## Results

We set temperature=0.2, top_p=1.0 and frequency_penalty=0.0 for all the models on the validation set.

| Model                | PSAQ (%) | ABQ (%) | UASQ (%) |
| -------------------- | -------- | ------- | -------- |
| gpt-4-0613           | 65.26    | 59.75   | 66.05    |
| gpt-3.5-turbo-0613   | 55.35    | 47.25   | 52.21    |
| llama-2-7b           | 37.53    | 32.49   | 34.01    |
| code-llama-7b        | 47.59    | 39.59   | 44.67    |
| code-llama-python-7b | 47.03    | 40.86   | 40.78    |
| chatglm-3-6b         | 18.10    | 14.84   | 15.19    |

We draw a spider chart to show PSAQ with every concept:

![spider](./figures/spider.png)

We also report the ABQ where questions involved only one concept and more then one concepts.

| Model                | 1 concept (%) | >1 concepts (%) | Overall (%) |
| -------------------- | ------------- | --------------- | ----------- |
| gpt-4-0613           | 61.07         | 57.34           | 59.75       |
| gpt-3.5-turbo-0613   | 52.46         | 39.86           | 47.25       |
| llama-2-7b           | 41.60         | 19.58           | 32.49       |
| code-llama-7b        | 46.64         | 28.67           | 39.59       |
| code-llama-python-7b | 48.74         | 28.67           | 40.86       |
| chatglm-3-6b         | 18.10         | 10.07           | 14.84       |


