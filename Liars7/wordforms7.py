# This is the new generation code. It creates 2 tables: one for all wordforms,
# the other for the noun-lemmas, and populates it with different information.
# Namely, 1. wordform, POS (the previous 2 uniquelly identify the entry),
# reference id to the noun-lemma it gets converted to.

# import timing
import xlrd
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
            print('There is more thant 1 attribute: ', s, attrib_s)
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
            if words[i-1][0] == "'" and words[i] == "'":
                # print('A word originally in single quatation marks, before the first quatation mark removed: ', words[i-1])
                words[i-1] = words[i-1][1:]
                indexes_todelete = indexes_todelete + [i]
        words = np.delete(words, indexes_todelete).tolist()
        for i in range(1, len(words)):
            word = words[i]
            if word[0] == "'" and word[-1] == "'": words[i] = word[1:-2]
            elif word[0] == "'" and word != "'": words[i] = word[1:]
            elif word[0] == '-' and word != '-': words[i] = word[1:]
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
                wordforms[(word_prev, 'AU')] = wordforms.get((word_prev, 'AU'), 0) + 1

            # if word.lower() == 'dr':
            #     print(sentence)
            if tag[0] == 'V' and word.lower() in ['am', "m", "'m", 'is', "s", "'s", 'are', "re", "'re", 'was', 'were', 'being', 'been', 'be', 'have', "ve", "'ve", 'has', 'had', 'd', "'d", 'do', 'does', 'did', 'will', 'll', "'ll", 'would', 'shall', 'should', 'may', 'might', 'must', 'can', 'could']:
                a += 1 # a marker to memorize that the word was a verb to handle auxiliary verbs
                if a > 3:
                    # print('More than 3 consecutive verbs detected in the following sentence: ', nltk_tagged)
                    a = 0
                    break
                tag_prev = tag
                word_prev = word.lower()
            elif a >= 1 and (tag[:2] == 'RB' or word.lower() in ['not' , "n't", 't', "'t"]):
                a += 1
                # if word.lower() in ["n't", 't', "'t"]:
                #     print("Sentence containing n't, t or 't'", nltk_tagged)
            else: a = 0

            wordforms[(word.lower(), tag)] = wordforms.get((word.lower(), tag), 0) + 1

    return wordforms

