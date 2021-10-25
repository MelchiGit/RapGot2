pip install lyricsgenius

import re

# Open a file and store contents
textFile = open('G:\Dropbox\Dropbox\Personal\Projects\RapGot\Lyrics.txt', encoding="utf8", mode='r')
fileContent = textFile.read()
textFile.close()

# pattern  = re.compile(r'[\[\(]p\. \d+[\]\)]') #Page number text
# pattern = re.compile(r'\n\n\n+') #Consecutive whitespaces
# pattern = re.compile(r'\W-\n\n') #Non-oordafbrekingen
# pattern = re.compile(r'-\n\n') #Woordafbrekingen
# pattern = re.compile(r'([^\.!?:;])(\n\n)') #paragrafen die zijn afgebroken middenin een zin - eindigt niet met .!?:;
# pattern = re.compile(r'\n\n\s+') #Consecutive whitespaces

appendedText = re.sub(r'\[.*?\]', '', fileContent) # Remove text in square brackets
appendedText = re.sub(r'\'', '', fileContent) # remove aposotrophes (')

print(appendedText)

# Write to text file
# Open a file and store contents
textFile = open('G:\Dropbox\Dropbox\Personal\Projects\RapGot\Lyrics.txt', encoding="utf8", mode='w')
textFile.truncate(0)
textFile.write(appendedText)

# Close the file
textFile.close()