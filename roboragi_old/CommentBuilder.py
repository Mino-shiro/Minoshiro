'''
CommentBuilder.py
Takes the data given to it by search and formats it into a comment
'''

import re
import traceback
from os import linesep

from discord import Embed

import roboragi_old.DatabaseHandler as DatabaseHandler
import roboragi_old.Discord as Discord


# Removes the (Source: MAL) or (Written by X) bits from the decriptions in the databases
def cleanupDescription(desc):
    for match in re.finditer("([\[\<\(](.*?)[\]\>\)])", desc, re.S):
        if 'ource' in match.group(1).lower():
            desc = desc.replace(match.group(1), '')
        if 'MAL' in match.group(1):
            desc = desc.replace(match.group(1), '')

    for match in re.finditer("([\<](.*?)[\>])", desc, re.S):
        if 'br' in match.group(1).lower():
            desc = desc.replace(match.group(1), '')

    reply = ''
    for i, line in enumerate(
            linesep.join([s for s in desc.splitlines() if s]).splitlines()):
        if i is not 0:
            reply += '\n'
        reply += line + '\n'
    return reply


# Builds an anime comment from MAL/Anilist data
def buildAnimeComment(isExpanded, mal, ani, ap, anidb):
    try:
        comment = ''

        title = None
        jTitle = None

        cType = None

        malURL = None
        aniURL = None
        apURL = ap
        anidbURL = anidb

        youtubeTrailer = None

        status = None
        episodes = None
        genres = []

        countdown = None
        nextEpisode = None

        desc = None

        if mal:
            desc = mal['synopsis']

            if mal['type']:
                cType = mal['type']

            malURL = 'http://myanimelist.net/anime/' + str(mal['id'])

        if ani is not None:
            title = ani['title_romaji']
            aniURL = 'http://anilist.co/anime/' + str(ani['id'])

            try:
                cType = ani['type']
                desc = ani['description']
            except:
                pass

            status = ani['airing_status'].title()

            try:
                if ani['title_japanese'] is not None:
                    jTitle = ani['title_japanese']

                if ani['youtube_id'] is not None:
                    youtubeTrailer = ani['youtube_id']

                if ani['total_episodes'] is not None:
                    if ani['total_episodes'] == 0:
                        episodes = 'Unknown'
                    else:
                        episodes = ani['total_episodes']

                if ani['genres'] is not None:
                    genres = ani['genres']

                if ani['airing'] is not None:
                    countdown = ani['airing']['countdown']
                    nextEpisode = ani['airing']['next_episode']
            except:
                print('No full details for Anilist')

        stats = DatabaseHandler.getRequestStats(title, 'Anime')

        if ani is not None:
            stats = DatabaseHandler.getRequestStats(ani['title_romaji'],
                                                    'Anime')

        # ---------- BUILDING THE COMMENT ----------#

        # ----- TITLE -----#
        comment += '**' + title.strip() + '** - \n\n'

        # ----- LINKS -----#
        urlComments = []

        if malURL is not None:
            urlComments.append(malURL)
        if apURL is not None:
            urlComments.append(apURL)
        if ani is not None:
            urlComments.append(aniURL)
        if anidbURL is not None:
            urlComments.append(anidbURL)

        for i, link in enumerate(urlComments):
            if i is not 0:
                comment += '\n\n'
            comment += link

        # ----- JAPANESE TITLE -----#
        if (isExpanded):
            if jTitle is not None:
                comment += '\n\n'

                splitJTitle = jTitle.split()
                for i, word in enumerate(splitJTitle):
                    if not (i == 0):
                        comment += ' '
                    comment += word

        # ----- INFO LINE -----#
        if (isExpanded):
            comment += '\n\n('

            if cType:
                comment += '**' + cType + '** | '

            comment += '**Status:** ' + status

            if cType != 'Movie':
                comment += ' | **Episodes:** ' + str(episodes)

            comment += ' | **Genres:** '
        else:
            comment += '\n\n('

            if cType:
                comment += cType + ' | '

            comment += 'Status: ' + status

            if cType != 'Movie':
                comment += ' | Episodes: ' + str(episodes)

            comment += ' | Genres: '

        if not (genres == []):
            for i, genre in enumerate(genres):
                if i is not 0:
                    comment += ', '
                comment += genre
        else:
            comment += 'None'

        if (isExpanded) and (stats is not None):
            comment += '  \n**Stats:** ' + str(
                stats['total']) + ' requests across ' + str(
                stats['uniqueSubreddits']) + ' server(s)) - ' + str(
                round(stats['totalAsPercentage'], 3)) + '% of all requests'
        else:
            comment += ')'

        # ----- EPISODE COUNTDOWN -----#
        if (countdown is not None) and (nextEpisode is not None):
            # countdown is given to us in seconds
            days, countdown = divmod(countdown, 24 * 60 * 60)
            hours, countdown = divmod(countdown, 60 * 60)
            minutes, countdown = divmod(countdown, 60)

            comment += '\n\n(Episode ' + str(nextEpisode) + ' airs in ' + str(
                days) + ' days, ' + str(hours) + ' hours, ' + str(
                minutes) + ' minutes)'

        # ----- DESCRIPTION -----#
        if (isExpanded):
            comment += '\n\n' + cleanupDescription(desc)

        # ----- END -----#
        receipt = '(A) Request successful: ' + title + ' - '
        if malURL is not None:
            receipt += 'MAL '
        if apURL is not None:
            receipt += 'AP '
        if ani is not None:
            receipt += 'ANI '
        if anidbURL is not None:
            receipt += 'ADB '
        print(receipt.encode('utf8'))

        # We return the title/comment separately so we can track if multiples of the same comment have been requests (e.g. {Nisekoi}{Nisekoi}{Nisekoi})
        dictToReturn = {}
        dictToReturn['title'] = title
        dictToReturn['comment'] = comment

        return dictToReturn
    except Exception as e:
        print("Error creating embed: {}\n".format(e))
        # traceback.print_exc()
        return None


