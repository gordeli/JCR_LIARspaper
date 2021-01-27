# The code adds 'depth' (number of hypernym values to the table [Noun-lemmas])

from pathos.multiprocessing import ProcessingPool as Pool
n_processes = 28
from tqdm import tqdm
import time

def get_n_rows(input_file_name, sqlstr):
    conn = sqlite3.connect(input_file_name)
    cur = conn.cursor()
    rows = [row for row in cur.execute(sqlstr)]
    cur.close()
    conn.close()
    return len(rows)

import nltk
from nltk.corpus import wordnet as wn

# Now lets define the fuctions to find both hypernym and hyponym depth.

def get_hypernyms(synset):
    hypernyms = set()
    for h in synset.hypernyms():
        hypernyms |= set(get_hypernyms(h))
    return hypernyms | set(synset.hypernyms())

def hyp_num(noun, POS): # 20200617 added POS option to make sure we pick the right synset (proper none or not)
    # if dry:
    #     return 1
    synsets = wn.synsets(noun, 'n')
    if POS != 'NNP':
        for s in synsets:
            if s.instance_hypernyms() != []:
                continue
            else:
                synset = s
                break
    else:
        synset = synsets[0]
        for s in synsets:
            if s.instance_hypernyms() == []:
                continue
            else:
                synset = s.instance_hypernyms()[0]
                break
    # first_s.name().split('.')[1]
    hyp_set = get_hypernyms(synset)
    if POS == 'NNP':
        return 1 + len(hyp_set)
    else:
        return len(hyp_set)

# Main code block
import sqlite3
import shutil # we use this library to create a copy of a file (in this case to duplicate the database
# so that we can loop over one instance while editing the other)
# Establish a SQLite connection to a database named 'Liars4.sqlite':
conn = sqlite3.connect('yelp_wordforms.sqlite') # The copy of the original database to use for iterating
# # Get the cursor, which is used to traverse the database, line by line
cur = conn.cursor()
# Then we duplicate thedatabase, so that one can loop and edit it at the same time
# and 'open' the other 'instance' of the same database
shutil.copyfile('yelp_wordforms.sqlite', 'Liars7_w.sqlite')
input_file_name = 'yelp_wordforms.sqlite'
conn_w = sqlite3.connect('Liars7_w.sqlite') # The database to be updated
cur_w = conn_w.cursor()

sqlstr = 'SELECT id, Noun_lemma FROM [Noun-lemmas]' # Select query that instructs over what we will be iterating
n_rows = get_n_rows(input_file_name,sqlstr)
print('Number of rows {}'.format(n_rows))

rows = [row for row in cur.execute(sqlstr)]

for row in cur.execute(sqlstr):
    id = row[0]
    noun = row[1]
    try:
        depth = hyp_num(noun, 'NN')
        cur_w.execute('UPDATE [Noun-lemmas] SET WordNet_depth = ? WHERE id = ?', (depth, id, ))
    except:
        if noun == 'google':
            depth = hyp_num(noun, 'NNP')
            cur_w.execute('UPDATE [Noun-lemmas] SET WordNet_depth = ? WHERE id = ?', (depth, id, ))
        else:
            print("Didn't calculate for the following noun_lemma: ", noun)

conn_w.commit()
cur_w.close()
conn_w.close()
cur.close()
conn.close()

shutil.copyfile('Liars7_w.sqlite', 'yelp_nouns.sqlite')
