'''
Anilist.py
Handles all of the connections to Anilist.
'''

import requests
import aiohttp
import difflib
import traceback
import pprint
import asyncio
ANICLIENT = ''
ANISECRET = ''

session = aiohttp.ClientSession()

try:
    import Config
    ANICLIENT = Config.aniclient
    ANISECRET = Config.anisecret
except ImportError:
    pass

access_token = ''

escape_table = {
     "&": " ",
     "\'": "\\'",
     '\"': '\\"',
     '/': ' ',
     '-': ' ',
     '!': '\!'
     }

#Anilist's database doesn't like weird symbols when searching it, so you have to escape or replace a bunch of stuff.
def escape(text):
     return "".join(escape_table.get(c,c) for c in text)

def getSynonyms(request):
    synonyms = []
    
    synonyms.append(request['title_english']) if request['title_english'] else None
    synonyms.append(request['title_romaji']) if request['title_romaji'] else None
    synonyms.extend(request['synonyms']) if request['synonyms'] else None

    return synonyms
    
#Sets up the connection to Anilist. You need a token to get stuff from them, which expires every hour.
async def setup():
    print('Setting up AniList')
    loop = asyncio.get_event_loop()
    try: 
        async with session.post('https://anilist.co/api/auth/access_token', params={'grant_type':'client_credentials', 'client_id':ANICLIENT, 'client_secret':ANISECRET}) as resp:
            request = await resp.json()
            global access_token
            access_token = request['access_token']
    except Exception as e:
        print('Error getting Anilist token: '+ e)

#Returns the closest anime (as a Json-like object) it can find using the given searchtext
async def getAnimeDetails(searchText):
    
    try:
        htmlSearchText = escape(searchText)

        async with session.get("https://anilist.co/api/anime/search/" + htmlSearchText, params={'access_token':access_token}, timeout=10) as resp:          
            if resp.status == 401:
                await setup()
                request = await session.get("https://anilist.co/api/anime/search/" + htmlSearchText, params={'access_token':access_token}, timeout=10)
            
            request = await resp.json()
            
            #Of the given list of shows, we try to find the one we think is closest to our search term
            closestAnime = getClosestAnime(searchText, request)

            if closestAnime:
                fullDetails = await getFullAnimeDetails(closestAnime['id'])
                return fullDetails
            else:
                return None
            
    except Exception as e:
        traceback.print_exc()
        return None

#Returns the anime details based on an id
def getAnimeDetailsById(animeID):
    try:
        return getFullAnimeDetails(animeID)
    except Exception as e:
        return None

#Gets the "full" anime details (which aren't displayed when we search using the basic function). Gives us cool data like time until the next episode is aired.
async def getFullAnimeDetails(animeID):
    try:
        async with session.get("https://anilist.co/api/anime/" + str(animeID), params={'access_token':access_token}, timeout=10) as resp:
            if resp.status == 401:
                await setup()
                resp = await session.get("https://anilist.co/api/anime/" + str(animeID), params={'access_token':access_token}, timeout=10)
                
            request = await resp.json()
            if resp.status == 200:
                return request
            else:
                return None
    except Exception as e:
        #traceback.print_exc()
        return None

#Given a list, it finds the closest anime series it can.
def getClosestAnime(searchText, animeList):
    try:
        animeNameList = []
        animeNameListNoSyn = []

        #For each anime series, add all the titles/synonyms to an array and do a fuzzy string search to find the one closest to our search text.
        #We also fill out an array that doesn't contain the synonyms. This is to protect against shows with multiple adaptations and similar synonyms (e.g. Haiyore Nyaruko-San)
        for anime in animeList:
            animeNameList.append(anime['title_english'].lower())
            animeNameList.append(anime['title_romaji'].lower())

            animeNameListNoSyn.append(anime['title_english'].lower())
            animeNameListNoSyn.append(anime['title_romaji'].lower())

            for synonym in anime['synonyms']:
                 animeNameList.append(synonym.lower())
        
        closestNameFromList = difflib.get_close_matches(searchText.lower(), animeNameList, 1, 0.95)[0]
        
        for anime in animeList:
            if (anime['title_english'].lower() == closestNameFromList.lower()) or (anime['title_romaji'].lower() == closestNameFromList.lower()):
                return anime
            else:
                for synonym in anime['synonyms']:
                    if (synonym.lower() == closestNameFromList.lower()) and (synonym.lower() not in animeNameListNoSyn):
                        return anime

        return None
    except:
        #traceback.print_exc()
        return None