# Builds a manga comment from MAL/Anilist/MangaUpdates data
def buildMangaComment(isExpanded, mal, ani, mu, ap):
    try:
        comment = ''

        title = None
        jTitle = None

        cType = None

        malURL = None
        aniURL = None
        muURL = mu
        apURL = ap

        status = None
        chapters = None
        volumes = None
        genres = []

        desc = None

        if not (mal is None):
            title = mal['title']
            malURL = 'http://myanimelist.net/manga/' + str(mal['id'])
            desc = mal['synopsis']
            status = mal['status']

            cType = mal['type']

            try:
                if (int(mal['chapters']) == 0):
                    chapters = 'Unknown'
                else:
                    chapters = mal['chapters']
            except:
                chapters = 'Unknown'

            try:
                volumes = mal['volumes']
            except:
                volumes = 'Unknown'

        if ani is not None:
            if title is None:
                title = ani['title_english']
            aniURL = 'http://anilist.co/manga/' + str(ani['id'])
            desc = ani['description']
            status = ani['publishing_status'].title()

            cType = ani['type']

            try:
                if ani['title_japanese'] is not None:
                    jTitle = ani['title_japanese']

                if ani['total_chapters'] is not None:
                    if ani['total_chapters'] == 0:
                        chapters = 'Unknown'
                    else:
                        chapters = ani['total_chapters']

                if ani['total_volumes'] is not None:
                    volumes = ani['total_volumes']
                else:
                    volumes = 'Unknown'

                if ani['genres'] is not None:
                    genres = ani['genres']

            except Exception as e:
                print(e)

        stats = DatabaseHandler.getRequestStats(title, 'Manga')

        # ---------- BUILDING THE COMMENT ----------#

        # ----- TITLE -----#
        comment += '**' + title.strip() + '** - \n\n'

        # ----- LINKS -----#
        urlComments = []

        if malURL is not None:
            urlComments.append(malURL)
        if apURL is not None:
            urlComments.append(apURL)
        if aniURL is not None:
            urlComments.append(aniURL)
        if muURL is not None:
            urlComments.append(muURL)

        for i, link in enumerate(urlComments):
            if i is not 0:
                comment += '\n\n'
            comment += link

        comment += '\n\n'

        # ----- JAPANESE TITLE -----#
        if (isExpanded):
            if jTitle is not None:
                comment += '\n\n'

                splitJTitle = jTitle.split()
                for i, word in enumerate(splitJTitle):
                    if not (i == 0):
                        comment += ' '
                    comment += word

        # ----- INFO LINE -----#

        if (isExpanded):
            comment += '\n\n('

            if cType:
                if cType == 'Novel':
                    cType = 'Light Novel'

                comment += '**' + cType + '** | '

            comment += '**Status:** ' + status

            if (cType != 'Light Novel'):
                if str(chapters) is not 'Unknown':
                    comment += ' | **Chapters:** ' + str(chapters)
            else:
                comment += ' | **Volumes:** ' + str(volumes)

            if genres:
                comment += ' | **Genres:** '
        else:
            comment += '\n\n('

            if cType:
                if cType == 'Novel':
                    cType = 'Light Novel'

                comment += cType + ' | '

            comment += 'Status: ' + status

            if (cType != 'Light Novel'):
                if str(chapters) is not 'Unknown':
                    comment += ' | Chapters: ' + str(chapters)
            else:
                comment += ' | Volumes: ' + str(volumes)

            if genres:
                comment += ' | Genres: '

        if genres:
            for i, genre in enumerate(genres):
                if i is not 0:
                    comment += ', '
                comment += genre

        if (isExpanded) and (stats is not None):
            comment += '  \n**Stats:** ' + str(
                stats['total']) + ' requests across ' + str(
                stats['uniqueSubreddits']) + ' server(s)) - ' + str(
                round(stats['totalAsPercentage'], 3)) + '% of all requests'
        else:
            comment += ')'

        # ----- DESCRIPTION -----#
        if (isExpanded):
            comment += '\n\n' + cleanupDescription(desc)

        # ----- END -----#
        receipt = '(M) Request successful: ' + title + ' - '
        if malURL is not None:
            receipt += 'MAL '
        if ap is not None:
            receipt += 'AP '
        if ani is not None:
            receipt += 'ANI '
        if muURL is not None:
            receipt += 'MU '
        print(receipt.encode('utf8'))

        dictToReturn = {}
        dictToReturn['title'] = title
        dictToReturn['comment'] = comment

        return dictToReturn
    except:
        traceback.print_exc()
        return None


