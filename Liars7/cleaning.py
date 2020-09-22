# This code adds an extra column to the table 'Reviews' and populates it with
# corrected text of the reviews. The purpose of this is to avoid repeating the
# time-costly spellchecking correction everytime we call the nouns() function.

# The multiprocessing and progress bar functionality was added by Vasily Pestun

from pathos.multiprocessing import ProcessingPool as Pool

UNCORRECTED_ERRORS = True

n_processes = 12

import sys

if len(sys.argv) != 2:
    print("")
    print("Usage {}  <database_file_name_without_sqlite_extention> ".format(sys.argv[0]))
    print("Example: {} Liars7 ".format(sys.argv[0]))
    print("If no parameter is supplied, the default input is Liars7.sqlite")
    print("")
    input_file = 'Liars7.sqlite'
else:
    input_file = sys.argv[1]

if input_file.find('.sqlite') < 0:
    print("The file name must end in .sqlite")
    sys.exit(-1)

input_file = input_file[:input_file.find('.sqlite')]

input_file_name = input_file + '.sqlite'
input_file_name_w = input_file + '_w.sqlite'
input_file_name_clean = input_file + '_clean_tr20200618.sqlite'

#import timing # doesn't seem to work in python 3

import time

from tqdm import tqdm

from nltk.corpus import wordnet as wn
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag.mapping import tagset_mapping, map_tag

from nltk.stem import WordNetLemmatizer
wnl = WordNetLemmatizer()

from sacremoses import MosesDetokenizer
MD = MosesDetokenizer(lang='en')
# from mosestokenizer import MosesDetokenizer
# MD = MosesDetokenizer()

import re
import enchant
from enchant.checker import SpellChecker

import sqlite3
import shutil

