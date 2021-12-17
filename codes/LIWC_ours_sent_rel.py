# This code loads the LIWC results for the reviews

# import timing
import xlrd
import nltk
from nltk.corpus import wordnet as wn
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag.mapping import tagset_mapping, map_tag
from nltk.stem import WordNetLemmatizer

import sqlite3
import shutil # we use this library to create a copy of a file (in this case to duplicate the database
# so that we can loop over one instance while editing the other)
# Establish a SQLite connection to a database named 'Liars4.sqlite':
conn = sqlite3.connect('Liars7_LIWC_rel.sqlite')
# Get the cursor, which is used to traverse the database, line by line
cur = conn.cursor()
# Then we duplicate thedatabase, so that one can loop and edit it at the same time
# and 'open' the other 'instance' of the same database
shutil.copyfile('Liars7_LIWC_rel.sqlite', 'Liars7_w.sqlite')
conn_w = sqlite3.connect('Liars7_w.sqlite')
cur_w = conn_w.cursor()

# Create columns for LIWC data:

try: # cleaned
    cur_w.execute('''ALTER TABLE Sentences_raw ADD space_rel_LIWC REAL DEFAULT 0''') # DEFAULT 0 was removed from the sql string
except:
    print('''The column 'space_rel_LIWC' exists already''')
    pass # handle the error

try: # cleaned
    cur_w.execute('''ALTER TABLE Sentences_raw ADD time_rel_LIWC REAL DEFAULT 0''') # DEFAULT 0 was removed from the sql string
except:
    print('''The column 'time_rel_LIWC' exists already''')
    pass # handle the error

# First, let's move brysbaert into SQL:
#Input the name of the excel file to be converted into a SQL database
# name = input("Enter excel file name:")
# if len(name) < 1 : name = "Concreteness_ratings_Brysbaert_et_al_BRM.xlsx"

name = "LIWC_Sentences_TimeSpaceRel.xls"

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

#Create a For loop to iterate through each row in the XLS file,
#starting at row 3 by default to skip the headers:
for r in range(1, sheet.nrows):
    if sheet.cell_type(r, 0) == (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK): continue
    else:
        try: # attempt to extract the content of the relevant cells
            id                  = int(sheet.cell(r,0).value)
            spaceRel            = float(sheet.cell(r,7).value)
            timeRel             = float(sheet.cell(r,6).value)
        except IndexError: #handling the error: print a possible error source
            print('One or several of the cells selected may be out of the table range. Please doublecheck the location of the column from which to parse the data')
        else: # populating the table with data from the original excel
            cur_w.execute('''UPDATE Sentences_raw SET (space_rel_LIWC, time_rel_LIWC) = (?, ?) WHERE id = ?''', (spaceRel, timeRel, id))

        #cur.execute('SELECT id FROM Product WHERE asin = ? ', (asin, ))
        #Product_id = cur.fetchone()[0]

# Commit the transaction
conn_w.commit()
cur_w.close()
conn_w.close()
cur.close()
conn.close()
shutil.copyfile('Liars7_w.sqlite', 'Liars7_LIWC_Rel_sent.sqlite')