# Builds a manga comment from MAL/Anilist/MangaUpdates data
def buildLightNovelComment(isExpanded, mal, ani, nu, lndb):
    try:
        comment = ''

        title = None
        jTitle = None

        cType = None

        malURL = None
        aniURL = None
        nuURL = nu
        lndbURL = lndb

        status = None
        chapters = None
        volumes = None
        genres = []

        desc = None

        if not (mal is None):
            title = mal['title']
            malURL = 'http://myanimelist.net/manga/' + str(mal['id'])
            desc = mal['synopsis']
            status = mal['status']

            cType = mal['type']

            try:
                if (int(mal['chapters']) == 0):
                    chapters = 'Unknown'
                else:
                    chapters = mal['chapters']
            except:
                chapters = 'Unknown'

            try:
                volumes = mal['volumes']
            except:
                volumes = 'Unknown'

        if ani is not None:
            if title is None:
                title = ani['title_english']
            aniURL = 'http://anilist.co/manga/' + str(ani['id'])
            desc = ani['description']
            status = ani['publishing_status'].title()

            cType = ani['type']

            try:
                if ani['title_japanese'] is not None:
                    jTitle = ani['title_japanese']

                if ani['total_chapters'] is not None:
                    if ani['total_chapters'] == 0:
                        chapters = 'Unknown'
                    else:
                        chapters = ani['total_chapters']

                if ani['total_volumes'] is not None:
                    volumes = ani['total_volumes']
                else:
                    volumes = 'Unknown'

                if ani['genres'] is not None:
                    genres = ani['genres']

            except Exception as e:
                print(e)

        stats = DatabaseHandler.getRequestStats(title, 'LN')

        # ---------- BUILDING THE COMMENT ----------#

        # ----- TITLE -----#
        comment += '**' + title.strip() + '** -\n\n'

        # ----- LINKS -----#
        urlComments = []

        if malURL is not None:
            urlComments.append(malURL)
        if aniURL is not None:
            urlComments.append(aniURL)
        if nuURL is not None:
            urlComments.append(nuURL)
        if lndbURL is not None:
            urlComments.append(lndbURL)

        for i, link in enumerate(urlComments):
            if i is not 0:
                comment += '\n '
            comment += link

        comment += '\n\n'

        # ----- JAPANESE TITLE -----#
        if (isExpanded):
            if jTitle is not None:
                comment += '\n\n'

                splitJTitle = jTitle.split()
                for i, word in enumerate(splitJTitle):
                    if not (i == 0):
                        comment += ' '
                    comment += word

        # ----- INFO LINE -----#

        if (isExpanded):
            comment += '\n\n('

            if cType:
                if cType == 'Novel':
                    cType = 'Light Novel'

                comment += '**' + cType + '** | '

            comment += '**Status:** ' + status

            if (cType != 'Light Novel'):
                if str(chapters) is not 'Unknown':
                    comment += ' | **Chapters:** ' + str(chapters)
            else:
                comment += ' | **Volumes:** ' + str(volumes)

            if genres:
                comment += ' | **Genres:** '
        else:
            comment += '\n\n('

            if cType:
                if cType == 'Novel':
                    cType = 'Light Novel'

                comment += cType + ' | '

            comment += 'Status: ' + status

            if (cType != 'Light Novel'):
                if str(chapters) is not 'Unknown':
                    comment += ' | Chapters: ' + str(chapters)
            else:
                comment += ' | Volumes: ' + str(volumes)

            if genres:
                comment += ' | Genres: '

        if genres:
            for i, genre in enumerate(genres):
                if i is not 0:
                    comment += ', '
                comment += genre

        if (isExpanded) and (stats is not None):
            comment += '  \n**Stats:** ' + str(
                stats['total']) + ' requests across ' + str(
                stats['uniqueSubreddits']) + ' subreddit(s)^) ^- ^' + str(
                round(stats['totalAsPercentage'], 3)) + '% ^of ^all ^requests'
        else:
            comment += ')'

        # ----- DESCRIPTION -----#
        if (isExpanded):
            comment += '\n\n' + cleanupDescription(desc)

        # ----- END -----#
        receipt = '(LN) Request successful: ' + title + ' - '
        if malURL is not None:
            receipt += 'MAL '
        if ani is not None:
            receipt += 'ANI '
        if nuURL is not None:
            receipt += 'MU '
        if lndbURL is not None:
            receipt += 'LNDB '
        print(receipt.encode('utf8'))

        dictToReturn = {}
        dictToReturn['title'] = title
        dictToReturn['comment'] = comment

        return dictToReturn
    except:
        traceback.print_exc()
        return None


