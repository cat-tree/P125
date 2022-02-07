import pandas as pd

data = pd.read_excel("sqa_train_set_sfcfs.xlsx")
data.head()

import ast


def _parse_answer_coordinates(answer_coordinate_str):
    """Parses the answer_coordinates of a question.
    Args:
      answer_coordinate_str: A string representation of a Python list of tuple
        strings.
        For example: "['(1, 4)','(1, 3)', ...]"
    """

    try:
        answer_coordinates = []
        # make a list of strings
        coords = ast.literal_eval(answer_coordinate_str)
        # parse each string as a tuple
        for row_index, column_index in sorted(
                ast.literal_eval(coord) for coord in coords):
            answer_coordinates.append((row_index, column_index))
    except SyntaxError:
        raise ValueError('Unable to evaluate %s' % answer_coordinate_str)

    return answer_coordinates


def _parse_answer_text(answer_text):
    """Populates the answer_texts field of `answer` by parsing `answer_text`.
    Args:
      answer_text: A string representation of a Python list of strings.
        For example: "[u'test', u'hello', ...]"
      answer: an Answer object.
    """
    try:
        answer = []
        for value in ast.literal_eval(answer_text):
            answer.append(value)
    except SyntaxError:
        raise ValueError('Unable to evaluate %s' % answer_text)

    return answer


data['answer_coordinates'] = data['answer_coordinates'].apply(lambda coords_str: _parse_answer_coordinates(coords_str))
data['answer_text'] = data['answer_text'].apply(lambda txt: _parse_answer_text(txt))

data.head(10)

def get_sequence_id(example_id, annotator):
  if "-" in str(annotator):
    raise ValueError('"-" not allowed in annotator.')
  return f"{example_id}-{annotator}"

data['sequence_id'] = data.apply(lambda x: get_sequence_id(x.id, x.annotator), axis=1)
data.head()

# let's group table-question pairs by sequence id, and remove some columns we don't need
grouped = data.groupby(by='sequence_id').agg(lambda x: x.tolist())
grouped = grouped.drop(columns=['id', 'annotator', 'position'])
grouped['table_file'] = grouped['table_file'].apply(lambda x: x[0])
grouped.head(10)

# path to the directory containing all csv files
table_csv_path = "table_csv"

item = grouped.iloc[0]
table = pd.read_csv(table_csv_path + item.table_file[9:]).astype(str)

#display(table)
print("")
print(item.question)

import torch
from transformers import TapasTokenizer

# initialize the tokenizer
tokenizer = TapasTokenizer.from_pretrained("google/tapas-base")


encoding = tokenizer(table=table, queries=item.question, answer_coordinates=item.answer_coordinates, answer_text=item.answer_text,
                     truncation=True, padding="max_length", return_tensors="pt")
encoding.keys()