def cleaning_POS(text, pattern, dry=False):
    ''' This function performs the basic cleaning of the text. It consists of a
    block to remove any characters apart from words and punctuation. And
    another block to correct spelling mistakes. '''
    if dry:
        return text, 0, 0
    # Remove all non-letter characters using regular expressions
    p = pattern
    text_re = p.sub(' ', text)

    sentences = sent_tokenize(text_re)
    sentences_truecase = sentences.copy()
    k = 0
    for i in range(len(sentences)):
        if sentences[i].isupper():
            k = k + 1
            # print(sentence)
            sentence = sentences[i]
            sentences_truecase[i] = truecaser_Gordeli(sentence)
        else: continue
    if k > 0:
        text_tr = MD.detokenize(sentences_truecase, return_str=True)
        # print(text_tr)
        if "ca n't" in text_tr:
            text_tr = text_tr.replace("ca n't", "can't")
    else: text_tr = text_re



    # The following block of code fixes spelling mistakes.
    d = enchant.Dict("en_US")

    chkr = SpellChecker("en_US",text_tr)
    error_count = 0
    not_corrected = 0
    for err in chkr:
        if d.suggest(chkr.word)==[]:
            not_corrected = not_corrected + 1
        else:
            if (chkr.word).lower() == 'excersises':
                err.replace('exercises')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'excersizes':
                err.replace('exercises')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'exersizes':
                err.replace('exercises')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'vid': # was changing it to 'div'
                err.replace('video')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'definatley':
                err.replace('definitely')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'layed':
                err.replace('laid')
                error_count = error_count + 1
            elif (chkr.word).lower() == "kind've":
                err.replace('kind of')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'thw':
                err.replace('the')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'im':
                err.replace("I'm")
                error_count = error_count + 1
            elif (chkr.word).lower() == "wan't":
                err.replace("wasn't")
                error_count = error_count + 1
            elif (chkr.word).lower() == 'wasnt':
                err.replace("wasn't")
                error_count = error_count + 1
            elif (chkr.word).lower() == 'isnt':
                err.replace("isn't")
                error_count = error_count + 1
            elif (chkr.word).lower() == 'didnt':
                err.replace("didn't")
                error_count = error_count + 1
            elif (chkr.word).lower() == 'doesnt':
                err.replace("doesn't")
                error_count = error_count + 1
            elif (chkr.word).lower() == 'dont':
                err.replace("don't")
                error_count = error_count + 1
            elif (chkr.word).lower() == "din't":
                err.replace("didn't")
                error_count = error_count + 1
            elif (chkr.word).lower() == 'arent':
                err.replace("aren't")
                error_count = error_count + 1
            elif (chkr.word).lower() == 'havent':
                err.replace("haven't")
                error_count = error_count + 1
            elif (chkr.word).lower() == 'youre':
                err.replace('you are')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'outta':
                err.replace('out of')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'alot':
                err.replace('a lot')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'bennifit':
                err.replace('benefit')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'consintrate':
                err.replace('concentrate')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'overral':
                err.replace('overall')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'sholders':
                err.replace('shoulders')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'rotaing':
                err.replace('rotating')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'repor': # auto fixes to 'roper'
                err.replace('rapport')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'behing':
                err.replace('behind')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'suprise':
                err.replace('surprise')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'uncomfortabilty':
                err.replace('discomfort')
            elif (chkr.word).lower() == 'relxation':
                err.replace('relaxation')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'convinent':
                err.replace('convenient')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'slideshow':
                err.replace('slide show')
            elif (chkr.word).lower() == 'underarmour':
                err.replace('Under Armour')
            elif (chkr.word).lower() == 'fitlab':
                err.replace('FitLab')
            elif (chkr.word).lower() == 'yur':
                err.replace('your')
                error_count = error_count + 1
            elif (chkr.word).lower() == 'dialogue': # was replacing it by 'dialogged'
                continue
            elif (chkr.word).lower() == 'internet': # was replacing it by 'INTERNET'
                continue
            elif (chkr.word).lower() == 'gameplay': # was splitting it into 'game play'
                continue
            elif (chkr.word).lower() == 'smartphone': # was splitting it into 'smart phone'
                continue
            elif (chkr.word).lower() == 'meds': # was replacing by 'eds'
                continue
            elif (chkr.word).lower() == 'mins': # was replacing it to 'ins'
                continue
                # err.replace('minutes')
            elif (chkr.word).lower() == 'ipad':
                err.replace('iPad')
            elif (chkr.word).lower() == 'youtube':
                err.replace('Youtube')
            elif (chkr.word).lower() == 'peloton':
                err.replace('Peloton')
            elif (chkr.word).lower() == 'iphone':
                err.replace('iPhone')
            elif (chkr.word).lower() == 'ios':
                err.replace('iOS')
            elif (chkr.word).lower() == 'macbook':
                err.replace('MacBook')
            elif (chkr.word).lower() == 'nike':
                err.replace('Nike')
            elif (chkr.word).lower() == 'powerpoint':
                err.replace('PowerPoint')
            elif (chkr.word).lower() == 'ahhh':
                continue
            elif (chkr.word).lower() == 'apps':
                continue
            elif (chkr.word).lower() == "app's":
                continue
            elif (chkr.word).lower() == 'facebook':
                continue
            elif (chkr.word).lower() == 'snapchat':
                continue
            elif (chkr.word).lower() == 'instagram':
                continue
            elif (chkr.word).lower() == 'microtransaction':
                continue
            elif (chkr.word).lower() == 'online':
                continue
            elif (chkr.word).lower() == 'vroom':
                continue
            elif (chkr.word).lower()[-5:] == 'esque':
                continue
            elif (chkr.word).lower() != 'app':
                err.replace(d.suggest(chkr.word)[0])
                error_count = error_count + 1
    text_cleaned = chkr.get_text() # This returns the corrected string.
    # de-stressing (DE-Stressing), preschool (per-school)
    text_cleaned1  = text_cleaned.replace('per-school', 'preschool')
    text_cleaned2  = text_cleaned1.replace('DE-stress', 'de-stress')
    text_cleaned3  = text_cleaned2.replace('new York times', 'New York Times')
    text_cleaned4  = text_cleaned3.replace('my fitness pal', 'MyFitnessPal')
    text_cleaned5  = text_cleaned4.replace('DE-compress', 'de-compress')
    text_cleaned6  = text_cleaned5.replace('under Armour', 'Under Armour')
    text_cleaned7  = text_cleaned6.replace('wont', "won't")
    text_cleaned8  = text_cleaned7.replace('florescent', 'fluorescent')
    text_cleaned9  = text_cleaned8.replace('hep', 'help')
    text_cleaned10 = text_cleaned9.replace('power point', 'PowerPoint')
    text_cleaned11 = text_cleaned10.replace('theres', "there's")
    text_cleaned12 = text_cleaned11.replace('fine tuning', 'fine-tuning')
    text_cleaned13 = text_cleaned12.replace(' built in ', ' built-in ')
    text_cleaned14 = text_cleaned13.replace('no nonsense', 'no-nonsense')
    text_cleaned15 = text_cleaned14.replace('five year old', 'five-year-old')
    text_cleaned16 = text_cleaned15.replace('year old', '-year-old')
    text_cleaned17 = text_cleaned16.replace(' et ', ' get ')
    text_cleaned18 = text_cleaned17.replace('two minute', 'two-minute')
    text_cleaned19 = text_cleaned18.replace(' i ll ', " I'll ")
    text_cleaned20 = text_cleaned19.replace(' woks ', ' works ')
    text_cleaned21 = text_cleaned20.replace(' i ', " I ")
    text_cleaned22 = text_cleaned21.replace('over extending', 'overextending')
    text_cleaned23 = text_cleaned22.replace('child like', 'childlike')
    text_cleaned24 = text_cleaned23.replace('work day', 'workday')
    text_cleaned25 = text_cleaned24.replace('I actually thing', 'I actually think')
    text_cleaned26 = text_cleaned25.replace('time consuming', 'time-consuming')
    text_cleaned27 = text_cleaned26.replace('anytime of the', 'any time of the')
    text_cleaned28 = text_cleaned27.replace('you neck', 'your neck')
    text_cleaned29 = text_cleaned28.replace(' a re ', ' are ')
    text_cleaned30 = text_cleaned29.replace('.i ', '. I ')
    text_cleaned31 = text_cleaned30.replace('.I ', '. I ')
    text_cleaned32 = text_cleaned31.replace('clear my had', 'clear my head')
    text_cleaned33 = text_cleaned32.replace("let's you", 'lets you')
    text_cleaned34 = text_cleaned33.replace('preforming', 'performing')
    text_cleaned35 = text_cleaned34.replace('in depth', 'in-depth')
    text_cleaned36 = text_cleaned35.replace('user friendly', 'user-friendly')
    text_cleaned37 = text_cleaned36.replace('everyday', 'every day')
    text_cleaned38 = text_cleaned37.replace('every day life', 'everyday life')
    text_cleaned39 = text_cleaned38.replace('every day routine', 'everyday routine')
    text_cleaned40 = text_cleaned39.replace('pain relieving', 'pain-relieving')
    text_cleaned41 = text_cleaned40.replace('life saving', 'life-saving')
    text_cleaned42 = text_cleaned41.replace('I as able', 'I was able')
    text_cleaned43 = text_cleaned42.replace('feel the affects', 'feel the effects')
    text_cleaned44 = text_cleaned43.replace('otter people', 'other people')
    text_cleaned45 = text_cleaned44.replace('whole heartedly', 'wholeheartedly')
    text_cleaned46 = text_cleaned45.replace('brain power', 'brainpower')
    text_cleaned47 = text_cleaned46.replace('mind blowing', 'mind-blowing')
    text_cleaned48 = text_cleaned47.replace('Any one can', 'Anyone can')
    text_cleaned49 = text_cleaned48.replace('money saving', 'money-saving')
    text_cleaned50 = text_cleaned49.replace(' and and ', ' and ')
    text_cleaned51 = text_cleaned50.replace('much needed', 'much-needed')
    text_cleaned52 = text_cleaned51.replace("you're neck", 'your neck')
    text_cleaned53 = text_cleaned52.replace(' me neck', ' my neck')
    text_cleaned54 = text_cleaned53.replace('something differ ', 'something different ')
    text_cleaned55 = text_cleaned54.replace(' to to ', ' to ')
    text_cleaned56 = text_cleaned55.replace(' be less stresses ', ' be less stressed ')
    text_cleaned57 = text_cleaned56.replace(' thats what ', " that's what ")
    text_cleaned58 = text_cleaned57.replace(' thats it', " that's it")
    text_cleaned59 = text_cleaned58.replace('life style', 'lifestyle')
    text_cleaned60 = text_cleaned59.replace(' your stuck ', " you're stuck ")
    text_cleaned61 = text_cleaned60.replace(' Ill ', " I'll ")
    text_cleaned62 = text_cleaned61.replace(' well trained', ' well-trained')
    text_cleaned63 = text_cleaned62.replace('becoming more focus,', 'becoming more focused,')
    text_cleaned64 = text_cleaned63.replace('life changing', 'life-changing')
    text_cleaned65 = text_cleaned64.replace('ther then that', 'ther than that')
    text_cleaned66 = text_cleaned65.replace(' stated using', ' started using')
    text_cleaned67 = text_cleaned66.replace(' may benefits', ' many benefits')
    text_cleaned68 = text_cleaned67.replace(' must have', ' must-have')
    text_cleaned69 = text_cleaned68.replace('Cost effective', 'Cost-effective')
    text_cleaned70 = text_cleaned69.replace('cost effective', 'cost-effective')
    text_cleaned71 = text_cleaned70.replace('really effects', 'really affects')
    text_cleaned72 = text_cleaned71.replace(' your doing', " you're doing")
    text_cleaned73 = text_cleaned72.replace('I cam across', 'I came across')
    text_cleaned74 = text_cleaned73.replace('through out the ', 'throughout the ')
    text_cleaned75 = text_cleaned74.replace(' a one trick ', ' a one-trick ')
    text_cleaned76 = text_cleaned75.replace('moving a round', 'moving around')
    text_cleaned77 = text_cleaned76.replace(' I now I ', ' I know I ')
    text_cleaned78 = text_cleaned77.replace('game changer', 'game-changer')
    text_cleaned79 = text_cleaned78.replace('mini break', 'mini-break')
    text_cleaned80 = text_cleaned79.replace(' a big different', ' a big difference')
    text_cleaned81 = text_cleaned80.replace('working form home', 'working from home')
    text_cleaned82 = text_cleaned81.replace(' life saver', ' lifesaver')
    text_cleaned83 = text_cleaned82.replace(' effected ', ' affected ')
    text_cleaned84 = text_cleaned83.replace(' neck neck ', ' neck ')
    text_cleaned85 = text_cleaned84.replace(' for awhile ', ' for a while ')
    text_cleaned86 = text_cleaned85.replace(' work space ', ' workspace ')
    text_cleaned87 = text_cleaned86.replace(' my all day ', ' my all-day ')
    text_cleaned88 = text_cleaned87.replace(' really ease to ', ' really easy to ')
    text_cleaned89 = text_cleaned88.replace('  starts ', ' stars ')
    text_cleaned90 = text_cleaned89.replace(' anytime any where ', ' anytime anywhere ')
    text_cleaned91 = text_cleaned90.replace(' siting a he ', ' sitting at the ')
    text_cleaned92 = text_cleaned91.replace(' overtime my neck ', ' over time my neck ')
    text_cleaned93 = text_cleaned92.replace('I fee ', 'I feel ')
    text_cleaned94 = text_cleaned93.replace(' full time desk', ' full-time desk')
    text_cleaned95 = text_cleaned94.replace(' multi tasking ', ' multi-tasking ')
    text_cleaned96 = text_cleaned95.replace(' piece of mind ', ' peace of mind ')
    text_cleaned97 = text_cleaned96.replace(' no where ', ' nowhere ')
    text_cleaned98 = text_cleaned97.replace(' make it though the ', ' make it through the ')
    text_cleaned99 = text_cleaned98.replace(' a god-send ', ' a godsend ')
    text_cleaned100 = text_cleaned99.replace(' be overall more product', ' be overall more productive')
    text_cleaned101 = text_cleaned100.replace(' every one out ', ' everyone out ')
    text_cleaned102 = text_cleaned101.replace(' by lunch time ', ' by lunchtime ')
    text_cleaned103 = text_cleaned102.replace('relive neck pain', 'relieve neck pain')
    text_cleaned104 = text_cleaned103.replace(' step my step', ' step by step')
    text_cleaned105 = text_cleaned104.replace('cringe worthy', 'cringe-worthy')
    text_cleaned106 = text_cleaned105.replace('hyper mobile', 'hypermobile')
    text_cleaned107 = text_cleaned106.replace(' built in.', ' built-in.')
    text_cleaned108 = text_cleaned107.replace(' to  to ', ' to ')
    text_cleaned109 = text_cleaned108.replace(' heck stretching', ' neck stretching')
    text_cleaned110 = text_cleaned109.replace(' app-to-date ', ' app to date ')
    text_cleaned111 = text_cleaned110.replace(' AP,', ' app, ')
    text_cleaned112 = text_cleaned111.replace('INTERNET', 'internet')
    text_cleaned113 = text_cleaned112.replace(' Leary ', ' leery ')
    text_cleaned114 = text_cleaned113.replace(' UN-challenging', ' un-challenging')

    # sentences = sent_tokenize(text_cleaned111)
    # sentences_truecase = sentences.copy() # sentences_truecase = sentences[:]
    # for i in range(len(sentences)):
    #     # for sentence in sentences:
    #     sentence = sentences[i]
    #     sentence = truecaser_Gordeli(sentence)
    #     sentences_truecase[i] = sentence
    # text_truecase = MD.detokenize(sentences_truecase, return_str=True)

    # return text_truecase, error_count, not_corrected
    return text_cleaned114, error_count, not_corrected