# Builds a stats comment. If it is basic stats the default server id is the Discordoragi help server
def buildStatsComment(server=None, username=None,
                      serverID="171004769069039616"):
    try:
        statComment = ''
        receipt = '(S) Request successful: Stats'

        if username:
            userStats = DatabaseHandler.getUserStats(username)

            if userStats:
                statComment += 'Some stats on ' + username + ':\n\n'
                statComment += '- **' + str(userStats[
                                                'totalUserComments']) + '** total comments searched (' + str(
                    round(userStats['totalUserCommentsAsPercentage'],
                          3)) + '% of all comments)\n'
                statComment += '- **' + str(userStats[
                                                'totalUserRequests']) + '** requests made (' + str(
                    round(userStats['totalUserRequestsAsPercentage'],
                          3)) + '% of all requests and #' + str(
                    userStats['overallRequestRank']) + ' overall)\n'
                statComment += '- **' + str(userStats[
                                                'uniqueRequests']) + '** unique anime/manga requested\n'
                statComment += '- **/r/' + str(userStats[
                                                   'favouriteSubreddit']) + '** is their favourite server with ' + str(
                    userStats[
                        'favouriteSubredditCount']) + ' requests (' + str(
                    round(userStats['favouriteSubredditCountAsPercentage'],
                          3)) + '% of the server\'s requests)\n'
                statComment += '\n'
                statComment += 'Their most frequently requested anime/manga overall are:\n\n'

                for i, request in enumerate(userStats['topRequests']):
                    statComment += str(i + 1) + '. **' + str(
                        request[0]) + '** (' + str(request[1]) + ' - ' + str(
                        request[2]) + ' requests)  \n'
            else:
                statComment += '/u/' + str(
                    username) + ' hasn\'t used Roboragi yet.'

            receipt += ' - /u/' + username
        elif server:
            serverID = server.id
            server = str(server)
            serverStats = DatabaseHandler.getSubredditStats(server.lower())

            if serverStats:
                statComment += '**' + server + ' Stats**\n\n'

                statComment += 'I\'ve searched through ' + str(
                    serverStats['totalComments'])
                statComment += ' unique comments on ' + server
                statComment += ' and fulfilled a total of ' + str(
                    serverStats['total']) + ' requests, '
                statComment += 'representing ' + str(
                    round(serverStats['totalAsPercentage'],
                          2)) + '% of all requests. '
                statComment += 'A total of ' + str(serverStats[
                                                       'uniqueNames']) + ' unique anime/manga have been requested here, '
                statComment += 'with a mean value of ' + str(
                    round(serverStats['meanValuePerRequest'],
                          3)) + ' requests/show'
                statComment += ' and a standard deviation of ' + str(
                    round(serverStats['standardDeviation'], 3)) + '.'

                statComment += '\n\n'

                statComment += 'The most frequently requested anime/manga on this server are:\n\n'

                for i, request in enumerate(serverStats['topRequests']):
                    statComment += str(i + 1) + '. **' + str(
                        request[0]) + '** (' + str(request[1]) + ' - ' + str(
                        request[2]) + ' requests)\n'

                statComment += '\n'

                statComment += 'The most frequent requesters on this server are:\n\n'
                for i, requester in enumerate(serverStats['topRequesters']):
                    statComment += str(i + 1) + '. /u/' + str(
                        requester[0]) + ' (' + str(
                        requester[1]) + ' requests)\n'

            else:
                statComment += 'There have been no requests on ' + str(
                    server) + ' yet.'

            receipt += ' - ' + server
        else:
            basicStats = DatabaseHandler.getBasicStats(serverID)

            # The overall stats section
            statComment += '**Overall Stats**\n\n'

            statComment += 'I\'ve searched through ' + str(
                basicStats['totalComments'])
            statComment += ' unique comments and fulfilled a total of ' + str(
                basicStats['total'])
            statComment += ' requests across ' + str(
                basicStats['uniqueSubreddits']) + ' unique server(s). '
            statComment += 'A total of ' + str(basicStats['uniqueNames'])
            statComment += ' unique anime/manga have been requested, with a mean value of ' + str(
                round(basicStats['meanValuePerRequest'], 3))
            statComment += ' requests/show and a standard deviation of ' + str(
                round(basicStats['standardDeviation'], 3)) + '.'

            statComment += '\n\n'

            statComment += 'The most frequently requested anime/manga overall are:\n\n'

            for i, request in enumerate(basicStats['topRequests']):
                statComment += str(i + 1) + '. **' + str(
                    request[0]) + '** (' + str(request[1]) + ' - ' + str(
                    request[2]) + ' requests)\n'

            statComment += '\n'

            statComment += 'The most frequent requesters overall are:  \n'
            for i, requester in enumerate(basicStats['topRequesters']):
                statComment += str(i + 1) + '. ' + str(
                    Discord.getUsernameFromID(requester[0], )) + ' (' + str(
                    requester[1]) + ' requests)  \n'

            statComment += '\n'
            receipt += ' - Basic'

        print(receipt.encode('utf8'))
        return statComment
    except:
        traceback.print_exc()
        return None


