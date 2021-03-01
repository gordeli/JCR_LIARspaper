# This code counts different POS per review and loads those values into the
# corresponding columns. In addition, it counts the total number of words, the
# noun-length of each review, which only incudes nouns found in WordNet, verb-length

# import timing
import numpy as np
np.seterr(all='raise')
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

wnl = WordNetLemmatizer()

# Functions to generate wordfroms and noun-lemmas they convert to. from wordforms.py
def wordnet_word(word):
    from nltk.corpus import wordnet as wn
    if not wn.synsets(word):
        return False
    else:
        return True

def wordnet_tag(word):
    from nltk.corpus import wordnet as wn
    noun_synsets = wn.synsets(word, pos='n')
    verb_synsets = wn.synsets(word, pos='v')
    adj_synsets = wn.synsets(word, pos='a')
    adv_synsets = wn.synsets(word, pos='r')
    if noun_synsets != [] and verb_synsets == [] and adj_synsets == [] and adv_synsets == []:
        tag = 'NN'
    elif noun_synsets == [] and verb_synsets != [] and adj_synsets == [] and adv_synsets == []:
        tag = 'VB'
    elif noun_synsets == [] and verb_synsets == [] and adj_synsets != [] and adv_synsets == []:
        tag = 'JJ'
    elif noun_synsets == [] and verb_synsets == [] and adj_synsets == [] and adv_synsets != []:
        tag = 'RB'
    else: tag = None
    return tag

def hyphenated_word(word):
    if word[0] != '-' and '-' in word:
        return True
    else:
        return False

def wordent_hyphenation(words):
    # This function takes a list of words and deals with hyphenated words in
    # this list, checking if each of the single words is in WordNet
    i = 0
    while i < len(words): #word in words:
        try: word = words[i]
        except: print(i, words)
        if hyphenated_word(word):
            if wordnet_word(word):
                i = i + 1
            elif wordnet_word(word.replace('-', '')):
                words[i] = word.replace('-', '')
                i = i + 1
            else: # replace word by wordbeforehyphen, wordafterhyphen
                hyphen_words = word.split('-')
                word1 = hyphen_words[0]
                word2 = hyphen_words[1]
                # print(word, word1, word2)
                words[i] = word1
                words.insert(i+1, word2)
                if len(hyphen_words) > 2:
                    for k in range(2,len(hyphen_words)):
                        words.insert(i+k, hyphen_words[k])
                i = i + len(hyphen_words)
        i = i + 1
    # Need to remove the instances of '' from the list which could appear
    a = 0
    while a < 1:
        try:
            words.remove('')
        except:
            a = 1
    return words

def derivational_conversion(word, from_pos, to_pos):
    synsets = wn.synsets(word, pos=from_pos)

    # Word not found
    if not synsets:
        return []

    # Get all lemmas of the word (consider 'a'and 's' equivalent)
    lemmas = []
    for s in synsets:
        for l in s.lemmas():
            if s.name().split('.')[1] == from_pos or from_pos in ('a', 's') and s.name().split('.')[1] in ('a', 's'):
                lemmas += [l]

    # Get related forms
    derivationally_related_forms = [(l, l.derivationally_related_forms()) for l in lemmas]

    # filter only the desired pos (consider 'a' and 's' equivalent)
    related_noun_lemmas = []

    for drf in derivationally_related_forms:
        for l in drf[1]:
            if l.synset().name().split('.')[1] == to_pos or to_pos in ('a', 's') and l.synset().name().split('.')[1] in ('a', 's'):
                related_noun_lemmas += [l]

    # Extract the words from the lemmas
    words = [l.name() for l in related_noun_lemmas]
    # print(words)
    len_words = len(words)

    # Build the result in the form of a list containing tuples (word, probability)
    used = set()
    unique_list = [x for x in words if x not in used and (used.add(x) or True)]
    # unique_list = set(words) # added this line for testing and edited it in the follwoing line  as well
    # print(unique_list) # to check if the order stays the same
    result = [(w, float(words.count(w)) / len_words) for w in unique_list]
    result.sort(key=lambda w:-w[1]) # result = sorted(result, key=lambda w:-w[1])# Changed the original to keep the order intact over re-runs of the the code. The original version: result.sort(key=lambda w:-w[1])

    return result

