# update Reviews table with www, which includes the "What" (object)
# import timing
import numpy as np
# import matplotlib as mpl
# import matplotlib.pyplot as plt
import scipy
from scipy import linalg, optimize, special
from scipy.special import comb
import nltk
from nltk.corpus import wordnet as wn
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag.mapping import tagset_mapping, map_tag
from nltk.stem import WordNetLemmatizer

import nltk
from nltk.corpus import wordnet as wn
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag.mapping import tagset_mapping, map_tag
from nltk.stem import WordNetLemmatizer
wnl = WordNetLemmatizer()

import sqlite3

def www_sent_obj(sentence):
    # This function take a sentence as an input and outpust the list of variables to be used for WWW, namely: s, t, www_ST,  www_ST_pairs, space_emb, time_emb, www_st_emb
    conn_sent = sqlite3.connect('Liars7_www_sent_obj.sqlite') # The copy of the original database to use for iterating
    # # Get the cursor, which is used to traverse the database, line by line
    cur_sent = conn_sent.cursor()
    sqlstr = "SELECT WC_LIWC, What, WWW_ST_obj, WWW_ST_pairs_obj, WWW_ST_emb_obj FROM Sentences_raw WHERE Sentence = ?"
    cur_sent.execute(sqlstr, (sentence,))
    row = cur_sent.fetchone()
    # print(row, type(row))
    wc = row[0]
    what = row[1]
    www = row[2]
    www_pairs = row[3]
    www_emb = row[4]

    return what, www, www_pairs, www_emb
    # if row:
    #     depth = row[1]
    #     return depth


# Let's write a function that calculates concreteness values based on BWK
def www_counts(text):
    # This function calculates the following:
    # 1) space_sent - the integrated over sentences number of space words
    # 2) time_sent - the integrated over sentences number of time words
    # 3) www_ST_sent - the integrated over sentences www value based on basic ST simulataneous presense (value 1) idea
    # 4) www_ST_pairs_sent - the integrated over sentences www value based on number of full pairs of ST idea
    # 5) space_emb_sent - the integrated over sentences space embedding (see van Laer paper) idea
    # 6) time_emb_sent - the integrated over sentences time embedding (see van Laer paper) idea
    # 7) www_ST_emb_sent - integrated over sentences based on van Laer concepts of space and time embeddings that is Space mixed with Perceptual processes and Time mixed with Causation, using standart LIWC dictionaries for the 4 categories (Space, Perceptual processes, Time and Causation)

    # First create a list of sentences for the text:
    sentences = sent_tokenize(text)
    sentences_dic = dict() # Note, in principle we do not need to count the repetitions of each sentence, as no texts in our dataset contain any sentece twice within the text
    for s in sentences:
        if s not in ['!', '.']: # we exclude artifact sentences like '.' and '!'
            sentences_dic[s] = sentences_dic.get(s, 0) + 1

    www_dic = dict()
    for sv in sentences_dic:
        www_dic[(sv, sentences_dic[sv])] = www_sent_obj(sv)

    return www_dic # dictionary with key: tuple of (sentence, occurence rate in text) and value = what, www, www_pairs, www_emb

# # Testing block:
# sentence = "I gave the app a try and experienced positive benefits from the start."
# print(www_sent(sentence))
# print(type(www_sent(sentence)))

# Main code block
import shutil # we use this library to create a copy of a file (in this case to duplicate the database
# so that we can loop over one instance while editing the other)
# Establish a SQLite connection to a database named 'Liars4.sqlite':
#conn = sqlite3.connect('Liars4.sqlite') # The copy of the original database to use for iterating
# # Get the cursor, which is used to traverse the database, line by line
#cur = conn.cursor()
# Then we duplicate thedatabase, so that one can loop and edit it at the same time
# and 'open' the other 'instance' of the same database
#shutil.copyfile('Liars4_TFNULL_current.sqlite', 'Liars4_w.sqlite')
shutil.copyfile('Liars7_www_sent_obj.sqlite', 'Liars7_w.sqlite') # we need to create an extra database to use it to generate another search query, because we will need a nested loop (a loop with a subloop)
conn = sqlite3.connect('Liars7_www_sent_obj.sqlite')
cur = conn.cursor()
conn_w = sqlite3.connect('Liars7_w.sqlite') # The database to be updated
cur_w = conn_w.cursor()