def truecaser_Gordeli(sentence):
    tokens = word_tokenize(sentence)
    newtokens = tokens.copy()
    # newtokens = tokens[:] # Note: for python 3.3 and higher, use list.copy() method instead: tokens.copy()
    # print tokens
    # how to check if the first and only first letter of the word is a capital
    if len(tokens) > 1: # makes sure the sentence has at least 2 words to be modified
        for i in range(len(tokens)):
            word = tokens[i] # the original word
            # newword = word
            # print word, 'word' # this line prints out the original word
            if i < 1: # sets previous word to all uppercase letters for the first word in the sentence
                previous_word = 'FIRSTWORD'
            else: # sets previous word to the original previous word
                previous_word = tokens[i-1]
            # print previous_word, 'previous word' # this line prints out the original previous word
            if i < len(tokens) - 1: # sets the next word to the original next word unless the current word is the last one
                next_word = tokens[i+1]
            else: # sets the next word to an all-uppercase letters word for the last word in the sentence
                next_word = 'LASTWORD'
            # print next_word, 'next word' # prints out the next word
            if len(word) > 1 and i > 0: # for non single-letter words except for the first word in the sentence
                if (word.isupper() and previous_word.isupper() and (next_word.isupper() or (next_word == '.') or (next_word == ',') or (next_word == '!'))): # ensures abbreviations are not affected # word[0].isupper() and word[1].isupper():
                    newtokens[i] = word.lower()
                    # print newtokens[i], 'after if'
            elif len(word) > 1 and i == 0:
                if (word.isupper() and previous_word.isupper() and (next_word.isupper() or (next_word == '.') or (next_word == ',') or (next_word == '!'))): # ensures abbreviations are not affected # word[0].isupper() and word[1].isupper():
                    newtokens[i] = word.capitalize()
                    # print tokens[i], 'first token after the first loop iteration should not change!!!'
            elif len(word) == 1 and i == 0: # deals with single letter words at the beginning of the sentence
                newtokens[i] = word.capitalize()
            else: # deals with single letter words. preserving the capitalization of all letters but 'i' or 'a'
                if word.lower() == 'a': # lowercases all single letter 'a' words
                    newtokens[i] = word.lower()
                elif word.lower() == 'i':
                    newtokens[i] = word.capitalize() # capitalizes words 'i'
                else: newtokens[i] = word.upper()
                # print newtokens[i], 'after else else'
            # print tokens, i
    sentence = MD.detokenize(newtokens, return_str=True)
    # print tokens, newtokens
    return sentence

