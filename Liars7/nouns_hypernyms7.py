# Working on a code that will generate concreteness values for each review
# We have observed that using nouns alone is not enough, as the number of nouns
# does depend on the condition and the specifics of the experiment. Namely,
# the semantic memory reliance means participants will mostly recall relevant
# nouns, thus potentially boosting the concreteness score based on nouns alone.
# We believe including verbs adjectives and adverbs could be essential from the
# theoretical POV (verbs define specific actions, adjectives specify nouns,
# adverbs specify verbs). And also from the computational POV. It seems that
# nouns, verbs and adjectives (some speific POS tags) differ significantly
# between the conditions. Even throughout various datasets.

# The following concreteness parameters TYPES may be of interest:
# categorical vs perceptual concretness;
# total concreteness vs. specific concretness (divided)
# For specific concreteness, we do not want it in SQL, as we can always divide
# by a relevant parameter afterwards as long as we have it in the tables.
# For categorical concretness we have the

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

# Now we have a dictionary with nouns and their occurences. We could replace it
# with a dictionary of nouns excluding stopwords or we could exclude stopwords
# when we calculate the depth of the review only

# Now lets define the fuctions to find both hypernym and hyponym depth.
def hypernym_depth(word, postag):
    return wn.synsets(wnl.lemmatize(word, postag), postag)[0].min_depth() #this selects the first synset. We could think of a smarter way of selecting a synset

def get_hypernyms(synset):
    hypernyms = set()
    for h in synset.hypernyms():
        hypernyms |= set(get_hypernyms(h))
    return hypernyms | set(synset.hypernyms())

def get_hyponyms(synset):
    hyponyms = set()
    for h in synset.hyponyms():
        hyponyms |= set(get_hyponyms(h))
    return hyponyms | set(synset.hyponyms())

def hyp_num(noun, POS): # 20200617 added POS option to make sure we pick the right synset (proper none or not)
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

def chain_nods(noun):
    synset = wn.synsets(noun, 'n')[0]
    hyp_set = get_hypernyms(synset)
    hypo_set = get_hyponyms(synset)

    return len(hyp_set|hypo_set)

def wordforms_to_filter(condition): # 0 - fake, 1 - real, 3 - recall
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

    wordforms_instructions = wordformtion(instructions)
    wordfroms_list = [wordform[0] for wordform in wordforms_instructions]
    # print(type(nouns_instructions))
    # print(nouns_instructions)
    return wordforms_list

def nouns_to_filter(condition): # 0 - fa ke, 1 - real, 3 - recall
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

    wordforms_instructions = wordformtion(instructions)
    nouns_instructions = noun_lemmas(wordforms_instructions)[0]
    nouns_list = []
    for n in nouns_instructions.values():
        if n not in nouns_list:
            nouns_list.append(n)
    # print(type(nouns_instructions))
    # print(nouns_instructions)
    return nouns_list

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
conn_w = sqlite3.connect('Liars7_w.sqlite') # The database to be updated
cur_w = conn_w.cursor()

# try:
#     cur_w.execute('''ALTER TABLE [Noun-lemmas] ADD Nods_in_chain INTEGER DEFAULT 0''') # DEFAULT 0 was removed from the sql string
# except:
#     print('''The column 'Nods_in_chain' exists already''')
#     pass # handle the error

# exclusion_list_fake = nouns_to_filter(0)
# exclusion_list_real = nouns_to_filter(1)
# exclusion_list_recall = nouns_to_filter(3)

# exclusion_list_fake = []
# exclusion_list_real = []
# # exclusion_list_recall = []
#
# print('Nouns exclusion list for the fake condition: ', exclusion_list_fake)
# print('Nouns exclusion list for the real condition: ', exclusion_list_real)

sqlstr = 'SELECT id, Noun_lemma FROM [Noun-lemmas]' # Select query that instructs over what we will be iterating
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
    # try:
    #     cur_w.execute('UPDATE [Noun-lemmas] SET WordNet_depth = ? WHERE id = ?', (depth, id, ))
    # except:
    #     print("Didn't calculate for the following noun_lemma: ", noun)

conn_w.commit()
cur_w.close()
conn_w.close()
cur.close()
conn.close()

shutil.copyfile('Liars7_w.sqlite', 'Liars7_nouns.sqlite')