def noun_lemmas(wordforms):
    """This function receves as input a dictionary of wordforms and outputs the corresponding noun-lemmas as a dictionary with wordform(word, tag) as key and the noun-lemma as the value"""

    all_nouns = dict()
    wordforms_notinWordNet = []
    for w in wordforms:
        word = w[0]
        tag = w[1]
            # Now let's update the list of nouns.
            # First, we ensure that the word quaifies. That is: 1) it is longer than 2 characters
        if tag[:2] == 'VB' and word == 're':
            word = 'are'
        elif tag[:2] == 'VB' and word == 've':
            word = 'have'

        if ((len(word) > 2 or tag == 'CD' or (tag != 'AU' and word in ['be', 'do', 'go', 'ad', 'is', 'am'])) and word != "n't") or (tag[:2] == 'NN' and word.lower() in ['pc', 'pt', 'ms']): # and tag in ['N', 'V', 'J', 'R']
            if word in ['app', 'apps']:
                word_rep = 'application'
            # elif tag == 'NN' and word.lower() in ['pc']: # ;wnl.lemmatize doesn't work on double words
            #     word_rep = 'personal computer'
            #     print(word_rep)
            elif tag[:2] == 'NN' and word in ['pt']: # ;wnl.lemmatize doesn't work on double words
                word_rep = 'therapist'
            elif tag == 'NNP' and word.lower() in ['ms']: # ;wnl.lemmatize doesn't work on double words
                word_rep = 'microsoft'
            elif tag[:2] == 'JJ' and word in ['ok', 'ok.']: # ;wnl.lemmatize doesn't work on double words
                word_rep = 'satisfactoriness'
            elif word in ['ios']: # ;wnl.lemmatize doesn't work on double words
                word_rep = 'software'
            elif 'smartphone' in word:
                word_rep = 'phone'
            elif tag == 'NNP' and word == 'kevin':
                word_rep = 'person'
            elif tag[0] == 'N' and word in ['others']:
                word_rep = 'people'
            elif 'redesign' in word:
                word_rep = 'design'
            elif 'restructure' in word:
                word_rep = 'structure'
            elif 'realign' in word:
                word_rep = 'align'
            elif tag[0] == 'N' and word == 'rhyming':
                word_rep = 'rhyme'
            elif 'download' in word:
                word_rep = 'transfer'
            elif 'customize' in word:
                word_rep = 'custom'
            elif 'thank' in word:
                word_rep = 'thanks'
            elif 'keyboarding' in word:
                word_rep = 'keyboard'
            elif 'multitasking' in word:
                word_rep = 'task'
            elif 'off-putting' in word:
                word_rep = 'appeal'
            elif 'inexcusable' in word:
                word_rep = 'excuse'
            elif tag[:2] == 'VB' and word == 'due':
                word_rep = 'do'
            elif tag[0] == 'V' and 'enable' in word:
                word_rep = 'ability'
            # elif tag[0] == 'V' and word == 'sobering':
            #     word_rep = 'sobriety'
            elif tag[0] == 'J' and word == 'unorganized':
                word_rep = 'organization'
            elif tag[0] == 'J' and word == 'hypermobile':
                word_rep = 'mobility'
            elif tag[0] == 'J' and word == 'memorable':
                word_rep = 'memory'
            elif tag[0] == 'J' and word == 'delightful':
                word_rep = 'delight'
            elif tag[0] == 'J' and word == 'optional':
                word_rep = 'option'
            elif tag[0] == 'J' and word == 'outdated':
                word_rep = 'date'
            elif tag[0] == 'J' and word == 'positional':
                word_rep = 'position'
            elif tag[0] == 'J' and word == 'unfocused':
                word_rep = 'focus'
            elif tag[0] == 'J' and word == 'descriptive':
                word_rep = 'description'
            elif word in ['never', 'once', 'already', 'full-time', 'ever', 'initially', 'again', 'sometimes', 'before', 'yet', 'soon', 'ahead', 'anytime', 'eventually', 'finally', 'ago', 'throughout']:
                word_rep = 'time'
            elif tag[:2] == 'RB' and word in ['prior']:
                word_rep = 'time'
            elif word in ['maybe', 'perhaps']:
                word_rep = 'possibility'
            elif tag == 'RB' and word in ['quite', 'bit', 'far']:
                word_rep = 'extent'
            elif tag == 'RB' and word in ['long']:
                word_rep = 'length'
            elif tag[0] == 'R' and word == 'simply':
                word_rep = 'simplicity'
            elif tag[0] == 'R' and word == 'professionally':
                word_rep = 'profession'
            elif tag[0] == 'R' and word == 'supposedly':
                word_rep = 'supposition'
            elif tag[0] == 'R' and word == 'undoubtedly':
                word_rep = 'doubt'
            elif tag[0] == 'R' and word == 'continually':
                word_rep = 'continuity'
            elif tag[0] == 'R' and word == 'safely':
                word_rep = 'safety'
            elif tag[0] == 'R' and word == 'routinely':
                word_rep = 'routine'
            elif tag[0] == 'R' and word == 'additionally':
                word_rep = 'addition'
            elif tag[0] == 'R' and word == 'namely':
                word_rep = 'name'
            elif tag[0] == 'R' and word == 'periodically':
                word_rep = 'period'
            elif tag[0] == 'R' and word == 'relaxed':
                word_rep = 'relaxation'
            elif word in ['another', 'every', 'both', 'either', 'together', 'anymore', 'almost', 'else']:
                word_rep = 'number'
            elif word in ['visually']:
                word_rep = 'vision'
            elif tag[0] == 'R' and word in ['most', 'more']:
                word_rep = 'group'
            elif tag[0] == 'R' and word in ['around', 'away', 'elsewhere', 'wherever', 'anywhere', 'between', 'sidewards', 'forth']:
                word_rep = 'place'
            elif tag[0] == 'R' and word in ['loose']:
                word_rep = 'looseness'
            elif tag[:2] == 'RB' and word in ['lighter']:
                word_rep = 'lightness'
            else:
                word_rep = word
            noun = None # pre-assign the variable noun to None
            # check if the word is found in WordNet as it is:
            if (tag[0] == 'N' or tag == 'CD') and wn.synsets(wnl.lemmatize(word_rep,'n'), pos='n') != []:
                noun = wnl.lemmatize(word_rep,'n') # = all_nouns.get((word.lower(), tag, wnl.lemmatize(word_rep,'n')), 0) + 1
            elif 'sideway' in word_rep:
                noun = ['side', 'way'] # = all_nouns.get((word.lower(), tag, ('side', 'way')), 0) + 1
            # elif tag[0] == 'N' and word.lower() == 'rhyming':
            #     all_nouns['rhyme'] = all_nouns.get('rhyme', 0) + 1
            elif tag[0] in ['N', 'V', 'J', 'R'] and tag != 'RP': # Added on 20200520 "and tag != 'RP'" to exclude Particles. New idea: use derivationally related forms etc. Original idea: Transform the word through stemming and lemmatization
                short_tag = tag[0].lower() # generate a short-tag from POS tag
                if short_tag == 'j': short_tag = 'a'

                noun = nounify(word_rep, short_tag) # prints out word and short_tag if not found in Wordnet

                if noun == None and word_rep not in ['also', 'not', 'just', 'too', 'instead', 'only', 'very', 'rather', 'however', 'esque', 'but', 'anyway', 'furthermore', 'about', 'though', 'regardless', 'alright', 'further', 'mostly', 'anyways', 'nonetheless', 'virtually', 'beyond', 'along', 'alongside', 'somehow']:# and word.lower()[-2:] != 'ly':
                    # check if the word is found in WordNet as it is:
                    if wn.synsets(wnl.lemmatize(word_rep,'n'), pos='n') != [] and word not in ['tho', 'otter']:
                        noun = wnl.lemmatize(word_rep,'n') # = all_nouns.get((word.lower(), tag, wnl.lemmatize(word_rep,'n')), 0) + 1

            if tag[:2] in ['NN', 'VB', 'JJ', 'RB', 'CD'] and noun == None and word_rep not in ['also', 'not', 'just', 'too', 'instead', 'only', 'very', 'rather', 'however', 'esque', 'but', 'anyway', 'furthermore', 'about', 'though', 'regardless', 'alright', 'further', 'mostly', 'anyways', 'nonetheless', 'virtually', 'beyond', 'along', 'alongside', 'somehow', 'thus']:# and word.lower()[-2:] != 'ly':
                wordforms_notinWordNet = wordforms_notinWordNet + [w]
            elif noun != None:
                    all_nouns[w] = noun # = all_nouns.get((word.lower(), tag, noun), 0) + 1

    return all_nouns, wordforms_notinWordNet