# def process_text(text, pattern):
#     # text_cleaned = cleaning_POS(text, pattern, dry=False)
#     # sentences = sent_tokenize(text_cleaned)
#     # sentences_truecase = sentences.copy()
#     # for i in range(len(sentences)):
#     # # for sentence in sentences:
#     #     sentence = sentences[i]
#     #     sentence = truecaser_Gordeli(sentence)
#     #     sentences_truecase[i] = sentence
#     # text_truecase = MD.detokenize(sentences_truecase, return_str=True)
#     # return text_truecase
#
#     sentences = sent_tokenize(text)
#     sentences_truecase = sentences.copy() # sentences_truecase = sentences[:]
#     for i in range(len(sentences)):
#     # for sentence in sentences:
#         sentence = sentences[i]
#         sentence = truecaser_Gordeli(sentence)
#         sentences_truecase[i] = sentence
#     text_truecase = MD.detokenize(sentences_truecase, return_str=True)
#     [text_cleaned, error_count, not_corrected] = cleaning_POS(text_truecase, pattern, dry=False)
#     return text_cleaned, error_count, not_corrected


def get_n_rows(input_file_name, sqlstr):
    conn = sqlite3.connect(input_file_name)
    cur = conn.cursor()
    rows = [row for row in cur.execute(sqlstr)]
    cur.close()
    conn.close()
    return len(rows)

