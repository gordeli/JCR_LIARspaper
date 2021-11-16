# update Sentences table with different values necessary to calculate WWW and maybe Narrative (Transportation)
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

# Main code block
import sqlite3
import shutil # we use this library to create a copy of a file (in this case to duplicate the database
# so that we can loop over one instance while editing the other)
# Establish a SQLite connection to a database named 'Liars4.sqlite':
#conn = sqlite3.connect('Liars4.sqlite') # The copy of the original database to use for iterating
# # Get the cursor, which is used to traverse the database, line by line
#cur = conn.cursor()
# Then we duplicate thedatabase, so that one can loop and edit it at the same time
# and 'open' the other 'instance' of the same database
#shutil.copyfile('Liars4_TFNULL_current.sqlite', 'Liars4_w.sqlite')
shutil.copyfile('Liars7_LIWC_sent_new.sqlite', 'Liars7_w.sqlite') # we need to create an extra database to use it to generate another search query, because we will need a nested loop (a loop with a subloop)
conn = sqlite3.connect('Liars7_LIWC_sent_new.sqlite')
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
    cur_w.execute('''ALTER TABLE Sentences_raw ADD WWW_ST INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
except:
    print("The column 'WWW_ST' exists already")
    pass # handle the error

try:
    cur_w.execute('''ALTER TABLE Sentences_raw ADD WWW_ST_pairs INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
except:
    print("The column 'WWW_ST_pairs' exists already")
    pass # handle the error

try:
    cur_w.execute('''ALTER TABLE Sentences_raw ADD Space_emb INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
except:
    print("The column 'Space_emb' exists already")
    pass # handle the error

try:
    cur_w.execute('''ALTER TABLE Sentences_raw ADD Time_emb INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
except:
    print("The column 'Time_emb' exists already")
    pass # handle the error

try:
    cur_w.execute('''ALTER TABLE Sentences_raw ADD WWW_ST_emb INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
except:
    print("The column 'WWW_ST_emb' exists already")
    pass # handle the error

#can you make a clumn formula? i.e set the column equal to some function of the other column?
#cur_w.execute('UPDATE Nouns SET Frequency = TF/?', (count, ))
sqlstr = 'SELECT id, WC_LIWC, space_LIWC, time_LIWC, percept_LIWC, cause_LIWC FROM Sentences_raw'
for row in cur.execute(sqlstr):
    prmr_id = row[0]
    word_count = row[1]
    space_count = round(word_count*row[2]/100)
    time_count = round(word_count*row[3]/100)
    percept_count = round(word_count*row[4]/100)
    cause_count = round(word_count*row[5]/100)
    space_emb = 0
    if space_count > 0:
        space_emb = 1 + (percept_count > 0)
    time_emb = (time_count > 0) + (cause_count > 0)
    www_ST_emb = min(space_emb, time_emb)
    cur_w.execute('UPDATE Sentences_raw SET Space_emb = ?, Time_emb = ?, WWW_ST_emb = ? WHERE id = ?', (space_emb, time_emb, www_ST_emb, prmr_id, ))

    if space_count > 0 and time_count > 0:
        www_ST = 1
        www_STpairs = min(space_count, time_count)
        cur_w.execute('UPDATE Sentences_raw SET WWW_ST = ?, WWW_ST_pairs = ? WHERE id = ?', (www_ST, www_STpairs, prmr_id, ))


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

shutil.copyfile('Liars7_w.sqlite', 'Liars7_www_sent_new.sqlite')