def nounalike_conversion(word, from_pos):
    """ This function checks if there is an identically spelled noun in WordNet"""
    synsets = wn.synsets(word, from_pos)

    # Word not found
    if not synsets:
        return []

    # for s in synsets:

    syn_1 = synsets[0]
    word_1 = syn_1.name().split('.')[0]
    noun_synset_1 = wn.synsets(word_1, pos='n')
    if noun_synset_1 != []:
        result = [(word_1, 1)]
    else:
        return []

    return result

def attribute_conversion(word, from_pos):
    """ This function converts a word to a noun using the attribute method from WordNet"""
# The attribute method exists for adjectives I think
    synsets = wn.synsets(word, from_pos)

    # Word not found
    if not synsets:
        return []

    result =[]
    attribute_list = []
    for s in synsets:
        # word_g = s.name().split('.')[0]
        attrib_s = s.attributes()
        if len(attrib_s) > 1:
            print('There is more than 1 attribute: ', s, attrib_s)
        attribute_list += attrib_s
    for a in attribute_list:
        word_a = a.name().split('.')[0]
        noun_a = wn.synsets(word_a, pos='n')
        if noun_a != []:
            result = [(word_a, 1)]
            break
        else: continue

    return result

def convert_similartos(word, from_pos):
    """ Transforms words uing synomyms (similar_tos) method from WordNet"""
    synsets = wn.synsets(word, from_pos)

    # Word not found
    if not synsets:
        return []

    synsets_similar = []
    for s in synsets:
        similar_s = s.similar_tos() # gives a list of synsets similar ot this one
        synsets_similar += similar_s
    # if not synsets_similar:
    #     result = []

    # Get all lemmas of the word (consider 'a'and 's' equivalent)
    lemmas = []
    for s in synsets_similar:
        for l in s.lemmas():
            if s.name().split('.')[1] == from_pos or from_pos in ('a', 's') and s.name().split('.')[1] in ('a', 's'):
                lemmas += [l]

    # Get related forms
    derivationally_related_forms = [(l, l.derivationally_related_forms()) for l in lemmas]

    # filter only the desired pos (consider 'a' and 's' equivalent)
    related_noun_lemmas = []

    for drf in derivationally_related_forms:
        for l in drf[1]:
            if l.synset().name().split('.')[1] == 'n':
                related_noun_lemmas += [l]

    # Extract the words from the lemmas
    words = [l.name() for l in related_noun_lemmas]
    # print(words)
    len_words = len(words)

    # Build the result in the form of a list containing tuples (word, probability)
    used = set()
    unique_list = [x for x in words if x not in used and (used.add(x) or True)]
    # unique_list = set(words) # added this line for testing and edited it in the follwoing line  as well
    # print(unique_list) # to check if the order stays the same
    result = [(w, float(words.count(w)) / len_words) for w in unique_list]
    result.sort(key=lambda w:-w[1]) # result = sorted(result, key=lambda w:-w[1])# Changed the original to keep the order intact over re-runs of the the code. The original version: result.sort(key=lambda w:-w[1])

    return result # the result is a list of tuples with (word, word-frequency) as a tuple

def convert_pertainym(word):
    """ Transforms adverbs into adjectives"""
    synsets = wn.synsets(word, 'r')

    # Word not found
    if not synsets:
        return []

    # Get all lemmas of the word (consider 'a'and 's' equivalent)
    lemmas = []
    for s in synsets:
        for l in s.lemmas():
            lemmas += [l]

    # Get pertainyms
    pertainyms = [(l, l.pertainyms()) for l in lemmas]

    # filter only the desired pos (consider 'a' and 's' equivalent)
    related_adj_lemmas = []

    for prt in pertainyms:
        for l in prt[1]:
            if l.synset().name().split('.')[1] in ['a', 's']:
                related_adj_lemmas += [l]
            else:
                print('Pertainym for the word is not an adjectif: ', word, l.synset().name().split('.')[1])

    # Extract the words from the lemmas
    words = [l.name() for l in related_adj_lemmas]
    # print(words)
    len_words = len(words)

    # Build the result in the form of a list containing tuples (word, probability)
    used = set()
    unique_list = [x for x in words if x not in used and (used.add(x) or True)]
    # unique_list = set(words) # added this line for testing and edited it in the follwoing line  as well
    # print(unique_list) # to check if the order stays the same
    result = [(w, float(words.count(w)) / len_words) for w in unique_list]
    result.sort(key=lambda w:-w[1]) # result = sorted(result, key=lambda w:-w[1])# Changed the original to keep the order intact over re-runs of the the code. The original version: result.sort(key=lambda w:-w[1])

    return result # the result is a list of tuples with (word, word-frequency) as a tuple