conn = sqlite3.connect(input_file_name)
cur = conn.cursor()

shutil.copyfile(input_file_name, input_file_name_w)

conn_w = sqlite3.connect(input_file_name_w)
cur_w = conn_w.cursor()

# Next we create an extra column in the Reviews table to have it edited later with the cleaned texts
# We do that only if the column does not exist yet
try:
    cur_w.execute('''ALTER TABLE Reviews ADD Review_cleaned TEXT''')
except:
    print("The column 'Review_cleaned' exists already")
    pass # handle the error

try:
    cur_w.execute('''ALTER TABLE Reviews ADD Review_errors_corrected INTEGER NOT NULL DEFAULT 0''')
except:
    print("The column 'Review_errors_corrected' exists already")
    pass # handle the error


if UNCORRECTED_ERRORS:
    try:
        cur_w.execute('''ALTER TABLE Reviews ADD Review_errors_not_corrected INTEGER NOT NULL DEFAULT 0''')
    except:
        print("The column 'Review_errors_not_corrected' exists already")
        pass # handle the error




# Here we loop through the table, and correct each review, then put it back into the database (in a new column)

sqlstr = 'SELECT Review FROM Reviews'

n_rows = get_n_rows(input_file_name,sqlstr)
print('Number of rows {}'.format(n_rows))