# Builds an embed using the same data
def buildAnimeEmbed(isExpanded, mal, ani, ap, anidb):
    try:
        comment = ''
        descComment = ''
        title = None
        jTitle = None

        cType = None

        malimage = ''
        malURL = None
        aniURL = None
        apURL = ap
        anidbURL = anidb

        youtubeTrailer = None

        status = None
        episodes = None
        genres = []

        countdown = None
        nextEpisode = None

        desc = None

        if mal:
            desc = mal['synopsis']

            if mal['type']:
                cType = mal['type']

            malURL = 'http://myanimelist.net/anime/' + str(mal['id'])
            if mal['title']:
                title = mal['title']

            if mal['english']:
                title = mal['english']

            if mal['image']:
                malimage = mal['image']

            if mal['status']:
                status = mal['status']
        if ani is not None:
            title = ani['title_romaji']
            aniURL = 'http://anilist.co/anime/' + str(ani['id'])

            try:
                cType = ani['type']
                desc = ani['description']
            except:
                pass

            if status is None:
                try:
                    status = ani['airing_status'].title()
                except Exception as e:
                    print(e)
            try:
                if ani['title_japanese'] is not None:
                    jTitle = ani['title_japanese']

                if ani['youtube_id'] is not None:
                    youtubeTrailer = ani['youtube_id']

                if ani['total_episodes'] is not None:
                    if ani['total_episodes'] == 0:
                        episodes = 'Unknown'
                    else:
                        episodes = ani['total_episodes']

                if ani['genres'] is not None:
                    genres = ani['genres']

                if ani['airing'] is not None:
                    countdown = ani['airing']['countdown']
                    nextEpisode = ani['airing']['next_episode']
            except:
                print('No full details for Anilist')

        stats = DatabaseHandler.getRequestStats(title, 'Anime')

        if ani is not None:
            stats = DatabaseHandler.getRequestStats(ani['title_romaji'],
                                                    'Anime')

        # ---------- BUILDING THE COMMENT ----------#

        comment = ''

        # ----- LINKS -----#
        urlComments = []
        allLinks = ''

        try:
            mal_english = mal['english']
        except:
            pass

        if malURL is not None:
            urlComments.append(
                "[MAL]({})".format(sanitise_url_for_markdown(malURL)))
        if apURL is not None:
            urlComments.append(
                "[AP]({})".format(sanitise_url_for_markdown(apURL)))
        if ani is not None:
            urlComments.append(
                "[AL]({})".format(sanitise_url_for_markdown(aniURL)))
        if anidbURL is not None:
            urlComments.append(
                "[AniDB]({})".format(sanitise_url_for_markdown(anidbURL)))

        for i, link in enumerate(urlComments):
            if i is not 0:
                allLinks += ', '
            allLinks += link
        # ----- JAPANESE TITLE -----#
        if (isExpanded):
            if jTitle is not None:
                comment += '\n\n'

                splitJTitle = jTitle.split()
                for i, word in enumerate(splitJTitle):
                    if not (i == 0):
                        comment += ' '
                    comment += word

        # ----- INFO LINE -----#
        if (isExpanded):
            comment += '\n\n('

            if cType:
                comment += '**' + cType + '** | '

            comment += '**Status:** ' + status

            if cType != 'Movie':
                comment += ' | **Episodes:** ' + str(episodes)

            comment += ' | **Genres:** '
        else:
            comment += '\n\n('

            if cType:
                comment += cType + ' | '

            comment += 'Status: ' + status

            if cType != 'Movie':
                comment += ' | Episodes: ' + str(episodes)

            comment += ' | Genres: '

        if not (genres == []):
            for i, genre in enumerate(genres):
                if i is not 0:
                    comment += ', '
                comment += genre
        else:
            comment += 'None'

        if (isExpanded) and (stats is not None):
            comment += ')  \n\n**Stats:** ' + str(
                stats['total']) + ' requests across ' + str(
                stats['uniqueSubreddits']) + ' server(s)) - ' + str(
                round(stats['totalAsPercentage'], 3)) + '% of all requests'
        else:
            comment += ')'

        # ----- EPISODE COUNTDOWN -----#
        if (countdown is not None) and (nextEpisode is not None):
            # countdown is given to us in seconds
            days, countdown = divmod(countdown, 24 * 60 * 60)
            hours, countdown = divmod(countdown, 60 * 60)
            minutes, countdown = divmod(countdown, 60)

            comment += '\n\n(Episode ' + str(nextEpisode) + ' airs in ' + str(
                days) + ' days, ' + str(hours) + ' hours, ' + str(
                minutes) + ' minutes)'

        # ----- DESCRIPTION -----#
        if (isExpanded):
            descComment += cleanupDescription(desc)

        # ----- END -----#
        receipt = '(A) Request successful: ' + title + ' - '
        if malURL is not None:
            receipt += 'MAL '
        if apURL is not None:
            receipt += 'AP '
        if ani is not None:
            receipt += 'AL '
        if anidbURL is not None:
            receipt += 'ADB '
        print(receipt.encode('utf8'))
        try:
            embed = buildEmbedObject(title, allLinks, comment, malimage,
                                     isExpanded, descComment)
        except Exception as e:
            print(e)
        # We return the title/comment separately so we can track if multiples of the same comment have been requests (e.g. {Nisekoi}{Nisekoi}{Nisekoi})
        dictToReturn = {}
        dictToReturn['title'] = title
        dictToReturn['embed'] = embed
        return dictToReturn
    except Exception as e:
        print(e)
        # traceback.print_exc()
        return None