# Now lets define the fuctions to find both hypernym and hyponym depth.
def hypernym_depth(word, postag):
    return wn.synsets(wnl.lemmatize(word, postag), postag)[0].min_depth() #this selects the first synset. We could think of a smarter way of selecting a synset
    #wn.synset('car.n.01').min_depth()


# Now let's create a table with verbs inside our database and populate it with their respective depth values
import sqlite3
import shutil # we use this library to create a copy of a file (in this case to duplicate the database
# so that we can loop over one instance while editing the other)
# Establish a SQLite connection to a database named 'Liars4.sqlite':
conn = sqlite3.connect('Liars7_clean_tr20200618.sqlite')
# Get the cursor, which is used to traverse the database, line by line
cur = conn.cursor()
# Then we duplicate thedatabase, so that one can loop and edit it at the same time
# and 'open' the other 'instance' of the same database
shutil.copyfile('Liars7_clean_tr20200618.sqlite', 'Liars7_w.sqlite')
conn_w = sqlite3.connect('Liars7_w.sqlite')
cur_w = conn_w.cursor()

# First, let's move brysbaert into SQL:
#Input the name of the excel file to be converted into a SQL database
name = input("Enter excel file name:")
if len(name) < 1 : name = "Concreteness_ratings_Brysbaert_et_al_BRM.xlsx"