def convert_to_noun(word, from_pos):
    """ Transform words given from/to POS tags """

    if word.lower() in ['most', 'more'] and from_pos == 'a':
        word = 'many'

    synsets = wn.synsets(word, pos=from_pos)

    # Word not found
    if not synsets:
        return []

    result = derivational_conversion(word, from_pos, 'n')

    if len(result) == 0:
        result = attribute_conversion(word, from_pos)

    if len(result) == 0 and word[-2:].lower() == 'ed' and from_pos != 'v':
        result = derivational_conversion(word, 'v', 'n')

    if len(result) == 0:
        result = convert_similartos(word, from_pos)

    if len(result) == 0 and from_pos == 'r': # working with pertainyms
        adj_words = convert_pertainym(word)
        for adj in adj_words:
            word_a = adj[0]
            # print(word_a)
            result = derivational_conversion(word_a, 'a', 'n')
            if len(result) == 0:
                result = attribute_conversion(word_a, 'a')
            else: break
            if len(result) == 0 and word_a[-2:].lower() == 'ed' and from_pos != 'v':
                result = derivational_conversion(word_a, 'v', 'n')
            else: break
            if len(result) == 0:
                result = convert_similartos(word_a, 'a')
            else: break

    if len(result) == 0:
        result = nounalike_conversion(word, from_pos)

    # return all the possibilities sorted by probability
    return result

def nounify(word, tag):
    noun_list = convert_to_noun(word, tag)
    if noun_list != []:
        noun = noun_list[0][0]
    else:
        # print('Not found in derivationally related forms: ', word, tag)
        if word == 'visuals': noun = 'picture'
        elif word.lower() == 'gameplay': noun = 'game'
        elif word.lower() == 'personalization': noun = 'individualization'
        elif word.lower() == 'coworker': noun = 'co-worker'
        elif word.lower() == 'coworkers': noun = 'co-workers'
        elif word.lower() == 'sans': noun = 'font'
        elif word.lower() == 'microsoft': noun = 'corporation'
        elif word.lower() == 'ios': noun = 'software'
        elif word.lower() == 'powerpoint': noun = 'programme'
        elif word.lower() == 'youtube': noun = 'website'
        elif word.lower() == 'hodge': noun = 'surname'
        elif tag == 'n' and 'thing' in word.lower():
            noun = 'thing'
        elif tag[0] == 'n' and word.lower() in ['anyone', 'everyone', 'anybody', 'everybody']:
            noun = 'person'
        elif tag == 'a':
            noun_list = convert_to_noun(word, 'v')
            if noun_list != []:
                noun = noun_list[0][0]
            else: noun = None
        else: noun = None

    return noun

def wordformtion(text):
    # this function generates 2 dictionaries: a dictionary of wordforms with POS and count
    # and a dictionary of corrsponding noun-lemmas with counts
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    import numpy as np
    from nltk.stem import PorterStemmer
    porter = PorterStemmer()
    sentences = sent_tokenize(text)
    wordforms = dict() # Initializes an empty dictionary where we will keep track of all nouns in the whole corpus of reviews and how many times their occurence values
    word_wordforms = dict() # The wordforms whithout punctuation, CC, DT, EX, IN

    for sentence in sentences:
        words = word_tokenize(sentence)
        indexes_todelete = [] # A list of indicies of the wrds to be deleted (artifacts from word_tokenization)
        for i in range(1, len(words)):
            word = words[i]
            word.strip() # Remove the whitespaces from the beginning and the end of the word added on 20210127
            words[i] = word
            if words[i-1][0] == "'" and words[i] == "'":
                # print('A word originally in single quatation marks, before the first quatation mark removed: ', words[i-1])
                words[i-1] = words[i-1][1:]
                indexes_todelete = indexes_todelete + [i]
        words = np.delete(words, indexes_todelete).tolist()
        words = list(filter(None, words)) #added on 20210127 to remove empty words
        for i in range(1, len(words)):
            word = words[i]
            try:
                if word[0] == "'" and word[-1] == "'" and word not in ["'", "''"]:
                    word = word[1:-2] # Added and word != "'" on 20210126
                    word.strip()
                    words[i] = word
                elif word[0] == "'" and word != "'":
                    word = word[1:]
                    word.strip()
                    words[i] = word
                elif word[0] == '-' and word != '-':
                    word = word[1:]
                    word.strip()
                    words[i] = word
                elif word in ["'", "''"]: words[i] = None
                elif word != None:
                    word.strip()
                    words[i] = word
            except:
                word.strip()
                words[i] = word
                if len(word) > 0:
                    print('The code block that removes the apostrophe artifacts break on the word: ', word)
                continue
            # if len(words[i]) == 0:
            #     print(word, sentence)
        words = list(filter(None, words))

        # Here we need to insert treatement of hyphenated words
        words = wordent_hyphenation(words)

        try:
            nltk_tagged = nltk.pos_tag(words)
        except:
            print('NLTK-tagging fails on the following sentence: ', words)
            continue

        a = 0 # setting the marker for the preceeding word being a verb
        for word, tag in nltk_tagged:
