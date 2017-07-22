from pyquery import PyQuery as pq
import aiohttp
import difflib
import traceback
import pprint
import collections

BASE_URL = "http://www.anime-planet.com"

session = aiohttp.ClientSession()

def sanitiseSearchText(searchText):
    return searchText.replace('(TV)', 'TV')

async def getAnimeURL(searchText):
    try:
        searchText = sanitiseSearchText(searchText)
        
        async with session.get(BASE_URL + "/anime/all?name=" + searchText.replace(" ", "%20"), timeout=10) as resp:
            html = await resp.text()
            ap = pq(html)
            animeList = []

            #If it's taken us to the search page
            if ap.find('.cardDeck.pure-g.cd-narrow[data-type="anime"]'):
                for entry in ap.find('.card.pure-1-6'):
                    entryTitle = pq(entry).find('h4').text()
                    entryURL = pq(entry).find('a').attr('href')
                    
                    anime = {}
                    anime['title'] = entryTitle
                    anime['url'] = BASE_URL + entryURL
                    animeList.append(anime)

                closestName = difflib.get_close_matches(searchText.lower(), [x['title'].lower() for x in animeList], 1, 0.85)[0]
                closestURL = ''
                
                for anime in animeList:
                    if anime['title'].lower() == closestName:
                        return anime['url']
                
            #Else if it's taken us right to the series page, get the url from the meta tag
            else:
                return ap.find("meta[property='og:url']").attr('content')
            return None
            
    except Exception as e:
        return None

#Probably doesn't need to be split into two functions given how similar they are, but it might be worth keeping separate for the sake of issues between anime/manga down the line
async def getMangaURL(searchText, authorName=None):
    try:
        if authorName:
            async with sessions.get(BASE_URL + "/manga/all?name=" + searchText.replace(" ", "%20") + '&author=' + authorName.replace(" ", "%20"), timeout=10) as resp:
                html = await resp.text()
            if "No results found" in html:
                rearrangedAuthorNames = collections.deque(authorName.split(' '))
                rearrangedAuthorNames.rotate(-1)
                rearrangedName = ' '.join(rearrangedAuthorNames)
                async with session.get(BASE_URL + "/manga/all?name=" + searchText.replace(" ", "%20") + '&author=' + rearrangedName.replace(" ", "%20"), timeout=10) as resp:
                    html = await resp.text()
            
        else:
            async with session.get(BASE_URL + "/manga/all?name=" + searchText.replace(" ", "%20"), timeout=10) as resp:
                html = await resp.text()
            
        ap = pq(html)

        mangaList = []

        #If it's taken us to the search page
        if ap.find('.cardDeck.pure-g.cd-narrow[data-type="manga"]'):
            for entry in ap.find('.card.pure-1-6'):
                entryTitle = pq(entry).find('h4').text()
                entryURL = pq(entry).find('a').attr('href')
                
                manga = {}
                manga['title'] = entryTitle
                manga['url'] = BASE_URL + entryURL
                mangaList.append(manga)

            if authorName:
                authorName = authorName.lower()
                authorName = authorName.split(' ')

                for manga in mangaList:
                    manga['title'] = manga['title'].lower()
                    
                    for name in authorName:
                        manga['title'] = manga['title'].replace(name, '')
                    manga['title'] = manga['title'].replace('(', '').replace(')', '').strip()
                
            closestName = difflib.get_close_matches(searchText.lower(), [x['title'].lower() for x in mangaList], 1, 0.85)[0]
            closestURL = ''
            
            for manga in mangaList:
                if manga['title'].lower() == closestName:
                    return manga['url']
            
        #Else if it's taken us right to the series page, get the url from the meta tag
        else:
            return ap.find("meta[property='og:url']").attr('content')
        return None
            
    except:
        return None

def getAnimeURLById(animeId):
    return 'http://www.anime-planet.com/anime/' + str(animeId)

def getMangaURLById(mangaId):
    return 'http://www.anime-planet.com/manga/' + str(mangaId)