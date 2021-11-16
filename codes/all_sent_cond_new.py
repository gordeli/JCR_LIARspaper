# Working on a code that will populate the table [Review word pairs] with the values for TF for each condition
# import timing

import nltk
from nltk.corpus import wordnet as wn
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag.mapping import tagset_mapping, map_tag
from nltk.stem import WordNetLemmatizer
wnl = WordNetLemmatizer()
#text = " I stayed at the Grand Hyatt in Seattle last month. Very high quality, upscale and comfortable room for my 3 night stay. Excellent location in downtown Seattle, and Pike Place Market was within walking distance. The monorail was really close too, which I found very convenient.  /  / In the room itself, I absolutely loved the bathroom. It had both a separate shower and a standing tub, and definitely one of the nicest if not the nicest bathroom I've ever had in a hotel room. Bed was extremely comfortable, and I slept better than I normally do at home! The staff was extremely friendly and courteous, and they even accomodated a few special requests I had. Although check in was at 4, they allowed me to check in 2 hours early. This was overall an excellent hotel experience and I would recommend it to anybody visiting Seattle."

import sqlite3
import shutil # we use this library to create a copy of a file (in this case to duplicate the database
# so that we can loop over one instance while editing the other)
# Establish a SQLite connection to a database named 'Liars4.sqlite':
conn = sqlite3.connect('Liars7_sent_new.sqlite')
# # Get the cursor, which is used to traverse the database, line by line
cur = conn.cursor()
# Then we duplicate thedatabase, so that one can loop and edit it at the same time
# and 'open' the other 'instance' of the same database
shutil.copyfile('Liars7_sent_new.sqlite', 'Liars7_w.sqlite')
conn_w = sqlite3.connect('Liars7_w.sqlite')
cur_w = conn_w.cursor()

try:
    cur_w.execute('''ALTER TABLE Sentences_raw ADD TF_Real INTEGER NOT NULL DEFAULT 0''') # DEFAULT 0 was removed from the sql string
except:
    print("The column 'TF_Real' exists already")
    pass # handle the error

try:
    cur_w.execute('''ALTER TABLE Sentences_raw ADD TF_Fake INTEGER NOT NULL DEFAULT 0''') # DEFAULT 0 was removed from the sql string
except:
    print("The column 'TF_Fake' exists already")
    pass # handle the error

cur_w.execute('UPDATE Sentences_raw SET TF_Real = 0')
cur_w.execute('UPDATE Sentences_raw SET TF_Fake = 0')

sqlstr = 'SELECT Condition, Review FROM Participants JOIN Reviews ON Participants.id = Reviews.id' # Select query that instructs over what we will be iterating
for row in cur.execute(sqlstr):
    #reviewrow = reviewrow + 1
    reviewtext = row[1]
    sentences_dic = dict()
    sentences = sent_tokenize(reviewtext)
    for s in sentences:
        sentences_dic[s] = sentences_dic.get(s, 0) + 1

    if row[0] == 0:
        for sv in sentences_dic:
            count = sentences_dic[sv]
            cur_w.execute('UPDATE Sentences_raw SET TF_Real = TF_Real + ? WHERE Sentence = ?', (count, sv, ))
    elif row[0] == 1:
        for sv in sentences_dic:
            count = sentences_dic[sv]
            cur_w.execute('UPDATE Sentences_raw SET TF_Fake = TF_Fake + ? WHERE Sentence = ?', (count, sv, ))

conn_w.commit()

cur_w.close()
conn_w.close()
cur.close()
conn.close()

shutil.copyfile('Liars7_w.sqlite', 'Liars7_sent_new_cond.sqlite')
