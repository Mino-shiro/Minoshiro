import asyncio
import math

import roboragi.Anilist as Anilist
import roboragi.DatabaseHandler as DatabaseHandler
import roboragi.MAL as MAL


async def setup():
    end_index = input("How many anime titles do you want?  ")
    # result = await top_n_by_popularity('anime', end_index)
    result2 = await top_n_by_popularity('manga', end_index)
    result3 = await top40ByGenre('manga')


async def top40ByGenre(medium):
    errorList = []
    genres = await Anilist.getGenres(medium)
    for entry in genres:
        top40 = await Anilist.GetTop40ByGenre(medium, entry['genre'])
        for entry in top40:
            print("Working on anilist id: {}".format(entry['id']))
            try:
                DatabaseHandler.PopulateCache('anilist{}'.format(medium),
                                              entry)
            except Exception as e:
                print("{} failed with exception {}".format(entry['id'], e))
            try:
                animeName = None
                if entry['title_romaji']:
                    animeName = entry['title_romaji']
                else:
                    animeName = entry['title_english']
                if medium == 'anime':
                    malanime = await MAL.getAnimeDetails(animeName)
                elif medium == 'manga':
                    malanime = await MAL.getMangaDetails(animeName)
                if malanime:
                    try:
                        DatabaseHandler.PopulateCache('mal{}'.format(medium),
                                                      malanime)
                    except Exception as e:
                        print("{} failed with exception {}".format(
                            malanime['id'], e))
            except Exception as e:
                print("debug 1 error: {}".format(e))


async def top_n_by_popularity(medium, n):
    count = 1
    final_page = math.ceil(float(n) / float(40))
    while count < final_page:
        try:
            print("\n\n-------------Starting page {}------------\n\n".format(
                count))
            page_entries = await Anilist.get_page_by_popularity(medium, count)
            for entry in page_entries:
                print("Working on anilist id: {}".format(entry['id']))
                try:
                    DatabaseHandler.PopulateCache('anilist{}'.format(medium),
                                                  entry)
                except Exception as e:
                    print(
                        "{} failed with exception {}\n".format(entry['id'], e))
                try:
                    animeName = None
                    if entry['title_romaji']:
                        animeName = entry['title_romaji']
                    else:
                        animeName = entry['title_english']
                    if medium == 'anime':
                        malanime = await MAL.getAnimeDetails(animeName)
                    elif medium == 'manga':
                        malanime = await MAL.getMangaDetails(animeName)
                    if malanime:
                        try:
                            DatabaseHandler.PopulateCache(
                                'mal{}'.format(medium), malanime)
                        except Exception as e:
                            print("{} failed with exception {}\n".format(
                                malanime['id'], e))
                except Exception as e:
                    print("debug 1 error: {}\n".format(e))
            count += 1
        except Exception as e:
            count += 1
            print(e)


loop = asyncio.get_event_loop()
loop.run_until_complete(setup())