# Open the workbook and define the worksheet:
wb = xlrd.open_workbook(name)

# We could add input() function to select the sheets we would like
#to convert into the database
sheet = wb.sheet_by_index(0) #selecting the first sheet only
#sheet = book.sheet_by_name('Organized')
# Create a new table in the database:
# Note: The first line after 'try' statement deletes the table if it already exists.
# This is good at the stage of twicking your code. After the code for importing into
# the database from excel is finalized it is better to remove this: 'DROP TABLE IF EXISTS Reviews;'
# The 'try except else' that follows will generate a message if the table we are
# trying to create already exists.

try:
    cur_w.executescript('''DROP TABLE IF EXISTS BWK;
        CREATE TABLE BWK (
        id                        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        Wordform                  TEXT UNIQUE,
        Dom_Pos                   TEXT,
        Concreteness              REAL,
        Concreteness_SD           REAL,
        SUBTLEX                   INTEGER,
        Bigram                    INTEGER
        )''')
except sqlite3.OperationalError:
    print('Most probably the table we are trying to create already exists')
else:
    print('The table "BWK" has been successfully created')

try:
    cur_w.executescript('''DROP TABLE IF EXISTS [Noun-lemmas];
        CREATE TABLE [Noun-lemmas] (
        id                        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        Noun_lemma                TEXT UNIQUE,
        RF                        INTEGER DEFAULT 0,
        WordNet_depth             INTEGER
        )''')
except sqlite3.OperationalError:
    print('Most probably the table we are trying to create already exists')
else:
    print('The table "Noun-lemmas" has been successfully created')

try:
    cur_w.executescript('''DROP TABLE IF EXISTS Wordforms;
        CREATE TABLE Wordforms (
        id                        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        Wordform                  TEXT,
        POS                       TEXT,
        TF                        INTEGER DEFAULT 0,
        RF                        INTEGER DEFAULT 0,
        noun_lemma_id             INTEGER,
        UNIQUE(Wordform, POS)
        )''') # Note: noun_lemma_id need to replace by INTEGERE NOT NULL
except sqlite3.OperationalError:
    print('Most probably the table we are trying to create already exists')
else:
    print('The table "Wordforms" has been successfully created')

#Create a For loop to iterate through each row in the XLS file,
#starting at row 3 by default to skip the headers:
for r in range(1, sheet.nrows):
    if sheet.cell_type(r, 0) == (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK): continue
    else:
        try: # attempt to extract the content of the relevant cells
#            id                  = int(sheet.cell(r,0).value)
            wordform = sheet.cell(r,0).value
            dom_pos = sheet.cell(r,8).value
            concretness = float(sheet.cell(r,2).value)
            concreteness_sd = float(sheet.cell(r,3).value)
            subtlex         = int(sheet.cell(r,7).value)
            bigram          = int(sheet.cell(r,1).value)
            # print(id, date, duration, condition, word_recall)
            # break
            #condition       = 1
            #review          = 'abra'
        except IndexError: #handling the error: print a possible error source
            print('One or several of the cells selected may be out of the table range. Please doublecheck the location of the column from which to parse the data')
        else: # populating the table with data from the original excel
            cur_w.execute('''INSERT OR IGNORE INTO BWK (Wordform, Dom_Pos, Concreteness, Concreteness_SD, SUBTLEX, Bigram)
                VALUES (?, ?, ?, ?, ?, ?)''', (wordform, dom_pos, concretness, concreteness_sd, subtlex, bigram))

        #cur.execute('SELECT id FROM Product WHERE asin = ? ', (asin, ))
        #Product_id = cur.fetchone()[0]

# Commit the transaction
conn_w.commit()

# Next we loop through each review and identify a dictionary of wordforms and a dictionary of noun_lemmas