#Makes a search for a manga series using a specific author
async def getMangaWithAuthor(searchText, authorName):
    try:
        htmlSearchText = escape(searchText)
        
        async with session.get("https://anilist.co/api/manga/search/" + htmlSearchText, params={'access_token':access_token}, timeout=10) as resp:
            if resp.status == 401:
                await setup()
                resp = await session.get("https://anilist.co/api/manga/search/" + htmlSearchText, params={'access_token':access_token}, timeout=10)

            
            request = await resp.json()
            closestManga = getListOfCloseManga(searchText, request)
            fullMangaList = []

            for manga in closestManga:
                try:
                    async with session.get("https://anilist.co/api/manga/" + str(manga['id']) + "/staff", params={'access_token':access_token}, timeout=10) as fullManga:
                        if fullManga.status == 401:
                            await setup()
                            fullManga = await session.get("https://anilist.co/api/manga/" + str(manga['id']) + "/staff", params={'access_token':access_token}, timeout=10)    

                        fullMangaJson = await fullManga.json()   
                        fullMangaList.append(fullMangaJson)
                except:
                    pass

            potentialHits = []
            for manga in fullMangaList:
                for staff in manga['staff']:
                    isRightName = True
                    fullStaffName = staff['name_first'] + ' ' + staff['name_last']
                    authorNamesSplit = authorName.split(' ')

                    for name in authorNamesSplit:
                        if not (name.lower() in fullStaffName.lower()):
                            isRightName = False

                    if isRightName:
                        potentialHits.append(manga)

            if potentialHits:
                return getClosestManga(searchText, potentialHits)

            return None
        
    except Exception as e:
        traceback.print_exc()
        return None

def getLightNovelDetails(searchText):
    return getMangaDetails(searchText, True)

#Returns the closest manga series given a specific search term
async def getMangaDetails(searchText, isLN=False):
    try:
        htmlSearchText = escape(searchText)
        async with session.get ("https://anilist.co/api/manga/search/" + htmlSearchText, params={'access_token':access_token}, timeout=10) as resp:
            if resp.status == 401:
                await setup()
                resp = await session.get("https://anilist.co/api/manga/search/" + htmlSearchText, params={'access_token':access_token}, timeout=10)
            
            request = await resp.json()
            closestManga = getClosestManga(searchText, request, isLN)

            if (closestManga is not None):
                response = await session.get("https://anilist.co/api/manga/" + str(closestManga['id']), params={'access_token':access_token}, timeout=10)
                return await response.json()
            else:
                return None
        
    except Exception as e:
        traceback.print_exc()
        
        return None

#Returns the closest manga series given an id
async def getMangaDetailsById(mangaId):
    try:
        async with session.get("https://anilist.co/api/manga/" + str(mangaId), params={'access_token':access_token}, timeout=10) as resp:
            request = await resp.json()
            return request
    except Exception as e:
        
        return None

#Used to determine the closest manga to a given search term in a list
def getListOfCloseManga(searchText, mangaList):
    try:
        ratio = 0.90
        returnList = []
        
        for manga in mangaList:
            alreadyExists = False
            for thing in returnList:
                if int(manga['id']) == int(thing['id']):
                    alreadyExists = True
                    break
            if (alreadyExists):
                continue
            
            if round(difflib.SequenceMatcher(lambda x: x == "", manga['title_english'].lower(), searchText.lower()).ratio(), 3) >= ratio:
                returnList.append(manga)
            elif round(difflib.SequenceMatcher(lambda x: x == "", manga['title_romaji'].lower(), searchText.lower()).ratio(), 3) >= ratio:
                returnList.append(manga)
            elif not (manga['synonyms'] is None):
                for synonym in manga['synonyms']:
                    if round(difflib.SequenceMatcher(lambda x: x == "", synonym.lower(), searchText.lower()).ratio(), 3) >= ratio:
                        returnList.append(manga)
                        break
        return returnList
    except Exception as e:
        traceback.print_exc()
        return None

#Used to determine the closest manga to a given search term in a list
def getClosestManga(searchText, mangaList, isLN=False):
    try:
        mangaNameList = []

        for manga in mangaList:
            if isLN and 'novel' not in manga['type'].lower():
                mangaList.remove(manga)
            elif not isLN and 'novel' in manga['type'].lower():
                mangaList.remove(manga)
        
        for manga in mangaList:
            if isLN and 'novel' not in manga['type'].lower():
                mangaList.remove(manga)
            elif not isLN and 'novel' in manga['type'].lower():
                mangaList.remove(manga)

        for manga in mangaList:
            mangaNameList.append(manga['title_english'].lower())
            mangaNameList.append(manga['title_romaji'].lower())

            for synonym in manga['synonyms']:
                 mangaNameList.append(synonym.lower())

        closestNameFromList = difflib.get_close_matches(searchText.lower(), mangaNameList, 1, 0.90)[0]
        
        for manga in mangaList:
            if not ('one shot' in manga['type'].lower()):
                if (manga['title_english'].lower() == closestNameFromList.lower()) or (manga['title_romaji'].lower() == closestNameFromList.lower()):
                    return manga

        for manga in mangaList:                
            for synonym in manga['synonyms']:
                if synonym.lower() == closestNameFromList.lower():
                    return manga

        return None
    except Exception as e:
        #traceback.print_exc()
        return None

loop = asyncio.get_event_loop()
loop.run_until_complete(setup())
