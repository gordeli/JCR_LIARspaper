# This code adds a word count for each review to the database
# import timing

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

import sqlite3
import shutil

# Establish a SQLite connection to a database named 'Liars4.sqlite':
conn = sqlite3.connect('Liars7_wordpairs_cond20210129.sqlite')
# Get the cursor, which is used to traverse the database, line by line
cur = conn.cursor()

shutil.copyfile('Liars7_wordpairs_cond20210129.sqlite', 'Liars7_w.sqlite')
conn_w = sqlite3.connect('Liars7_w.sqlite') # The database to be updated
cur_w = conn_w.cursor()

try:
    cur_w.execute('''ALTER TABLE Reviews ADD Word_pair_count INTEGER''')
except Exception as e:
    print(e)
    pass # handle the error

sqlstr = 'SELECT id, Review_cleaned FROM Reviews'

row_count = 0

for row in cur.execute(sqlstr):
    id = row[0]
    reviewtext = row[1]#.encode('ascii','ignore')
    #condition = int(row[0])
    wordpairs = dict() # Initializes an empty dictionary where we will keep track of all wordforms in the whole corpus of reviews and how many times their occurence values

    sentences = sent_tokenize(reviewtext)
    for s in sentences:
        words = word_tokenize(s)
        for i in range(len(words) - 2 + 1):
            key = tuple(words[i:i+2])
            if ',' in key or '.' in key or ':' in key or '!' in key or '?' in key or ';' in key:
                continue
            else:
                wordpairs[key] = wordpairs.get(key, 0) + 1
    pairs_review = 0
    for wp in wordpairs:
        pairs_review += wordpairs[wp]
    cur_w.execute('UPDATE Reviews SET Word_pair_count = ? WHERE id = ?', (pairs_review, id, ))

conn_w.commit()
cur.close()
conn.close()
cur_w.close()
conn_w.close()

shutil.copyfile('Liars7_w.sqlite', 'Liars7_reviewpairslength20210129.sqlite')
