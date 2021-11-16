# This code adds a word count for each review to the database
# import timing

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

import sqlite3
import shutil

# Establish a SQLite connection to a database named 'Liars4.sqlite':
conn = sqlite3.connect('Liars7_sent_new_cond.sqlite')
# Get the cursor, which is used to traverse the database, line by line
cur = conn.cursor()

shutil.copyfile('Liars7_sent_new_cond.sqlite', 'Liars7_w.sqlite')
conn_w = sqlite3.connect('Liars7_w.sqlite') # The database to be updated
cur_w = conn_w.cursor()

try:
    cur_w.execute('''ALTER TABLE Reviews ADD N_sentences_raw INTEGER''')
except Exception as e:
    print(e)
    pass # handle the error

sqlstr = 'SELECT id, Review FROM Reviews'

row_count = 0

for row in cur.execute(sqlstr):
    id = row[0]
    reviewtext = row[1]#.encode('ascii','ignore')
    #condition = int(row[0])
    sentences_dic = dict()
    sentences = sent_tokenize(reviewtext)
    for s in sentences:
        sentences_dic[s] = sentences_dic.get(s, 0) + 1
    sent_review = 0
    for sv in sentences_dic:
        if sv not in ['.', '!'] and len(sv)>2:
            sent_review += sentences_dic[sv]
        else: continue
    cur_w.execute('UPDATE Reviews SET N_sentences_raw = ? WHERE id = ?', (sent_review, id, ))

conn_w.commit()
cur.close()
conn.close()
cur_w.close()
conn_w.close()

shutil.copyfile('Liars7_w.sqlite', 'Liars7_review_sent_new_length.sqlite')
