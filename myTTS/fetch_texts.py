from json import JSONDecodeError
from typing import Iterator, Tuple
import re
import json
from loguru import logger
from utils import find_anki_notes
from tqdm import tqdm

logger.remove()
logger.add("logs/fetch_texts.log", rotation="10 MB", level="INFO")

def normalize(text):
    """
    Normalize the input text by removing optional components:
    - Parentheses: Remove content inside parentheses, including the parentheses.
    - Slashes: Keep only the first option when multiple options are separated by slashes.
    - Brackets: Remove content inside brackets, including the brackets.
    a little (bit) -> a little
    sb -> somebody

    Args:
        text (str): The input string to normalize.

    Returns:
        str: The normalized string.
    """
    # Remove content inside parentheses, including the parentheses
    text = re.sub(r'\s*\([^)]*\)', '', text)

    # Remove content inside brackets, including the brackets
    text = re.sub(r'\s*\[[^\]]*\]', '', text)

    # Strip any extra whitespace introduced during normalization
    text = re.sub(r'\s+', ' ', text).strip()

    text = re.sub(r'\bsb\b', 'somebody', text)
    text = re.sub(r'\bsth\b', 'something', text)

    return text

def try_json(s):
    try:
        return json.loads(s)
    except JSONDecodeError as e:
        logger.error(f'incorrect JSON:\n---\n {s}')
        return []

def should_add_sentence_audio(tags):
    """
    only add sentence audio for intermediates
    """

    # exclude beginner
    if "CEFR_A1" in tags:
        return False

    # very common expressions
    if "K_高频普通" in tags or "CEFR_A2" in tags:
        return True

    # common expressions that has CEFR tag
    if "K_高频进阶" in tags and bool({f"CEFR_{level}" for level in ["B1", "B2", "C1", "C2"]} & set(tags)):
        return True

    # judge by B1-B2 CEFR for less common expressions
    return bool(set(tags) & {"CEFR_B1", "CEFR_B2"})

# ban optional components. eg. "that depends | it (all) depends"
ban_pattern = re.compile('[/|]')

def process_word(fields, text_pbar):
    word = fields["word"]
    if not ban_pattern.search(word):
        normalized_word = normalize(word)
        yield fields["id"], normalized_word
    text_pbar.update(1)

def process_examples(examples, tags, text_pbar):
    if should_add_sentence_audio(tags):
        for eg in examples:
            normalized_eg_en = normalize(eg["en"])
            yield eg["name"], normalized_eg_en
            text_pbar.update(1)
    else:
        text_pbar.update(len(examples))

def fetch_texts() -> Iterator[Tuple[str, str]]:
    """
    Fetches texts with unique IDs. This function can be customized by developers.
    :return: Iterator yielding tuples of (text_id, text).
    """
    todos = find_anki_notes(f'("deck:KEXP3::1. 读::1) 基础" OR "deck:KEXP3::1. 读::2) 高频::普通" OR "deck:KEXP3::1. 读::2) 高频::进阶" OR "deck:KEXP3::1. 读::3) 中频")')

    with tqdm(total=len(todos), desc="Processing notes") as note_pbar:
        for note in todos:
            fields = note["fields"]
            tags = note["tags"]

            examples = try_json(egs) if (egs:=fields["examples"]) else []

            with tqdm(total=len(examples) + 1, desc=f"Processing Texts in Note {fields['id']}", unit='text') as text_pbar:
                try:
                    yield from process_word(fields, text_pbar)
                    yield from process_examples(examples, tags, text_pbar)
                except Exception as e:
                    logger.error(f"Error processing note {fields['id']}: {e}")

            note_pbar.update(1)