#create a new columns:
# WWW_ST - 1 if S, T > 0 , 0 otherwise, where S and T are the measures of Space and Time from LIWC
# WWW_ST_pairs - number of complete pairs of S, T
# Space_emb - 1 if only Space present, 2 if both Space and Perceptual processes present, Spatial embedding (as in van Laer, 2019 10.1093/jcr/ucy067 but with standart LIWC dictionaries for Space, Perceptual processes)
# Time_emb - 1 if only one of Time and Causation is present, 2 if both Time and Causation present, Temporal embedding (as in van Laer, 2019 10.1093/jcr/ucy067 but with standart LIWC dictionaries for Time and Causation)
# WWW_ST_emb WWWW measure based on the concepts of Spatial embedding and Temporal embedding as in van Laer, 2019 10.1093/jcr/ucy067 but with standart LIWC dictionaries for Space, Perceptual processes, Time and Causation (min(Se, Te))

try:
    cur_w.execute('''ALTER TABLE Reviews ADD What_sent INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
except:
    print("The column 'What_sent' exists already")
    pass # handle the error

try:
    cur_w.execute('''ALTER TABLE Reviews ADD WWW_ST_sent_obj INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
except:
    print("The column 'WWW_ST_sent_obj' exists already")
    pass # handle the error

# try:
#     cur_w.execute('''ALTER TABLE Reviews ADD WWW_ST_pairs INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
# except:
#     print("The column 'WWW_ST_pairs' exists already")
#     pass # handle the error

try:
    cur_w.execute('''ALTER TABLE Reviews ADD WWW_ST_pairs_sent_obj INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
except:
    print("The column 'WWW_ST_pairs_sent_obj' exists already")

try:
    cur_w.execute('''ALTER TABLE Reviews ADD WWW_ST_emb_sent_obj INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
except:
    print("The column 'WWW_ST_emb_sent_obj' exists already")
    pass # handle the error

#can you make a clumn formula? i.e set the column equal to some function of the other column?
#cur_w.execute('UPDATE Nouns SET Frequency = TF/?', (count, ))
sqlstr = 'SELECT id, Review FROM Reviews'
for row in cur.execute(sqlstr):
    prmr_id = row[0]
    # word_count = row[1]
    # space_count = round(word_count*row[2]/100)
    # time_count = round(word_count*row[3]/100)
    # percept_count = round(word_count*row[4]/100)
    # cause_count = round(word_count*row[5]/100)
    # space_emb = 0
    # if space_count > 0:
    #     space_emb = 1 + (percept_count > 0)
    # time_emb = (time_count > 0) + (cause_count > 0)
    # www_ST_emb = min(space_emb, time_emb)
    # cur_w.execute('UPDATE Reviews SET Space_emb = ?, Time_emb = ?, WWW_ST_emb = ? WHERE id = ?', (space_emb, time_emb, www_ST_emb, prmr_id, ))
    #
    # if space_count > 0 and time_count > 0:
    #     www_ST = 1
    #     www_STpairs = min(space_count, time_count)
    #     cur_w.execute('UPDATE Reviews SET WWW_ST = ?, WWW_ST_pairs = ? WHERE id = ?', (www_ST, www_STpairs, prmr_id, ))

    review_text = row[1]
    www = www_counts(review_text)
    what_sent = 0
    www_ST_sent = 0
    www_pairs_sent = 0
    www_emb_sent = 0
    for sf in www: #what, www, www_pairs, www_emb
        # NOTE: we do not count the repeated sentences twice. In this dataset this wouldn't matter though, as sentences do not repeat within the same review
        what_sent += www[sf][0]
        www_ST_sent += www[sf][1]
        www_pairs_sent += www[sf][2]
        www_emb_sent += www[sf][3]
    cur_w.execute('UPDATE Reviews SET What_sent = ?, WWW_ST_sent_obj = ?, WWW_ST_pairs_sent_obj = ?,  WWW_ST_emb_sent_obj = ? WHERE id = ?', (what_sent, www_ST_sent, www_pairs_sent, www_emb_sent, prmr_id, ))

conn_w.commit()

# # check if the values in the column add up to 1. Is there a way in sql to add up the values in a cokumn???
# unity_real_pos = 0
# unity_real_neg = 0
# unity_fake_pos = 0
# unity_fake_neg = 0
#
# sqlstr = 'SELECT [Fqn Real+],[Fqn Real-], [Fqn Fake+], [Fqn Fake-] FROM [Review word forms]'
# for row in cur_w.execute(sqlstr):
#     unity_real_pos = unity_real_pos + row[0]
#     unity_real_neg = unity_real_neg + row[1]
#     unity_fake_pos = unity_fake_pos + row[2]
#     unity_fake_neg = unity_fake_neg + row[3]
# print unity_real_pos, unity_real_neg, unity_fake_pos, unity_fake_neg

cur_w.close()
conn_w.close()
cur.close()
conn.close()

shutil.copyfile('Liars7_w.sqlite', 'Liars7_www.sqlite')
shutil.copyfile('Liars7_www.sqlite', r"C:\Users\i_gordeliy\Dropbox\Marketing\Liars\Liars7git\Liars7_www.sqlite")