# The next piece deals with corrections to POS tagging
            if word.lower() in ['sans', 'microsoft', 'powerpoint', 'youtube', 'ios']:
                tag = 'NNP'
            elif word.lower() in ['app', 'pt', 'neck', 'bottom', 'font', 'kind', 'stiff', 'collar']:
                tag = 'NN'
            elif word.lower() in ['apps', 'thumbs', 'drawbacks']:
                tag = 'NNS'
            elif word.lower() in ['wow', 'aw']:
                tag = 'UH'
            elif tag == 'NNP' and word.lower() in ['boy']:
                tag = 'UH'
            elif word.lower() in ['weird', 'overall', 'great', 'ok', 'stupid', 'okay', 'perfect', 'ok.', 'full']:
                tag = 'JJ'
            elif tag[:2] == 'VB' and word.lower() in ['potential', 'routine', 'ping']:
                tag = 'NN'
            elif tag[:2] == 'VB' and word.lower() in ['deep', 'straight', 'simple', 'stiff', 'groundbreaking', 'good', 'handy', 'specific', 'daily', 'glad', 'sore', 'quick', 'sobering', 'fun']:
                tag = 'JJ'
            elif tag[:2] == 'VB' and word.lower() in ['more', 'sideways']:
                tag = 'RB'
            elif tag[:2] == 'JJ' and word.lower() in ['web']:
                tag = 'NN'
            elif tag[:2] == 'JJ' and word.lower() in ['aside']:
                tag = 'RB'
            elif tag[:2] == 'RB' and word.lower() in ['silly', 'friendly', 'sore', 'nice']:
                tag = 'JJ'
            elif tag[:2] == 'RB' and word.lower() in ['neck', 'strain', 'winter', 'pain', 'flows']:
                tag = 'NN'
            elif tag[:2] == 'NN' and word.lower() in ['begin', 'do', 'clasp', 'say']:
                tag = 'VB'
            elif tag == 'NNS' and word.lower() in ['uses', 'teaches', 'eases']: # or word.lower() == 'coherent' or word.lower() == 'helpful'):
                tag = 'VBZ'
            elif tag[0] == 'N' and word.lower() in ['saved', 'developed']: # or word.lower() == 'coherent' or word.lower() == 'helpful'):
                tag = 'VBD'
            elif tag[0] == 'N' and word.lower() in ['described']: # or word.lower() == 'coherent' or word.lower() == 'helpful'):
                tag = 'VBN'
            elif tag[0] == 'N' and word.lower() in ['buzzing', 'matching', 'crashing', 'staring']: # or word.lower() == 'coherent' or word.lower() == 'helpful'):
                tag = 'VBG'
            elif tag[0] == 'N' and word.lower() in ['soothing', 'condescending', 'entertaining', 'amazing', 'relaxing', 'challenging', 'interesting', 'confusing', 'damaging', 'nagging', 'changing', 'decent', 'easy', 'slow', 'relaxed', 'sure', 'goofy', 'quick']: # or word.lower() == 'coherent' or word.lower() == 'helpful'):
                tag = 'JJ'
            elif tag[0] == 'N' and word.lower() in ['quicker']: # or word.lower() == 'coherent' or word.lower() == 'helpful'):
                tag = 'JJR'
            elif tag[0] == 'N' and word.lower() in ['pretty', 'anytime', 'forth', 'first']: # or word.lower() == 'coherent' or word.lower() == 'helpful'):
                tag = 'RB'
            elif tag[0] == 'N' and word.lower() in ['towards', 'about']: # or word.lower() == 'coherent' or word.lower() == 'helpful'):
                tag = 'IN'
            elif tag[0] in ['N', 'V'] and word.lower() in ['ourselves', 'myself']: # or word.lower() == 'coherent' or word.lower() == 'helpful'):
                tag = 'PRP'
            elif tag[0] == 'N' and word.lower() in ['yours']: # or word.lower() == 'coherent' or word.lower() == 'helpful'):
                tag = 'PRP$'
            elif tag[0] == 'V' and word.lower() in ['everything']: # or word.lower() == 'coherent' or word.lower() == 'helpful'):
                tag = 'NN'
            elif tag[0] == 'V' and word.lower() in ['easy', 'tight']: # or word.lower() == 'coherent' or word.lower() == 'helpful'):
                tag = 'JJ'
            elif tag[0] == 'V' and word.lower() in ['that']: # or word.lower() == 'coherent' or word.lower() == 'helpful'):
                tag = 'PR'
            elif word.lower() == 'alright':
                tag = 'RB'
            elif tag[:2] != 'NN' and word.lower() in ['neck']:# , 'workday', 'workplace', 'desk']:
                tag = 'NN'
            elif len(word) > 2 and wordnet_tag(word) != None and (tag[:2] != wordnet_tag(word) or word == 'font') and (wordnet_tag(word) != 'NN' or 'font' in word): # and tag[0] in ['N', 'V', 'J', 'R'] I have removed the NN tagged words, as they often overlap with some strange words, abbreviations for pronouns or propositions which are not in wordnet. With the exclusion of the word font
                # print('Before tag replacement: ', word, tag)
                tag = wordnet_tag(word)
            elif len(word) > 2 and wordnet_tag(word) != None and (tag[:2] != wordnet_tag(word) or word.lower() == 'fun') and wordnet_tag(word) == 'NN' and word not in ['might']: # and tag[0] in ['N', 'V', 'J', 'R'] I have removed the NN tagged words, as they often overlap with some strange words, abbreviations for pronouns or propositions which are not in wordnet. With the exclusion of the word font
                if word.lower() not in ['why', 'its', 'who', 'may', 'yes', 'tho', 'while', 'otter', 'upside', 'genius', 'despite', 'sceptic', 'lifesaving']: # Note: removed the word 'fun' from the exclusion list
                    # print('Retagging as a noun. Before tag replacement: ', word, tag)
                    # print(sentence)
                    tag = wordnet_tag(word)

            if a >= 1 and tag[0] == 'V': # handling auxiliary verbs
                wordforms[(word_prev, tag_prev)] -= 1
                if wordforms[(word_prev, tag_prev)] < 0: # added on 20210127. Negative values do not make sence and lead to errors in calculating concreteness on verbs
                    # wordforms[(word_prev, tag_prev)] = 0
                    print("Error. The wordform count becomes negative: ", "For worform: ", word_prev, tag_prev, "On wordform: ", word, tag, "On sentence: ", sentence)

                wordforms[(word_prev, 'AU')] = wordforms.get((word_prev, 'AU'), 0) + 1
                a = 0 # reset the counter after tagging the AU verb, so that we do not count it again

            # if word.lower() == 'dr':
            #     print(sentence)
            if tag[0] == 'V' and word.lower() in ['am', "m", "'m", 'is', "s", "'s", 'are', "re", "'re", 'was', 'were', 'being', 'been', 'be', 'have', "ve", "'ve", 'has', 'had', 'd', "'d", 'do', 'does', 'did', 'will', 'll', "'ll", 'would', 'shall', 'should', 'may', 'might', 'must', 'can', 'could']:
                a += 1 # a marker to memorize that the word was a verb to handle auxiliary verbs
                if a > 3:
                    # print('More than 3 consecutive verbs detected in the following sentence: ', nltk_tagged)
                    a = 0
                    print("Sentence on which AU tagging breaks: more than 3 verbs in a row: ",sentence)
                tag_prev = tag
                word_prev = word.lower()
            elif a >= 1 and (tag[:2] == 'RB' or word.lower() in ['not' , "n't", 't', "'t"]):
                a += 1
                # if word.lower() in ["n't", 't', "'t"]:
                #     print("Sentence containing n't, t or 't'", nltk_tagged)
            else: a = 0

            wordforms[(word.lower(), tag)] = wordforms.get((word.lower(), tag), 0) + 1

    return wordforms

