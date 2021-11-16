# Code creates a table 'Sentences' and populates it with TF and RF values for each Sentence.

# import timing

import nltk
import re # import the library for regular expressions
from nltk.corpus import wordnet as wn
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag.mapping import tagset_mapping, map_tag
from nltk.stem import WordNetLemmatizer
wnl = WordNetLemmatizer()

import sqlite3
import shutil # we use this library to create a copy of a file (in this case to duplicate the database
# so that we can loop over one instance while editing the other)
# Establish a SQLite connection to a database named 'Liars4.sqlite':

conn = sqlite3.connect('Liars7_uniquepairs1.sqlite')
# Get the cursor, which is used to traverse the database, line by line
cur = conn.cursor()
# Then we duplicate thedatabase, so that one can loop and edit it at the same time
# and 'open' the other 'instance' of the same database
shutil.copyfile('Liars7_uniquepairs1.sqlite', 'Liars7_w.sqlite')
conn_w = sqlite3.connect('Liars7_w.sqlite')
cur_w = conn_w.cursor()

#Create a new table in the database:
# Note: The first line after 'try' statement deletes the table if it already exists.
# This is good at the stage of twicking your code. After the code for importing into
# the database from excel is finalized it is better to remove this: 'DROP TABLE IF EXISTS Reviews;'
# The 'try except else' that follows will generate a message if the table we are
# trying to create already exists.
try:
    cur_w.executescript('''DROP TABLE IF EXISTS Sentences_raw;
        CREATE TABLE Sentences_raw (
        id                        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        Sentence                  TEXT UNIQUE,
        TF                        INTEGER,
        RF                        INTEGER
        )''')
except sqlite3.OperationalError:
    print('Most probably the table we are trying to create already exists')
else:
    print('The table "Sentences_raw" has been successfully created')

# Next we define the column through which we are going to loop
sqlstr = 'SELECT Review FROM Reviews'

# try:
#     cur_w.execute('''ALTER TABLE Nouns ADD TF INTEGER NOT NULL DEFAULT 0''') # DEFAULT 0 was removed from the sql string
# except:
#     print "The column 'TF' exists already"
#     pass # handle the error

for row in cur.execute(sqlstr):
    #reviewrow = reviewrow + 1
    reviewtext = row[0]
    sentences = sent_tokenize(reviewtext)
    sentences_dic = dict()
    for s in sentences:
        sentences_dic[s] = sentences_dic.get(s, 0) + 1

    # cur_w.execute('''INSERT OR IGNORE INTO [Review word pairs] (Word_pair, TF) VALUES (?, ?)''', (word, 0))
            #cur_w.execute('UPDATE [Word forms] SET TF = 0')
        #text = word_tokenize(sentence)
        #print text
        #nltk_tagged = nltk.pos_tag(word_tokenize(sentence))
        #simplifiedTagged = [(word, map_tag('en-ptb', 'universal', tag)) for word, tag in nltk_tagged] #The output variable is a list of tupples, where the first item is a word, while the second one is a simplified POS tag
        # We need to perform lemmatization of each word to bring it to its wordnet form.
        #list_of_words_WordNet_POS = []
    #     for word, tag in nltk_tagged:
    #         if (tag[0] =='N' and len(word) > 1): # we did exclude 1-letter words
    #             if wn.synsets(wnl.lemmatize(word,'n'), pos='n')==[]: continue #excludes nouns which can not be found in WordNet
    #             else:
    #                 #print word
    #                 if len(wnl.lemmatize(word.lower(),'n')) > 1 :
    #                     if (hypernym_depth(wnl.lemmatize(word.lower(),'n')) == 0 and wnl.lemmatize(word.lower(),'n') != 'entity'): continue
    #                     else:
    #                         all_nouns[wnl.lemmatize(word.lower(),'n')] = all_nouns.get(wnl.lemmatize(word.lower(),'n'),0)+1 # we lowercased all words. before doing that there was about 3600 unique words. After the change 3076 words left
    #                 else: continue
    # nouns_in_review = nouns(reviewtext)
    for sv in sentences_dic:
        if len(sv)<3:
            print(sv)
        cur_w.execute('''INSERT OR IGNORE INTO Sentences_raw (Sentence, TF, RF) VALUES (?, ?, ?)''', (sv, 0, 0))
                #cur_w.execute('UPDATE [Word forms] SET TF = 0')
        count = sentences_dic[sv]
        cur_w.execute('UPDATE Sentences_raw SET TF = TF + ?, RF = RF + 1 WHERE Sentence = ?', (count, sv, ))
        #cur_w.execute('UPDATE Nouns SET [TF-er] = [TF-er] + 1 WHERE Noun = ?', (noun, ))

conn_w.commit()

cur_w.close()
conn_w.close()
cur.close()
conn.close()

shutil.copyfile('Liars7_w.sqlite', 'Liars7_sent_new.sqlite')

# # Testing block
# text = "The app was poorly designed. It should have contained video or images to guide users. Also, the font choice and color was distracting. The inclusion of math problems and word problems was also completely unnecessary. And not all of the pages were right side up."
# sentences = sent_tokenize(text)
# print(type(sentences))
