# This code adds a word count for each review to the database
# import timing

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

import sqlite3
import shutil


def wordforms(text):
    import re # import the library for regular expressions
    from nltk.tokenize import word_tokenize
    p = re.compile('[^a-zA-Z\s]')
    text = p.sub(' ', text)
    # Change all to lower case:
    text_cleaned = text.lower()

    #sentences = sent_tokenize(text_cleaned)
    word_forms = dict() # Initializes an empty dictionary where we will keep track of all wordforms in the whole corpus of reviews and how many times their occurence values
    for word in word_tokenize(text_cleaned):
        word_forms[word] = word_forms.get(word,0) + 1
    return word_forms

# Establish a SQLite connection to a database named 'Liars4.sqlite':
conn = sqlite3.connect('Liars7_wordforms_cond20210129.sqlite')
# Get the cursor, which is used to traverse the database, line by line
cur = conn.cursor()

shutil.copyfile('Liars7_wordforms_cond20210129.sqlite', 'Liars7_w.sqlite')
conn_w = sqlite3.connect('Liars7_w.sqlite') # The database to be updated
cur_w = conn_w.cursor()

try:
    cur_w.execute('''ALTER TABLE Reviews ADD Review_word_count INTEGER''')
except Exception as e:
    print(e)
    pass # handle the error

sqlstr = 'SELECT id, Review_cleaned FROM Reviews'

row_count = 0

for row in cur.execute(sqlstr):
    count_review = 0
    id = row[0]
    reviewtext = row[1]#.encode('ascii','ignore')
    #condition = int(row[0])
    word_forms_review = wordforms(reviewtext)
    for word in word_forms_review:
        count_review = count_review + word_forms_review[word]
    cur_w.execute('UPDATE Reviews SET Review_word_count = ? WHERE id = ?', (count_review, id, ))

conn_w.commit()
cur.close()
conn.close()
cur_w.close()
conn_w.close()

shutil.copyfile('Liars7_w.sqlite', 'Liars7_reviewlength20210129.sqlite')
