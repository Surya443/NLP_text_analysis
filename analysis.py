import requests
from bs4 import BeautifulSoup
import nltk
import re
from nltk.corpus import stopwords
nltk.download('stopwords')
import openpyxl
import pandas as pd

def dataread(input_xlsx):

    try:
        #inorder to get each cell data from xlsx file as weblink we use openpyxl
        workbook = openpyxl.load_workbook(input_xlsx)
        worksheet = workbook.active
        url_list = []

        for row in worksheet.iter_rows(values_only=True):
            url_list.append(row[1])

        #the first cell doesnt contaain web address so we skip it
        return url_list[1::]
    
    except Exception as e:
        print(f"Error in dataread function: {str(e)}")

def stop_words(filenames):
    try:
        output_filename = 'stopwords.txt'

        # Open the output file in write mode
        with open(output_filename, 'w', encoding='utf-8') as output_file:

            # Loop through the input files
            for filename in filenames:
                
                # Open each input file in read mode
                with open(filename, 'r', encoding='iso-8859-1') as input_file:
                    # Read the contents of the file and write them to the output file
                    output_file.write(input_file.read())

            with open('stopwords.txt','r') as f:
                stop_words_list = [i.strip() for i in f]
        return stop_words_list
    
    except Exception as e:
        print(f"Error in stopwords function: {str(e)}")

def words(url,stop_words):
    try:
        response = requests.get(url)
        content = response.content
            
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        print(f"Text found: {text}")  # Add this line to check if any text is found
            
        # Tokenize the text and remove stop words
        words = nltk.word_tokenize(text)
        sentence = nltk.sent_tokenize(text)
        words = [word.lower() for word in words if word.lower() not in stop_words]
        sentence = [i.strip() for i in sentence]
        return words, sentence
    except Exception as e:
        print(f"Error in words function: {str(e)}")


def sentiment_analysis(words,positive_words,negative_words):
    try:
        pos_score,neg_score = 0,0

        for i in words:
            if i in positive_words:
                pos_score+=1
            if i in negative_words:
                 neg_score+=1
            if i not in positive_words or i not in negative_words:
                pass
        #refer to readme for formulas
        polarity_score = (pos_score - neg_score)/(pos_score + neg_score + 0.000001)
        subjectivity_score = (pos_score + neg_score)/(len(words) + 0.000001)

        return pos_score, neg_score, polarity_score, subjectivity_score
    
    except Exception as e:
        print(f"Error in sentiment_analysis function: {str(e)}")

def analysis_of_readability(sentences):

    try:
        complex_word_count = 0
        word_count = 0
        sentence_length = 0
        for i in sentences:
            words = nltk.word_tokenize(i)
            word_count += len(words)
            sentence_length += 1
            for j in words:
                vowel_count = sum(1 for letter in j if letter in 'aeiouAEIOU')
                if vowel_count > 2:
                    complex_word_count += 1
        #refer to readme for formulas
        avg_sentence_length = word_count / sentence_length
        avg_words_per_sentence = word_count / len(sentences)
        percent_complex_words = (complex_word_count / word_count) * 100
        fog_index = 0.4*(avg_sentence_length + percent_complex_words)
        
        return avg_sentence_length, percent_complex_words, fog_index, complex_word_count, avg_words_per_sentence
    
    except Exception as e:
        print(f"Error in analysis of readability function: {str(e)}")

def word_count(word):
    try:
        stop_words_nltk = set(stopwords.words('english'))
        punc = ['!','?',',',':','-']
        word_nltk = [i.lower() for i in word if i.lower() not in stop_words_nltk and punc]

        return len(word_nltk)
    
    except Exception as e:
        print(f'Error in word_count function : {str(e)}')
        return None

def complexwords(words):

    try:
        vowel_count = 0
        #words with two or more syllables is considered as complex word
        for i in words:
            if  i in ['a','e','i','o','u','A','E','I','O','U']:
                vowel_count += 1 
        complex_count = vowel_count/len(i)

        return complex_count
    
    except:
        print('Error in complexwords function')
        return None

def personal_pronouns(words):
   
    try:
        personal_pronouns_regex = r"\b(I|we|my|ours|us)\b(?![a-z])"
        personal_pronouns_count = 0
        for i in words:
            if re.search(personal_pronouns_regex, i):
                personal_pronouns_count += 1
                
        return personal_pronouns_count
    
    except:
        pass

if __name__ =='__main__':
    
    input_xlsx = 'Input.xlsx'
    url_list = dataread(input_xlsx)

    filenames =  ['StopWords_Auditor.txt', 'StopWords_Currencies.txt', 'StopWords_DatesandNumbers.txt','StopWords_Generic.txt',
                   'StopWords_GenericLong.txt','StopWords_Geographic.txt','StopWords_Names.txt']
    stop_words = stop_words(filenames)

    pos = open('positive-words.txt','r', encoding='iso-8859-1')
    neg = open('negative-words.txt','r', encoding='iso-8859-1')
 
    negative_words = [i.strip() for i in neg]
    positive_words = [i.strip() for i in pos]


    
    output = pd.read_csv('output.csv')
    output.drop(['AVG WORD LENGTH','SYLLABLE PER WORD'],inplace = True ,axis =1)

    for index, row in output.iterrows():
        url = url_list[index]
        word,sentence = words(url,stop_words)
        pos_score, neg_score, polarity_score, subjectivity_score = sentiment_analysis(word, positive_words, negative_words)
        avg_sentence_length, percent_complex_words, fog_index, complex_word_count,avg_words_per_sentence = analysis_of_readability(sentence)
        word_count_value = word_count(word)        
        complexwords_value = complexwords(word)
        personal_pronouns_count = personal_pronouns(word)
        
        #Update score values in the dataframe
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