# sets up the embed for Mangas
def buildMangaEmbed(isExpanded, mal, ani, mu, ap):
    try:
        comment = ''
        descComment = ''

        title = None
        jTitle = None

        cType = None

        malimage = ''
        malURL = None
        aniURL = None
        muURL = mu
        apURL = ap

        status = None
        chapters = None
        volumes = None
        genres = []

        desc = None

        if not (mal is None):
            title = mal['title']
            malURL = 'http://myanimelist.net/manga/' + str(mal['id'])
            desc = mal['synopsis']
            status = mal['status']
            malimage = mal['image']

            cType = mal['type']

            try:
                if (int(mal['chapters']) == 0):
                    chapters = 'Unknown'
                else:
                    chapters = mal['chapters']
            except:
                chapters = 'Unknown'

            try:
                if (int(mal['volumes']) == 0):
                    volumes = 'Unknown'
                else:
                    volumes = mal['volumes']
            except:
                volumes = 'Unknown'

        if ani is not None:
            if title is None:
                title = ani['title_english']
            aniURL = 'http://anilist.co/manga/' + str(ani['id'])
            if ani['description']:
                desc = ani['description']

            try:
                status = ani['publishing_status'].title()
            except:
                pass

            cType = ani['type']

            try:
                if ani['title_japanese'] is not None:
                    jTitle = ani['title_japanese']

                if ani['total_chapters'] is not None:
                    if ani['total_chapters'] == 0:
                        chapters = 'Unknown'
                    else:
                        chapters = ani['total_chapters']

                if ani['total_volumes'] is not None:
                    if ani['total_volumes'] == 0:
                        volumes = 'Unknown'
                    else:
                        volumes = ani['total_volumes']

                if ani['genres'] is not None:
                    genres = ani['genres']

            except Exception as e:
                print(e)

        stats = DatabaseHandler.getRequestStats(title, 'Manga')

        # ---------- BUILDING THE COMMENT ----------#

        # ----- LINKS -----#
        urlComments = []
        allLinks = ''
        if malURL is not None:
            urlComments.append(
                "[MAL]({})".format(sanitise_url_for_markdown(malURL)))
        if aniURL is not None:
            urlComments.append(
                "[ANI]({})".format(sanitise_url_for_markdown(aniURL)))
        if apURL is not None:
            urlComments.append(
                "[AP]({})".format(sanitise_url_for_markdown(apURL)))
        if muURL is not None:
            urlComments.append(
                "[MU]({})".format(sanitise_url_for_markdown(muURL)))

        for i, link in enumerate(urlComments):
            if i is not 0:
                allLinks += ', '
            allLinks += link

        # ----- JAPANESE TITLE -----#
        if (isExpanded):
            if jTitle is not None:
                comment += '\n\n'

                splitJTitle = jTitle.split()
                for i, word in enumerate(splitJTitle):
                    if not (i == 0):
                        comment += ' '
                    comment += word

        # ----- INFO LINE -----#

        if (isExpanded):
            comment += '\n\n('

            if cType:
                if cType == 'Novel':
                    cType = 'Light Novel'

                comment += '**' + cType + '** | '

            comment += '**Status:** ' + status

            if (cType != 'Light Novel'):
                if str(volumes) is not 'Unknown':
                    comment += ' | **Volumes:** ' + str(volumes)
                if str(chapters) is not 'Unknown':
                    comment += ' | **Chapters:** ' + str(chapters)
            else:
                if str(volumes) is not 'Unknown':
                    comment += ' | **Volumes:** ' + str(volumes)

            if genres:
                comment += ' | **Genres:** '
        else:
            comment += '\n\n('

            if cType:
                if cType == 'Novel':
                    cType = 'Light Novel'

                comment += cType + ' | '

            comment += 'Status: ' + status

            if (cType != 'Light Novel'):
                if str(volumes) is not 'Unknown':
                    comment += ' | Volumes: ' + str(volumes)
                if str(chapters) is not 'Unknown':
                    comment += ' | Chapters: ' + str(chapters)
            else:
                if str(volumes) is not 'Unknown':
                    comment += ' | Volumes: ' + str(volumes)

            if genres:
                comment += ' | Genres: '

        if genres:
            for i, genre in enumerate(genres):
                if i is not 0:
                    comment += ', '
                comment += genre

        if (isExpanded) and (stats is not None):
            comment += ') \n\n**Stats:** ' + str(
                stats['total']) + ' requests across ' + str(
                stats['uniqueSubreddits']) + ' server(s)) - ' + str(
                round(stats['totalAsPercentage'], 3)) + '% of all requests'
        else:
            comment += ')'

        # ----- DESCRIPTION -----#
        if (isExpanded):
            descComment += cleanupDescription(desc)

        # ----- END -----#
        receipt = '(M) Request successful: ' + title + ' - '
        if malURL is not None:
            receipt += 'MAL '
        if ap is not None:
            receipt += 'AP '
        if ani is not None:
            receipt += 'AL '
        if muURL is not None:
            receipt += 'MU '
        print(receipt.encode('utf8'))

        # ----- Build embed object -----#
        try:
            embed = buildEmbedObject(title, allLinks, comment, malimage,
                                     isExpanded, descComment)
        except Exception as e:
            print(e)
        dictToReturn = {}
        dictToReturn['title'] = title
        dictToReturn['embed'] = embed

        return dictToReturn
    except Exception as e:
        print(e)
        # traceback.print_exc()
        return None