# Main code block
import sqlite3
import shutil # we use this library to create a copy of a file (in this case to duplicate the database
# so that we can loop over one instance while editing the other)
# Establish a SQLite connection to a database named 'Liars4.sqlite':
conn = sqlite3.connect('Liars7_unique20210129.sqlite') # The copy of the original database to use for iterating
# # Get the cursor, which is used to traverse the database, line by line
cur = conn.cursor()
# Then we duplicate thedatabase, so that one can loop and edit it at the same time
# and 'open' the other 'instance' of the same database
# shutil.copyfile('Liars7_depth.sqlite', 'Liars7_w.sqlite')
shutil.copyfile('Liars7_unique20210129.sqlite', 'Liars7_w.sqlite')
conn_w = sqlite3.connect('Liars7_w.sqlite') # The database to be updated
cur_w = conn_w.cursor()

# Next we create an extra column in the Reviews table to have it edited later with noun-length of each review.
# We do that only if the column does not exist yet
# try:
#     cur_w.execute('''ALTER TABLE Reviews ADD Review_noun_length_POS INTEGER''') # DEFAULT 0 was removed from the sql string later removed: NOT NULL DEFAULT 0
# except:
#     print('''The column 'Review_noun_length_POS' exists already''')
#     pass # handle the error
#
# try:
#     cur_w.execute('''ALTER TABLE Reviews ADD Review_verv_length_POS INTEGER''') # DEFAULT 0 was removed from the sql string later removed: NOT NULL DEFAULT 0
# except:
#     print('''The column 'Review_verb_length_POS' exists already''')
#     pass # handle the error
#
# try:
#     cur_w.execute('''ALTER TABLE Reviews ADD Review_word_count_POS INTEGER''') # DEFAULT 0 was removed from the sql string later removed: NOT NULL DEFAULT 0
# except:
#     print('''The column 'Review_word_count_POS' exists already''')
#     pass # handle the error
#
# try:
#     cur_w.execute('''ALTER TABLE Reviews ADD Word_count_POS INTEGER DEFAULT 0''') # DEFAULT 0 was removed from the sql string later removed: NOT NULL DEFAULT 0
# except:
#     print('''The column 'Word_count_POS' exists already''')
#     pass # handle the error

