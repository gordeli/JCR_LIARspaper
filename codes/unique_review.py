# This code calculates the number of unique words in each review:
# import timing
import re # import the library for regular expressions
from nltk.tokenize import sent_tokenize, word_tokenize

import sqlite3
import shutil
# Establish a SQLite connection to a database named 'Liars4.sqlite':
# conn = sqlite3.connect('mott_corpus_clean.sqlite')
conn = sqlite3.connect('Liars7_wf_fqn20210129.sqlite')
# Get the cursor, which is used to traverse the database, line by line
cur = conn.cursor()
shutil.copyfile('Liars7_wf_fqn20210129.sqlite', 'Liars7_w.sqlite')
conn_w = sqlite3.connect('Liars7_w.sqlite') # The database to be updated
cur_w = conn_w.cursor()

try:
    cur_w.execute('''ALTER TABLE Reviews ADD Review_uniqwords INTEGER NOT NULL DEFAULT 0''') # DEFAULT 0 was removed from the sql string
except:
    print("The column 'Review_uniqwords' exists already")
    pass # handle the error

# Create a list of rare word forms:
# 1. go through the database table [Word forms], add word forms to a list of rare word forms
# 2. for each review, check if each  word form is in the list, if yes, add 1

# creting a list of rare word forms:
sqlstr = 'SELECT Word_form, TF FROM [Review word forms]'
wordforms_rare = []
for row in cur.execute(sqlstr):
    wordform = row[0]
    TF = row[1]
    if TF < 21: # This number is highly corpus specific (27 for Liars, 28 for Mott?), 6.3 for Liars Pilot, 20.2 for Liars 7 (reviews only)
        wordforms_rare.append(wordform)

sqlstr = 'SELECT Review_cleaned FROM Reviews' # Select query that instructs over what we will be iterating
for row in cur.execute(sqlstr):
    reviewtext = row[0]
    p = re.compile('[^a-zA-Z\s]')
    text = p.sub(' ', reviewtext)
    # Change all to lower case:
    text_cleaned = text.lower()
    unique_words = 0
    for word in word_tokenize(text_cleaned):
        if word in wordforms_rare:
            unique_words = unique_words + 1
    cur_w.execute('UPDATE Reviews SET Review_uniqwords = ? WHERE Review_cleaned = ?', (unique_words,reviewtext, ))

conn_w.commit()
cur_w.close()
conn_w.close()
cur.close()
conn.close()

shutil.copyfile('Liars7_w.sqlite', 'Liars7_unique20210129.sqlite')
