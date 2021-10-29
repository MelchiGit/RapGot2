import re
import os
import lyricsgenius

geniusAccessToken = ''
lyricsPath = ''
artistName = "Eminem"

# Set up Genius.com API Client
genius = lyricsgenius.Genius(geniusAccessToken)
genius.verbose = False # Turn off status messages
genius.remove_section_headers = True # Remove section headers (e.g. [Chorus]) from lyrics when searching
genius.skip_non_songs = True # Exclude hits thought to be non-songs (e.g. track lists)
genius.excluded_terms = ["(Remix)", "(Live)", "Freestyle", "(Skit)", "Intro"] # Exclude songs with these words in their title

# get most popular song titles from Eminem
rapper = genius.search_artist(artistName, max_songs=50, sort="popularity")
for song in rapper.songs:
    print(song.title)

    fileContent = song.lyrics

    appendedText = re.sub(r'\[.*?\]', '', fileContent)  # Remove text in square brackets
    appendedText = re.sub(r'[\'\"]', '', appendedText)  # remove aposotrophes (' & ")

    songTitle = song.title
    appendedTitle = re.sub(r'[\'\"\\/.,<>]', '', songTitle)  # remove aposotrophes (' & ")

    # Write to text file
    # Open a file and store contents
    if not os.path.exists(lyricsPath + song.artist):
        os.mkdir(lyricsPath + song.artist)
    textFile = open(lyricsPath + song.artist + '\\' + appendedTitle + '.txt', encoding="utf8", mode='w+')
    textFile.truncate(0)
    textFile.write(appendedText)

    # Close the file
    textFile.close()