# sets up the embed for Light Novels
def buildLightNovelEmbed(isExpanded, mal, ani, nu, lndb):
    try:
        comment = ''
        descComment = ''

        title = None
        jTitle = None

        cType = None

        malimage = ''
        malURL = None
        aniURL = None
        nuURL = nu
        lndbURL = lndb

        status = None
        chapters = None
        volumes = None
        genres = []

        desc = None

        if not (mal is None):
            title = mal['title']
            malURL = 'http://myanimelist.net/manga/' + str(mal['id'])
            desc = mal['synopsis']
            status = mal['status']
            malimage = mal['image']

            cType = mal['type']

            try:
                if (int(mal['chapters']) == 0):
                    chapters = 'Unknown'
                else:
                    chapters = mal['chapters']
            except:
                chapters = 'Unknown'

            try:
                if (int(mal['volumes']) == 0):
                    volumes = 'Unknown'
                else:
                    volumes = mal['volumes']
            except:
                volumes = 'Unknown'

        if ani is not None:
            if title is None:
                title = ani['title_english']
            aniURL = 'http://anilist.co/manga/' + str(ani['id'])
            if ani['description']:
                desc = ani['description']
            try:
                status = ani['publishing_status'].title()
            except:
                pass

            cType = ani['type']

            try:
                if ani['title_japanese'] is not None:
                    jTitle = ani['title_japanese']

                if ani['total_chapters'] is not None:
                    if ani['total_chapters'] == 0:
                        chapters = 'Unknown'
                    else:
                        chapters = ani['total_chapters']
                else:
                    volumes = 'Unknown'

                if ani['total_volumes'] is not None:
                    if ani['total_volumes'] == 0:
                        volumes = 'Unknown'
                    else:
                        volumes = ani['total_volumes']
                else:
                    volumes = 'Unknown'

                if ani['genres'] is not None:
                    genres = ani['genres']

            except Exception as e:
                print(e)

        stats = DatabaseHandler.getRequestStats(title, 'LN')

        # ---------- BUILDING THE COMMENT ----------#

        # ----- LINKS -----#
        urlComments = []
        allLinks = ''
        if malURL is not None:
            urlComments.append(
                "[MAL]({})".format(sanitise_url_for_markdown(malURL)))
        if aniURL is not None:
            urlComments.append(
                "[ANI]({})".format(sanitise_url_for_markdown(aniURL)))
        if nuURL is not None:
            urlComments.append(
                "[NU]({})".format(sanitise_url_for_markdown(nuURL)))
        if lndbURL is not None:
            urlComments.append(
                "[LNDB]({})".format(sanitise_url_for_markdown(lndbURL)))

        for i, link in enumerate(urlComments):
            if i is not 0:
                allLinks += ', '
            allLinks += link

        # ----- JAPANESE TITLE -----#
        if (isExpanded):
            if jTitle is not None:
                comment += '\n\n'

                splitJTitle = jTitle.split()
                for i, word in enumerate(splitJTitle):
                    if not (i == 0):
                        comment += ' '
                    comment += word

        # ----- INFO LINE -----#

        if (isExpanded):
            comment += '\n\n('

            if cType:
                if cType == 'Novel':
                    cType = 'Light Novel'

                comment += '**' + cType + '** | '

            comment += '**Status:** ' + status

            if (cType != 'Light Novel'):
                if str(volumes) is not 'Unknown':
                    comment += ' | **Volumes:** ' + str(volumes)
                if str(chapters) is not 'Unknown':
                    comment += ' | **Chapters:** ' + str(chapters)
            else:
                if str(volumes) is not 'Unknown':
                    comment += ' | **Volumes:** ' + str(volumes)

            if genres:
                comment += ' | **Genres:** '
        else:
            comment += '\n\n('

            if cType:
                if cType == 'Novel':
                    cType = 'Light Novel'

                comment += cType + ' | '

            comment += 'Status: ' + status

            if (cType != 'Light Novel'):
                if str(chapters) is not 'Unknown':
                    comment += ' | Chapters: ' + str(chapters)
            else:
                comment += ' | Volumes: ' + str(volumes)

            if genres:
                comment += ' | Genres: '

        if genres:
            for i, genre in enumerate(genres):
                if i is not 0:
                    comment += ', '
                comment += genre

        if (isExpanded) and (stats is not None):
            comment += ')\n\n**Stats:** ' + str(
                stats['total']) + ' requests across ' + str(
                stats['uniqueSubreddits']) + ' server(s)) - ' + str(
                round(stats['totalAsPercentage'], 3)) + '% of all requests'
        else:
            comment += ')'

        # ----- DESCRIPTION -----#
        if (isExpanded):
            descComment += cleanupDescription(desc)

        # ----- END -----#
        receipt = '(LN) Request successful: ' + title + ' - '
        if malURL is not None:
            receipt += 'MAL '
        if ani is not None:
            receipt += 'AL '
        if nuURL is not None:
            receipt += 'MU '
        if lndbURL is not None:
            receipt += 'LNDB '
        print(receipt.encode('utf8'))

        embed = buildEmbedObject(title, allLinks, comment, malimage,
                                 isExpanded, descComment)

        dictToReturn = {}
        dictToReturn['title'] = title
        dictToReturn['embed'] = embed

        return dictToReturn
    except Exception as e:
        print(e)
        # traceback.print_exc()
        return None


