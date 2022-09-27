# update Reviews table with different values necessary to calculate WWW and maybe Narrative (Transportation)
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

# def www_sent(sentence):
#     # This function take a sentence as an input and outpust the list of variables to be used for WWW, namely: s, t, www_ST,  www_ST_pairs, space_emb, time_emb, www_st_emb
#     conn_sent = sqlite3.connect('Liars7_www.sqlite') # The copy of the original database to use for iterating
#     # # Get the cursor, which is used to traverse the database, line by line
#     cur_sent = conn_sent.cursor()
#     sqlstr = "SELECT WC_LIWC, space_LIWC, time_LIWC, WWW_ST, WWW_ST_pairs, Space_emb, Time_emb, WWW_ST_emb FROM Sentences WHERE Sentence = ?"
#     cur_sent.execute(sqlstr, (sentence,))
#     row = cur_sent.fetchone()
#     # print(row, type(row))
#     wc = row[0]
#     space = round(wc*row[1]/100) # convert perrcentages from LIWV into actual counts
#     time = round(wc*row[2]/100) # convert perrcentages from LIWV into actual counts
#     www = row[3]
#     www_pairs = row[4]
#     space_emb = row[5]
#     time_emb = row[6]
#     www_emb = row[7]
#
#     return space, time, www, www_pairs, space_emb, time_emb, www_emb

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

    return www_dic # dictionary with key: tuple of (sentence, occurence rate in text) and value = space, time, www, www_pairs, space_emb, time_emb, www_emb

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

def wordlemmas(text):
    # First create a list of wordforms for the text:
    word_forms = wordformtion(text) # A dictionary with (word, POS) tuples as keys and the occurence rate of those in the text as the value
    # First we need to compile a list of lemmas for the text
    word_lemmas = dict()
    for w in word_forms:
        if w[1][0] in ['N', 'V', 'J', 'R'] or w[1] == 'CD':
            short_tag = w[1].lower()[0] # generate a short-tag from POS tag
            if short_tag == 'j':
                short_tag = 'a'
            elif short_tag == 'c':
                short_tag = 'n'
            w_l = wnl.lemmatize(w[0], short_tag)
            word_lemmas[w_l] = word_lemmas.get(w_l, 0) + word_forms[w]
    return word_lemmas # dictionary with lemma as key and occurence count as value 20201119

def lemmas_to_filter(condition): # 0 - fake, 1 - real, 3 - recall
    # Need to open the .txt file first
    filepath = "common_text.txt"
    handle = open(filepath)
    # The following line of code creates a string object from the text inside the file
    instructions_common = handle.read()

    # Now let's add the instruction file specific to real/fake condition
    if condition != 3:
        if condition == 0:
            file_cond = "fake_text.txt"
        else: file_cond = "real_text.txt"

        handle_cond = open(file_cond)
        instructions_cond = handle_cond.read()

        instructions = instructions_common + instructions_cond
    else:
        instructions = instructions_common

    # print(instructions)

    lemmas_instructions = wordlemmas(instructions)
    lemmas_list = [l for l in lemmas_instructions]
    # print(type(nouns_instructions))
    # print(nouns_instructions)
    return lemmas_list

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
shutil.copyfile('Liars7_www.sqlite', 'Liars7_w.sqlite') # we need to create an extra database to use it to generate another search query, because we will need a nested loop (a loop with a subloop)
conn = sqlite3.connect('Liars7_www.sqlite')
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
    cur_w.execute('''ALTER TABLE Reviews ADD What_sent_inst INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
except:
    print("The column 'What_sent_inst' exists already")
    pass # handle the error


# try:
#     cur_w.execute('''ALTER TABLE Reviews ADD WWW_ST INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
# except:
#     print("The column 'WWW_ST' exists already")
#     pass # handle the error

try:
    cur_w.execute('''ALTER TABLE Reviews ADD WWW_ST_sent_inst_obj INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
except:
    print("The column 'WWW_ST_sent_inst_obj' exists already")
    pass # handle the error

# try:
#     cur_w.execute('''ALTER TABLE Reviews ADD WWW_ST_pairs INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
# except:
#     print("The column 'WWW_ST_pairs' exists already")
#     pass # handle the error

try:
    cur_w.execute('''ALTER TABLE Reviews ADD WWW_ST_pairs_sent_inst_obj INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
except:
    print("The column 'WWW_ST_pairs_sent_inst_obj' exists already")
    pass # handle the error


try:
    cur_w.execute('''ALTER TABLE Reviews ADD WWW_ST_emb_sent_inst_obj INTEGER NOT NULL DEFAULT 0''') # TF-er is the originally calculated value wich colculated the sum of numbers of unique nouns in each review  DEFAULT 0 was removed from the sql string
except:
    print("The column 'WWW_ST_emb_sent_inst_obj' exists already")
    pass # handle the error

# Need to generate instructions exclusion lists
exclusion_list_fake = lemmas_to_filter(0)
exclusion_list_real = lemmas_to_filter(1)
print('Lemmas exclusion list for the fake condition: ', len(exclusion_list_fake), exclusion_list_fake)
print('Lemmas exclusion list for the real condition: ', len(exclusion_list_real), exclusion_list_real)

exclusion_set_fake = set(exclusion_list_fake)
exclusion_set_real = set(exclusion_list_real)
print('Lemmas exclusion set for the fake condition: ', len(exclusion_set_fake), exclusion_set_fake)
print('Lemmas exclusion set for the real condition: ', len(exclusion_set_real), exclusion_set_real)

#can you make a clumn formula? i.e set the column equal to some function of the other column?
#cur_w.execute('UPDATE Nouns SET Frequency = TF/?', (count, ))
sqlstr = 'SELECT Participants.id, Condition, Review FROM Participants JOIN Reviews ON Participants.id = Reviews.id'
for row in cur.execute(sqlstr):
    prmr_id = row[0]
    condition = row[1]
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

    review_text = row[2]
    www = www_counts(review_text)
    what_sent = 0
    www_ST_sent = 0
    www_pairs_sent = 0
    www_emb_sent = 0
    for sf in www:
        # NOTE: we do not count the repeated sentences twice. In this dataset this wouldn't matter though, as sentences do not repeat within the same review
        # Check if sentence contains words with lemmas from the instructions lists
        sentence_lemmas = wordlemmas(sf[0]) # dictionary, keys - lemmas
        lemmas_set = sentence_lemmas.keys()
        if condition == 1 and exclusion_set_real.intersection(lemmas_set):
            continue
        elif condition == 0 and exclusion_set_fake.intersection(lemmas_set):
            continue

        what_sent += www[sf][0]
        www_ST_sent += www[sf][1]
        www_pairs_sent += www[sf][2]
        www_emb_sent += www[sf][3]
    cur_w.execute('UPDATE Reviews SET What_sent_inst = ?,  WWW_ST_sent_inst_obj = ?, WWW_ST_pairs_sent_inst_obj = ?,  WWW_ST_emb_sent_inst_obj = ? WHERE id = ?', (what_sent, www_ST_sent, www_pairs_sent, www_emb_sent, prmr_id, ))

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

shutil.copyfile('Liars7_w.sqlite', 'Liars7_www_inst.sqlite')
shutil.copyfile('Liars7_www_inst.sqlite', r"C:\Users\i_gordeliy\Dropbox\Marketing\Liars\Liars7git\Liars7_www_sent.sqlite")
