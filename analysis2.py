import requests
import asyncio
from aiohttp import ClientSession
from bs4 import BeautifulSoup
import nltk
import re
from nltk.corpus import stopwords
import openpyxl
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

#using asynchronous requests to fetch multiple URLs concurrently, improving the code's efficiency.

async def fetch_url(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            else:
                logging.error(f"Failed to fetch URL: {url}, Status Code: {response.status}")
                return None
    except Exception as e:
        logging.error(f"Error fetching URL: {url}, Error: {str(e)}")
        return None

async def fetch_all_urls(urls):
    async with ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)

def dataread(input_xlsx):
    try:
        workbook = openpyxl.load_workbook(input_xlsx)
        worksheet = workbook.active
        url_list = [row[1] for row in worksheet.iter_rows(values_only=True)][1:]
        return url_list
    except Exception as e:
        logging.error(f"Error in dataread function: {str(e)}")

def load_stop_words(filenames):
    try:
        stop_words_list = set()
        for filename in filenames:
            with open(filename, 'r', encoding='iso-8859-1') as input_file:
                stop_words_list.update(input_file.read().strip().split())

        return stop_words_list
    except Exception as e:
        logging.error(f"Error in load_stop_words function: {str(e)}")

def preprocess_text(text, stop_words):
    words = nltk.word_tokenize(text)
    sentence = nltk.sent_tokenize(text)
    words = [word.lower() for word in words if word.lower() not in stop_words]
    sentence = [i.strip() for i in sentence]
    return words, sentence

def analyze_sentiment(words, positive_words, negative_words):
    pos_score, neg_score = 0, 0

    for word in words:
        if word in positive_words:
            pos_score += 1
        if word in negative_words:
            neg_score += 1

    polarity_score = (pos_score - neg_score) / (pos_score + neg_score + 0.000001)
    subjectivity_score = (pos_score + neg_score) / (len(words) + 0.000001)
    return pos_score, neg_score, polarity_score, subjectivity_score

def analyze_readability(sentences):
    complex_word_count, word_count, sentence_length = 0, 0, 0

    for sentence in sentences:
        words = nltk.word_tokenize(sentence)
        word_count += len(words)
        sentence_length += 1
        for word in words:
            vowel_count = sum(1 for letter in word if letter in 'aeiouAEIOU')
            if vowel_count > 2:
                complex_word_count += 1

    avg_sentence_length = word_count / sentence_length
    avg_words_per_sentence = word_count / len(sentences)
    percent_complex_words = (complex_word_count / word_count) * 100
    fog_index = 0.4 * (avg_sentence_length + percent_complex_words)
    return avg_sentence_length, percent_complex_words, fog_index, complex_word_count, avg_words_per_sentence

def word_count(text, stop_words):
    words = nltk.word_tokenize(text)
    punc = ['!', '?', ',', ':', '-']
    word_nltk = [word.lower() for word in words if word.lower() not in stop_words and word not in punc]
    return len(word_nltk)

def complexwords(words):
    vowel_count = sum(1 for word in words if word in 'aeiouAEIOU')
    complex_count = vowel_count / len(words)
    return complex_count

def personal_pronouns(words):
    try:
        personal_pronouns_regex = r"\b(I|we|my|ours|us)\b(?![a-z])"
        personal_pronouns_count = len(re.findall(personal_pronouns_regex, ' '.join(words)))
        return personal_pronouns_count
    except Exception as e:
        logging.error(f"Error in personal_pronouns function: {str(e)}")

async def main():
    input_xlsx = 'Input.xlsx'
    url_list = dataread(input_xlsx)

    filenames = ['StopWords_Auditor.txt', 'StopWords_Currencies.txt', 'StopWords_DatesandNumbers.txt',
                 'StopWords_Generic.txt', 'StopWords_GenericLong.txt', 'StopWords_Geographic.txt', 'StopWords_Names.txt']
    stop_words = load_stop_words(filenames)

    pos = open('positive-words.txt', 'r', encoding='iso-8859-1')
    neg = open('negative-words.txt', 'r', encoding='iso-8859-1')

    negative_words = set([word.strip() for word in neg])
    positive_words = set([word.strip() for word in pos])

    urls_content = await fetch_all_urls(url_list)

    output = pd.read_csv('output.csv')
    output.drop(['AVG WORD LENGTH', 'SYLLABLE PER WORD'], inplace=True, axis=1)

    for index, row in output.iterrows():
        url = url_list[index]
        text = urls_content[index]
        if text:
            word, sentence = preprocess_text(text, stop_words)
            pos_score, neg_score, polarity_score, subjectivity_score = analyze_sentiment(word, positive_words,
                                                                                          negative_words)
            avg_sentence_length, percent_complex_words, fog_index, complex_word_count, avg_words_per_sentence = analyze_readability(
                sentence)
            word_count_value = word_count(text, stop_words)
            complexwords_value = complexwords(word)
            personal_pronouns_count = personal_pronouns(word)

            # Update score values in the dataframe
            output.at[index, 'POSITIVE SCORE'] = pos_score
            output.at[index, 'NEGATIVE SCORE'] = neg_score
            output.at[index, 'POLARITY SCORE'] = polarity_score
            output.at[index, 'SUBJECTIVITY SCORE'] = subjectivity_score
            output.at[index, 'AVG SENTENCE LENGTH'] = avg_sentence_length
            output.at[index, 'PERCENTAGE OF COMPLEX WORDS'] = percent_complex_words
            output.at[index, 'FOG INDEX'] = fog_index
            output.at[index, 'COMPLEX WORD COUNT'] = complex_word_count
            output.at[index, 'AVG NUMBER OF WORDS PER SENTENCE'] = avg_words_per_sentence
            output.at[index, 'WORD COUNT'] = word_count_value
            output.at[index, 'COMPLEX WORD COUNT'] = complexwords_value
            output.at[index, 'PERSONAL PRONOUNS'] = personal_pronouns_count

    # Save updated dataframe back to CSV file
    output.to_csv('final_output.csv', index=False)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