def buildStatsEmbed(server=None, username=None, serverID="171004769069039616"):
    try:
        userNick = ''
        statComment = ''
        receipt = '(S) Request successful: Stats'

        if username is not None:
            reqMember = server.get_member(username)
            if reqMember.nick:
                userNick = reqMember.nick
            else:
                userNick = reqMember.name
            userStats = DatabaseHandler.getUserStats(username)

            if userStats:
                statComment += 'Some stats on ' + userNick + ':\n\n'
                statComment += '- **' + str(userStats[
                                                'totalUserRequests']) + '** requests made (' + str(
                    round(userStats['totalUserRequestsAsPercentage'],
                          3)) + '% of all requests and #' + str(
                    userStats['overallRequestRank']) + ' overall)\n'
                statComment += '- **' + str(userStats[
                                                'uniqueRequests']) + '** unique anime/manga requested\n'
                statComment += '\n'
                statComment += 'Their most frequently requested anime/manga overall are:\n\n'

                for i, request in enumerate(userStats['topRequests']):
                    statComment += str(i + 1) + '. **' + str(
                        request[0]) + '** (' + str(request[1]) + ' - ' + str(
                        request[2]) + ' requests)  \n'
            else:
                statComment += str(userNick) + ' hasn\'t used Roboragi yet.'

            receipt += ' - ' + userNick
        elif server:
            serverStats = DatabaseHandler.getSubredditStats(server)

            if serverStats:
                statComment += '**' + server.name + ' Stats**\n\n'
                statComment += 'On ' + server.name
                statComment += ' I have fulfilled a total of ' + str(
                    serverStats['total']) + ' requests, '
                statComment += 'representing ' + str(
                    round(serverStats['totalAsPercentage'],
                          2)) + '% of all requests. '
                statComment += 'A total of ' + str(serverStats[
                                                       'uniqueNames']) + ' unique anime/manga have been requested here, '
                statComment += 'with a mean value of ' + str(
                    round(serverStats['meanValuePerRequest'],
                          3)) + ' requests/show'
                statComment += ' and a standard deviation of ' + str(
                    round(serverStats['standardDeviation'], 3)) + '.'

                statComment += '\n\n'

                statComment += 'The most frequently requested anime/manga on this server are:\n\n'

                for i, request in enumerate(serverStats['topRequests']):
                    statComment += str(i + 1) + '. **' + str(
                        request[0]) + '** (' + str(request[1]) + ' - ' + str(
                        request[2]) + ' requests)\n'

            else:
                statComment += 'There have been no requests on ' + str(
                    server) + ' yet.'

            receipt += ' - ' + server.name
        else:
            basicStats = DatabaseHandler.getBasicStats(serverID)

            # The overall stats section
            statComment += '**Overall Stats**\n\n'

            statComment += 'I\'ve searched through ' + str(
                basicStats['totalComments'])
            statComment += ' unique comments and fulfilled a total of ' + str(
                basicStats['total'])
            statComment += ' requests across ' + str(
                basicStats['uniqueSubreddits']) + ' unique server(s). '
            statComment += 'A total of ' + str(basicStats['uniqueNames'])
            statComment += ' unique anime/manga have been requested, with a mean value of ' + str(
                round(basicStats['meanValuePerRequest'], 3))
            statComment += ' requests/show and a standard deviation of ' + str(
                round(basicStats['standardDeviation'], 3)) + '.'

            statComment += '\n\n'

            statComment += 'The most frequently requested anime/manga overall are:\n\n'

            for i, request in enumerate(basicStats['topRequests']):
                statComment += str(i + 1) + '. **' + str(
                    request[0]) + '** (' + str(request[1]) + ' - ' + str(
                    request[2]) + ' requests)\n'

            statComment += '\n'
            receipt += ' - Basic'

        print(receipt.encode('utf8'))
        localEmbed = buildEmbedObject('Stats', '', statComment, '', False, '')
        return localEmbed
    except:
        traceback.print_exc()
        return None


def buildHelpEmbed():
    try:
        embedTitle = "Help"
        helpComment = "You can call the bot by using specific tags on one of the active servers. Anime can be called using {curly braces}, manga can be called using <arrows> and light novels can be called using reverse square brace ]light novels\[ (e.g. {Nisekoi} or or ]Utsuro no Hako to Zero no Maria\[). {Single} ]will\[ give you a normal set of information while {{double}} <> ]]will\[\[ give you expanded information. Examples of these requests can be found [here](https://github.com/dashwav/Discordoragi/wiki/Example-Output)"
        localEmbed = buildEmbedObject(embedTitle, '', helpComment, '', False,
                                      '')
        return localEmbed
    except:
        traceback.print_exc()
        return None


def buildEmbedObject(embedTitle, embedLinks, embedContent, embedThumbnail,
                     isExpanded, descComment):
    localFooterTitle = '\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_'
    localFooter = "{anime}, <manga>, \]LN\[ | [FAQ](https://github.com/dashwav/Discordoragi/wiki) | [/r/](http://www.reddit.com/r/Roboragi/) | [Discord](https://discord.gg/SNv9yKs) | [Source](https://github.com/dashwav/Discordoragi) | [Synonyms](https://www.reddit.com/r/Roboragi/wiki/synonyms)"
    try:
        embed = Embed(title=embedTitle, description=embedLinks, type='rich')

        embed.set_thumbnail(url=embedThumbnail)

        embed.add_field(name='__Info__', value=embedContent)

        if isExpanded:
            if len(descComment.rstrip()) > 1023:
                descCommentCut = descComment.rstrip()[:1020] + '...'
                embed.add_field(name='__Description__', value=descCommentCut)
            else:
                embed.add_field(name='__Description__', value=descComment)

        embed.add_field(name=localFooterTitle, value=localFooter)
        return embed
    except Exception as e:
        print(e)


def sanitise_url_for_markdown(url):
    return url.replace('(', '\(').replace(')', '\)')