# Add columns for each tag:

# column_names = ([('CC',), ('CD',), ('DT',), ('EX',), ('FW',), ('IN',), ('JJ',),
#     ('JJR',), ('JJS',), ('LS',), ('MD',), ('NN',), ('NNS',), ('NNP',),
#     ('NNPS',), ('PDT',), ('POS',), ('PRP',), ('PRP$',), ('RB',), ('RBR',),
#     ('RBS',), ('RP',), ('SYM',), ('TO',), ('UH',), ('VB',), ('VBD',), ('VBG',),
#     ('VBN',), ('VBP',), ('VBZ',), ('WDT',), ('WP',), ('WP$',), ('WRB',)])
# cur_w.executemany('''ALTER TABLE Reviews ADD COLUMN {0} INTEGER DEFAUT 0'''.format(column_names))

column_names = (['CC', 'CD', 'DT', 'EX', 'FW', 'INN', 'JJ', 'JJR', 'JJS', 'LS',
    'MD', 'NN', 'NNS', 'NNP', 'NNPS', 'PDT', 'POS', 'PRP', 'PRP$', 'RB', 'RBR',
    'RBS', 'RP', 'SYM', 'TOO', 'UH', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ',
    'WDT', 'WP', 'WP$', 'WRB', 'AU', 'PR']) # NOte, 'AU'and 'PR' were added in addition to standard POS tags , and IN and TO tags were replaced by INN and TOO
for column_name in column_names:
    cur_w.execute('''ALTER TABLE Reviews ADD COLUMN ''' + column_name + ''' INTEGER DEFAULT 0''')