# Next we define the column through which we are going to loop
sqlstr = 'SELECT id, Review_cleaned FROM Reviews'

number_convertable = 0

nouns_notinWordNet = dict()
number_convertable_nouns = 0

verbs_notinWordNet = dict()
number_convertable_verbs = 0

adj_notinWordNet = dict()
number_convertable_adj = 0

adv_notinWordNet = dict()
number_convertable_adv = 0

# Here we loop through the table, extract the verbs from the reviews and populate the new table with values of depth and frequency in the whole corpus for each verb
for row in cur.execute(sqlstr):
    id = row[0]
    reviewtext = row[1]#.encode('ascii','ignore')
    word_forms_review = wordformtion(reviewtext)
    [nouns, wordforms_notinWordNet] = noun_lemmas(word_forms_review)

    # Now we need to loop through words in the review and get the value of depth for each one of them (and also keep the total count for each word)
    convertables = list()
    for wordform in word_forms_review:
        word = wordform[0]
        pos = wordform[1]
        tf = word_forms_review[wordform]
        rf = 0
        if tf > 0:
            rf = 1
        try:
            noun = nouns[wordform]
            if type(noun) == list:
                separator = ', '
                noun = separator.join(noun)
            cur_w.execute('''INSERT OR IGNORE INTO [Noun-lemmas] (Noun_lemma) VALUES (?)''', (noun,))
            cur_w.execute('''UPDATE [Noun-lemmas] SET RF = RF + ? WHERE Noun_lemma = ?''', (rf, noun))
            cur_w.execute('SELECT id FROM [Noun-lemmas] WHERE Noun_lemma = ? ', (noun, ))
            noun_id = cur_w.fetchone()[0]
            # noun_id = cur_w.lastrowid # cur_w.fetchone()[0] - need a select before this line
        except:
            noun_id = None

        cur_w.execute('''INSERT OR IGNORE INTO Wordforms (Wordform, POS, noun_lemma_id)
            VALUES (?, ?, ?)''', (word, pos, noun_id))
        cur_w.execute('''UPDATE Wordforms SET TF = TF + ? WHERE (Wordform = ? AND POS = ?)''', (tf, word, pos))
        cur_w.execute('''UPDATE Wordforms SET RF = RF + ? WHERE (Wordform = ? AND POS = ?)''', (rf, word, pos))

        # Let's count the convertable forms
        if len(word) > 2 and pos[0] in ['N', 'V', 'J', 'R'] and pos[0] != 'RP' and word not in ['esque', 'also', 'not', 'just', 'too', 'instead', 'only', 'very', 'rather', 'however', 'but', 'anyway', 'furthermore', 'about', 'though', 'regardless', 'alright', 'further', 'mostly', 'anyways', 'nonetheless', 'virtually', 'beyond', 'along', 'alongside', 'somehow', 'thus']: # added "and wordform[1][0] != 'RP'" on 20200520
            convertables = convertables + [wordform]

    number_convertable = number_convertable + len(convertables)

    convertable_nouns = list()
    for wordform in word_forms_review:
        if len(wordform[0]) > 2 and wordform[1][:2] in ['NN', 'CD'] and wordform[1][0] != 'RP' and wordform[0].lower() not in ['esque', 'also', 'not', 'just', 'too', 'instead', 'only', 'very', 'rather', 'however']:
            convertable_nouns = convertable_nouns + [wordform]
            if wordform[0].lower() == 'full':
                print(reviewtext)
    number_convertable_nouns = number_convertable_nouns + len(convertable_nouns)

    convertable_verbs = list()
    for wordform in word_forms_review:
        if len(wordform[0]) > 2 and wordform[1][0] == 'V' and wordform[1][0] != 'RP' and wordform[0].lower() not in ['esque', 'also', 'not', 'just', 'too', 'instead', 'only', 'very', 'rather', 'however']:
            convertable_verbs = convertable_verbs + [wordform]
            # if wordform[0].lower() == 'sideways':
            #     print(reviewtext)
    number_convertable_verbs = number_convertable_verbs + len(convertable_verbs)

    convertable_adj = list()
    for wordform in word_forms_review:
        if len(wordform[0]) > 2 and wordform[1][0] == 'J' and wordform[1][0] != 'RP' and wordform[0].lower() not in ['esque', 'also', 'not', 'just', 'too', 'instead', 'only', 'very', 'rather', 'however']:
            convertable_adj = convertable_adj + [wordform]
    number_convertable_adj = number_convertable_adj + len(convertable_adj)

    convertable_adv = list()
    for wordform in word_forms_review:
        if len(wordform[0]) > 2 and wordform[1][:2] == 'RB' and wordform[0].lower() not in ['also', 'not', 'just', 'too', 'instead', 'only', 'very', 'rather', 'however', 'esque', 'but', 'anyway', 'furthermore', 'about', 'though', 'regardless', 'alright', 'further', 'mostly', 'anyways', 'nonetheless', 'virtually', 'beyond', 'along', 'alongside', 'somehow', 'thus']: # excludes WH adverbs
            convertable_adv = convertable_adv + [wordform]
            # if wordform[0].lower() == 'okay':
            #     print(reviewtext)
    number_convertable_adv = number_convertable_adv + len(convertable_adv)

    # print('The number of convertable wordforms: ', len(convertables))
    # print('Convertable wordforms: ', len(convertables), convertables)
    if wordforms_notinWordNet != []:
        for wordform in wordforms_notinWordNet:
            if wordform[1][0] == 'N':
                nouns_notinWordNet[wordform[0]] = nouns_notinWordNet.get(wordform[0], 0) + 1 # counts the number of reviews with such a wordform
                # if wordform[0].lower() == 'kevin':
                #     print(wordform)
            if wordform[1][0] == 'V':
                verbs_notinWordNet[wordform[0]] = verbs_notinWordNet.get(wordform[0], 0) + 1 # counts the number of reviews with such a wordform
                # if wordform[0].lower() == 'ping':
                #     print(reviewtext)

            if wordform[1][0] == 'J':
                adj_notinWordNet[wordform[0]] = adj_notinWordNet.get(wordform[0], 0) + 1 # counts the number of reviews with such a wordform
                # if wordform[0].lower() == 'tight':
                #     print(reviewtext)

            if wordform[1][:2] == 'RB':
                adv_notinWordNet[wordform[0]] = adv_notinWordNet.get(wordform[0], 0) + 1 # counts the number of reviews with such a wordform
                # if wordform[0].lower() == 'ahead':
                #     print(reviewtext)

    # for w in word_forms_review:
    #     word = wordformm[0]
    #     # print(word)
    #     pos = wordformm[1]
    #     # print(pos)
    #     count = wordforms_review[wordformm]
    #     # if wn.synsets(wnl.lemmatize(word,'n'), pos='n')==[]:
    #     #     # print(word, tag)
    #     #     continue #excludes nouns which can not be found in WordNet
    #     # else:
    #     #     #print word
    #     #     if len(wnl.lemmatize(word.lower(),'n')) > 1 :
    #     #         if (hypernym_depth(wnl.lemmatize(word.lower(),'n'), 'n') == 0 and wnl.lemmatize(word.lower(),'n') != 'entity'): continue
    #     #         else:
    #     #             all_nouns[wnl.lemmatize(word.lower(),'n')] = all_nouns.get(wnl.lemmatize(word.lower(),'n'),0)+1 # we lowercased all words. before doing that there was about 3600 unique words. After the change 3076 words left
    #     #     else: continue
    #     cur_w.execute('''INSERT OR IGNORE INTO Wordforms (Wordform, POS)
    #         VALUES (?,?)''', (word, pos))
    #     cur_w.execute('''UPDATE Wordforms SET TF = TF + ? WHERE (Wordform = ? AND POS = ?)''', (count, word, pos))

