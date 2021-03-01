
# This code calculates the number of unique words in each review:
# import timing
import re # import the library for regular expressions
from nltk.tokenize import sent_tokenize, word_tokenize

import sqlite3
import shutil
# Establish a SQLite connection to a database named 'Liars4.sqlite':
# conn = sqlite3.connect('mott_corpus_clean.sqlite')
conn = sqlite3.connect('Liars7_wf_fqn_pairs20210129.sqlite')
# Get the cursor, which is used to traverse the database, line by line
cur = conn.cursor()
shutil.copyfile('Liars7_wf_fqn_pairs20210129.sqlite', 'Liars7_w.sqlite')
conn_w = sqlite3.connect('Liars7_w.sqlite') # The database to be updated
cur_w = conn_w.cursor()

try:
    cur_w.execute('''ALTER TABLE Reviews ADD Uniqpairs INTEGER NOT NULL DEFAULT 0''') # DEFAULT 0 was removed from the sql string
except:
    print("The column 'Uniqpairs' exists already")
    pass # handle the error

# Create a list of rare word forms:
# 1. go through the database table [Word forms], add word forms to a list of rare word forms
# 2. for each review, check if each  word form is in the list, if yes, add 1

# creting a list of rare word forms:
sqlstr = 'SELECT Word_pair, TF FROM [Review word pairs]'
wordpairs_rare = []
for row in cur.execute(sqlstr):
    wordpair = row[0]
    TF = row[1]
    if TF < 3: # This number is highly corpus specific (27 for Liars, 28 for Mott?), 6.3 for Liars Pilot, 20.2 for Liars 7 (reviews only), 2.78 for pairs Liars 7
        wordpairs_rare.append(wordpair)

sqlstr = 'SELECT Review_cleaned FROM Reviews' # Select query that instructs over what we will be iterating
for row in cur.execute(sqlstr):
    reviewtext = row[0]
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
    unique_pairs = 0
    for wp in wordpairs:
        wp_str =  ' '.join(wp)
        if wp_str in wordpairs_rare:
            unique_pairs = unique_pairs + wordpairs[wp]
    cur_w.execute('UPDATE Reviews SET Uniqpairs = ? WHERE Review_cleaned = ?', (unique_pairs,reviewtext, ))

conn_w.commit()
cur_w.close()
conn_w.close()
cur.close()
conn.close()

shutil.copyfile('Liars7_w.sqlite', 'Liars7_unique_pairs20210129.sqlite')
