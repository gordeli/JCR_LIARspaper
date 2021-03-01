# The code adds 'depth' (number of hypernym values to the table [Noun-lemmas])

from pathos.multiprocessing import ProcessingPool as Pool
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
conn = sqlite3.connect('Liars7_wordforms.sqlite') # The copy of the original database to use for iterating
# # Get the cursor, which is used to traverse the database, line by line
cur = conn.cursor()
# Then we duplicate thedatabase, so that one can loop and edit it at the same time
# and 'open' the other 'instance' of the same database
shutil.copyfile('Liars7_wordforms.sqlite', 'Liars7_w.sqlite')
input_file_name = 'Liars7_wordforms.sqlite'
conn_w = sqlite3.connect('Liars7_w.sqlite') # The database to be updated
cur_w = conn_w.cursor()

sqlstr = 'SELECT id, Noun_lemma FROM [Noun-lemmas]' # Select query that instructs over what we will be iterating
n_rows = get_n_rows(input_file_name,sqlstr)
print('Number of rows {}'.format(n_rows))


def process_row(row):
    """
    this function receives a single row of a table 
    and returns a pair (id, depth) for a given row 
    """

    id = row[0]
    noun = row[1]
    try:
        depth = hyp_num(noun, 'NN')
    except:
        if noun == 'google':
            depth = hyp_num(noun, 'NNP')
        else:
            depth = None
            print("Didn't calculate for the following noun_lemma: ", noun)
    time.sleep(0.005)
    return  (id, depth)

def record_answers(cur, answers):
    """
    this function receives cursor to sql (cur) and list of answers List[(id, depth)]
    and records answers to the sql

    for now, this is single process code
    """
    for answer in answers:
        id, depth = answer
        if not depth is None:
            cur_w.execute('UPDATE [Noun-lemmas] SET WordNet_depth = ? WHERE id = ?', (depth, id, ))


rows = [row for row in cur.execute(sqlstr)]   # read rows from sql

print("start computing..")
t0 = time.time()


n_processes = 50

if n_processes == 1:
    print("single process")
    answers = [process_row(row) for row in rows]  # single process each row in rows
else:
    print(f"pool process with {n_processes} threads")
    with Pool(proceses=n_processes) as pool:
        answers = list(tqdm(pool.imap(process_row, rows), total = len(rows)))


print(f"finished computing in {time.time() - t0} seconds...")


t0 = time.time()
print("start recording...")                                              
record_answers(cur_w, answers)   # recording answers
print(f"finished recording in {time.time() - t0} seconds")


conn_w.commit()
cur_w.close()
conn_w.close()
cur.close()
conn.close()

shutil.copyfile('Liars7_w.sqlite', 'Liars7_nouns.sqlite')