conn_w.commit()

number_nouns_notfound = 0
for wordform in nouns_notinWordNet:
    number_nouns_notfound = number_nouns_notfound + nouns_notinWordNet[wordform]

number_verbs_notfound = 0
for wordform in verbs_notinWordNet:
    number_verbs_notfound = number_verbs_notfound + verbs_notinWordNet[wordform]

number_adj_notfound = 0
for wordform in adj_notinWordNet:
    number_adj_notfound = number_adj_notfound + adj_notinWordNet[wordform]

number_adv_notfound = 0
for wordform in adv_notinWordNet:
    number_adv_notfound = number_adv_notfound + adv_notinWordNet[wordform]

print('Number of convertable wordforms: ', number_convertable)

print('Number of convertable nouns: ', number_convertable_nouns)
print('Number of nouns not converted: ', number_nouns_notfound)
print('Number of unique nouns which were not converted: ', len(nouns_notinWordNet))
print('Non-converted noun-wordforms: ', nouns_notinWordNet)

print('Number of convertable verbs: ', number_convertable_verbs)
print('Number of verbs not converted: ', number_verbs_notfound)
print('Number of unique verbs which were not converted: ', len(verbs_notinWordNet))
print('Non-converted verb-wordforms: ', verbs_notinWordNet)

print('Number of convertable adjectives: ', number_convertable_adj)
print('Number of adjectives not converted: ', number_adj_notfound)
print('Number of unique adjectives which were not converted: ', len(adj_notinWordNet))
print('Non-converted adjective-wordforms: ', adj_notinWordNet)