p = re.compile("[^0-9a-zA-Z\s\.\!\?',-]|(?<=[.,])(?=[^\s])") # (?<=[.,])(?=[^\s])
# matches the '.' or ',' which is followed by any character but whitespace
# added 0-9 on April 22, 2020

rows = [row for row in cur.execute('SELECT id, Review FROM Reviews')]



def get_process_row(p, dry=False):
    # return (lambda row : (row[0], process_text(row[1], p)))
    return (lambda row : (row[0], cleaning_POS(row[1], p, dry=dry)))


process_row = get_process_row(p,dry=False)

t0 = time.time()

print('Start cleaning with {} parallel processes'.format(n_processes))

with Pool(processes=n_processes) as pool:
    cleaned_rows = list( tqdm(pool.imap(process_row, rows), total = n_rows))

t1 = time.time()
print('Finished cleaning in {:4.4f} '.format(t1-t0))



error_count_total = 0
not_corrected_total = 0

print('Start dumping database_w')

for ires in tqdm(cleaned_rows, total=len(cleaned_rows)):
    error_count_total += ires[1][1]
    not_corrected_total += ires[1][2]
    if UNCORRECTED_ERRORS:
        cur_w.execute('UPDATE Reviews SET Review_cleaned = ?, Review_errors_corrected = ?,  Review_errors_not_corrected = ? WHERE id = ?',
                  (ires[1][0], ires[1][1], ires[1][2],  ires[0]))
    else:
        cur_w.execute('UPDATE Reviews SET Review_cleaned = ?, Review_errors_corrected = ?  WHERE id = ?',
                  (ires[1][0], ires[1][1],  ires[0]))


print('Finished dumping database_w')

print('finished loop')

conn_w.commit()
cur_w.close()
conn_w.close()
cur.close()
conn.close()
shutil.copyfile(input_file_name_w, input_file_name_clean)
print('Number of errors corrected: ', error_count_total)
print('Number of errors which were not corrected: ', not_corrected_total)