sqlstr = 'SELECT id, Review_cleaned FROM Reviews' # Select query that instructs over what we will be iterating
for row in cur.execute(sqlstr):
    count_review = 0
    word_count = 0
    id = row[0]
    reviewtext = row[1]
    wordforms_review = wordformtion(reviewtext)
    all_pos = dict()
    for w in wordforms_review:
        tag = w[1]
        if w[1] == '.' or w[1] == ',' or w[1] == "''" or w[1] == ':':
            continue
        elif w[1] == 'IN':
            tag = 'INN'
        elif w[1] == 'TO':
            tag = 'TOO'
        if tag not in column_names:
            print(tag)
        all_pos[tag] = all_pos.get(tag, 0) + 1

    # all_nouns = nouns(reviewtext)
    # #length = len(all_nouns) This gives the size of the dictionary rather than the number of nouns
    # length = 0
    # for noun in all_nouns:
    #     length = length + all_nouns[noun]
    # all_verbs = verbs(reviewtext)
    # length_verb = 0
    # for verb in all_verbs:
    #     length_verb = length_verb + all_verbs[verb]
    # sentences = sent_tokenize(reviewtext)
    # all_pos = dict()
    # for sentence in sentences:
    #     #text = word_tokenize(sentence)
    #     #print text
    #     nltk_tagged = nltk.pos_tag(word_tokenize(sentence))
    #     #simplifiedTagged = [(word, map_tag('en-ptb', 'universal', tag)) for word, tag in nltk_tagged] #The output variable is a list of tupples, where the first item is a word, while the second one is a simplified POS tag
    #     # We need to perform lemmatization of each word to bring it to its wordnet form.
    #     #list_of_words_WordNet_POS = []
    #     for word, tag in nltk_tagged:
    #         if tag == '.' or tag == ',' or tag == "''" or tag == ':':
    #             continue
    #         elif tag == 'IN':
    #             tag = 'INN'
    #         elif tag == 'TO':
    #             tag = 'TOO'
    #         word_count = word_count + 1
    #         all_pos[tag] = all_pos.get(tag, 0) + 1
    # word_forms_review = wordforms(reviewtext)
    # for word in word_forms_review:
    #     count_review = count_review + word_forms_review[word]
    # cur_w.execute('UPDATE Reviews SET Review_word_count_POS = ? WHERE id = ?', (count_review, id, ))
    # cur_w.execute('UPDATE Reviews SET Word_count_POS = ? WHERE id = ?', (word_count, id, ))
    # cur_w.execute('UPDATE Reviews SET Review_noun_length_POS = ? WHERE id = ?', (length,id, ))
    # cur_w.execute('UPDATE Reviews SET Review_verv_length_POS = ? WHERE id = ?', (length_verb,id, ))
    for tag in all_pos:
        try:
            cur_w.execute("UPDATE Reviews SET (" + tag + ") = ? WHERE id = ?", (all_pos[tag], id))
        except:
            print(tag)

conn_w.commit()

# try:
#     cur_w.execute('''ALTER TABLE [Word Recall] ADD Noun_length INTEGER''') # DEFAULT 0 was removed from the sql string later removed: NOT NULL DEFAULT 0
# except:
#     print('''The column 'Noun_length' exists already''')
#     pass # handle the error
#
# try:
#     cur_w.execute('''ALTER TABLE [Word Recall] ADD Review_verv_length_POS INTEGER''') # DEFAULT 0 was removed from the sql string later removed: NOT NULL DEFAULT 0
# except:
#     print('''The column 'Review-verb-length' exists already''')
#     pass # handle the error
#
# sqlstr = 'SELECT Words_cleaned FROM [Word Recall]' # Select query that instructs over what we will be iterating
# for row in cur.execute(sqlstr):
#     reviewtext = row[0]
#     all_nouns = nouns(reviewtext)
#     #length = len(all_nouns) This gives the size of the dictionary rather than the number of nouns
#     length = 0
#     for noun in all_nouns:
#         length = length + all_nouns[noun]
#     all_verbs = verbs(reviewtext)
#     length_verb = 0
#     for verb in all_verbs:
#         length_verb = length_verb + all_verbs[verb]
#     cur_w.execute('UPDATE [Word Recall] SET Noun_length = ? WHERE Words_cleaned = ?', (length,reviewtext, ))
#     cur_w.execute('UPDATE [Word Recall] SET Review_verv_length_POS = ? WHERE Words_cleaned = ?', (length_verb,reviewtext, ))
#
# conn_w.commit()

cur_w.close()
conn_w.close()
cur.close()
conn.close()

# shutil.copyfile('Liars7_w.sqlite', 'Liars7_length.sqlite')
shutil.copyfile('Liars7_w.sqlite', 'Liars7_pos20210129.sqlite')
