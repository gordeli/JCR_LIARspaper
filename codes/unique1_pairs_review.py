# This code calculates the number of unique words in each review:

# from pathos.multiprocessing import ProcessingPool as Pool
import multiprocessing
from multiprocessing.pool import Pool

from tqdm import tqdm
import time
# import timing
import re # import the library for regular expressions
from nltk.tokenize import sent_tokenize, word_tokenize

import sqlite3
import shutil

def get_rarepairs():
    """ This code finds the list of rare word pairs
    """
    connn = sqlite3.connect('Liars7_unique1.sqlite')
    # Get the cursor, which is used to traverse the database, line by line
    currr = conn.cursor()

    sqlstr = 'SELECT Word_pair, TF FROM [Review word pairs]'
    wordpairs_rare = []
    for row in currr.execute(sqlstr):
        wordpair = row[0]
        TF = row[1]
        if TF < 2: # This number is highly corpus specific (27 for Liars, 28 for Mott?), 6.3 for Liars Pilot, 20.2 for Liars 7 (reviews only), 2.78 for pairs Liars 7, 2.98 for Ott, 3.90 for yelpCHIhotels, 3.49 for kaggle21k
            wordpairs_rare.append(wordpair)

    return wordpairs_rare

def process_row(arg):
    """
    this function receives a single row of a table
    and returns a pair (id, depth) for a given row
    """
    wordpairs_rare, row = arg
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

    return (unique_pairs, reviewtext)

def record_answers(curr, answers):
    """
    this function receives cursor to sql (cur) and list of answers List[(id, depth)]
    and records answers to the sql
    for now, this is single process code
    """
    for answer in answers:
        unique_pairs, reviewtext = answer
        curr.execute('UPDATE Reviews SET Uniqpairs1 = ? WHERE Review_cleaned = ?', (unique_pairs,reviewtext, ))

if __name__ == '__main__':

    conn = sqlite3.connect('Liars7_unique1.sqlite')
    # Get the cursor, which is used to traverse the database, line by line
    cur = conn.cursor()
    shutil.copyfile('Liars7_unique1.sqlite', 'Am_kg_w.sqlite')
    conn_w = sqlite3.connect('Am_kg_w.sqlite') # The database to be updated
    cur_w = conn_w.cursor()

    try:
        cur_w.execute('''ALTER TABLE Reviews ADD Uniqpairs1 INTEGER NOT NULL DEFAULT 0''') # DEFAULT 0 was removed from the sql string
    except:
        print("The column 'Uniqpairs1' exists already")
        pass # handle the error

    wordpairs_rare = get_rarepairs()

    sqlstr = 'SELECT Review_cleaned FROM Reviews' # Select query that instructs over what we will be iterating

    args = [(wordpairs_rare, row) for row in cur.execute(sqlstr)]   # read rows from sql

    print("start computing..")
    t0 = time.time()

    n_processes = multiprocessing.cpu_count()

    if n_processes == 1:
        print("single process")
        answers = [process_row(arg) for arg in args]  # single process each row in rows
    else:
        print(f"pool process with {n_processes} threads")
        # we call initializer function = set_wordnet so that each worker receives separate wn object
        with Pool(processes=n_processes) as pool:
            answers = list(tqdm(pool.imap(process_row, args), total = len(args)))

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

    shutil.copyfile('Am_kg_w.sqlite', 'Liars7_uniquepairs1.sqlite')