print('Number of convertable adverbs: ', number_convertable_adv)
print('Number of adverbs not converted: ', number_adv_notfound)
print('Number of unique adverbs which were not converted: ', len(adv_notinWordNet))
print('Non-converted adverb-wordforms: ', adv_notinWordNet)
#
# sqlstr = 'SELECT Words_cleaned FROM [Word Recall]'
#
# # Here we loop through the table, extract the verbs from the reviews and populate the new table with values of depth and frequency in the whole corpus for each verb
# for row in cur.execute(sqlstr):
#     reviewtext = row[0]#.encode('ascii','ignore')
#     # The following line tests if the loop works by printing out the contents of the column row by row up to row 9
#     #if line < 10: print(reviewtext,type(reviewtext))
#
#     allverbs_in_review = verbs(reviewtext)
#     # Now we need to loop through verbs in the review and get the value of depth for each one of them (and also keep the total count for each verb)
#     for verb in allverbs_in_review:
#         depth = hypernym_depth(verb, 'v')
#         #frequency = frequency + allverbs_in_review[verb]
#         #frequency = 0
#         if (len(verb)<2 or (depth == 0 and verb != 'entity')): continue # make sure the words which are not in word and give depth 0 are not included. usually those are incorrectly assigned parts of speech. there was 298 of them without this line of code
#         else:
#             #if len(verb)<2: print verb
#             cur_w.execute('''INSERT OR IGNORE INTO Verbs (Verb, Depth)
#                     VALUES (?,?)''', (verb, depth))
#         #conn_w.commit()
# conn_w.commit()

# Now lets populate the table with verb count in the whole corpus.
#shutil.copyfile('Liars4_w.sqlite', 'Liars4_s.sqlite') # we need to create an extra database to use it to generate another search query, because we will need a nested loop (a loop with a subloop)
# conn_s = sqlite3.connect('Liars4_s.sqlite')
# cur_s = conn_s.cursor()
# for row in cur_s.execute('SELECT verb FROM verbs'):
#     verb = row[0]
#     count = 0
#     for line in cur:
#         reviewtext = line[0]
#         count = count + verbs(reviewtext)[verb]
#     cur_w.execute('''INSERT OR IGNORE INTO verbs (TF)
#                 VALUES (?)''', (count))
#
# conn_w.commit()
    # in the line just below we test if updating a column with set values of similarity works correctly
    #similarity = 0.5
    #cur_w.execute('UPDATE Reviews SET Similarity = ? WHERE review = ?', (similarity, reviewtext, ))
    #conn_w.commit()
    #line = line + 1

cur_w.close()
conn_w.close()
cur.close()
conn.close()
shutil.copyfile('Liars7_w.sqlite', 'Liars7_wordforms.sqlite')
