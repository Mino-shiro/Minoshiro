'''
AnimeBot.py
Acts as the "main" file and ties all the other functionality together.
'''

import asyncio
import re
import traceback
import requests
import time

import discord
import Discord
import DiscordoragiSearch
import CommentBuilder
import DatabaseHandler
import Config
import Reference

#the servers where expanded requests are disabled
disableexpanded = ['']
async_queue = asyncio.Queue(maxsize = 32)
ownerID = '164546159140929538'

@Discord.client.event
async def on_ready():
    print('Logged in as')
    print(Discord.client.user.name)
    print(Discord.client.user.id)
    print('------')

@Discord.client.event
async def on_server_join(server):
    DatabaseHandler.addServerToDatabase(server.id)
    print("Added server {} to database".format(server.id))
    
async def process_message(message, is_edit=False):
    #Anime/Manga requests that are found go into separate arrays
    animeArray = []
    mangaArray = []
    lnArray = []

    #Checks if bot has permissions to embed
    if message.channel.type != discord.ChannelType.private:
        canEmbed = message.channel.server.default_role.permissions.embed_links
    else:
        canEmbed = True
    if not canEmbed:
        botMember = Discord.getMemberFromID(Config.clientid, message.server)
        defaultroleperm = botMember.top_role.permissions
        canEmbed = defaultroleperm.embed_links
    

    isAdmin = message.author.top_role.permissions.administrator
    isServerMod = message.author.top_role.permissions.manage_server
    isOwner = message.author.id == ownerID
    
    if message.author.bot:
        return
    

    #ignores all "code" markup (i.e. anything between backticks)
    preCleanMessage = re.sub(r"\`(.*?)\`", "", message.clean_content)
    cleanMessage = re.sub(r'<:.+?:([0-9]{15,21})>', "", preCleanMessage)
    messageReply = ''

    if re.search('({!help.*?}|{{!help.*?}}|<!help.*?>|<<!help.*?>>)', cleanMessage, re.S) is not None:
        try:
            localEm = CommentBuilder.buildHelpEmbed()
            await Discord.client.send_message(message.channel, embed = localEm)
            return
        except:
            return

    if re.search('({!command.*?}|{{!command.*?}}|<!command.*?>|<<!command.*?>>)', cleanMessage, re.S) is not None:
        if 'toggleexpanded' in cleanMessage.lower() and (isAdmin or isServerMod):
            try:
                allowedStatus = DatabaseHandler.toggleAllowExpanded(message.server.id)
                print("Toggled allowExpanded for server {}".format(message.server.id))
                if allowedStatus.lower() == 'true':
                    await Discord.client.send_message(message.channel, "Expanded requests are now allowed.")
                else:
                    await Discord.client.send_message(message.channel, "Expanded requests are now disallowed.")
                return
            except Exception as e:
                print(e)
                return

        if 'addserver' in cleanMessage.lower() and (isOwner == True):
            try:
                DatabaseHandler.addServerToDatabase(message.server.id)
                await Discord.client.send_message(message.channel, "Server has been added.")
                return
            except Exception as e:
                print(e)
                return

        else:
            print("command failed, user probably has insufficient rights")
            return
    
    
    sender = re.search('[@]([A-Za-z0-9 _-]+?)(>|}|$)', cleanMessage, re.S)
    mentionArray = message.raw_mentions
    if re.search('({!stats.*?}|{{!stats.*?}}|<!stats.*?>|<<!stats.*?>>)', cleanMessage, re.S) is not None and sender is not None:
        for mention in mentionArray:
            if not canEmbed:
                messageReply = CommentBuilder.buildStatsComment(server=message.server, username=mention)
            else:
                localEm = CommentBuilder.buildStatsEmbed(server=message.server, username=mention)
                await Discord.client.send_message(message.channel, embed=localEm)
                return None
    if re.search('({!sstats}|{{!sstats}}|<!sstats>|<<!sstats>>)', cleanMessage, re.S) is not None:
        if not canEmbed:
            messageReply = CommentBuilder.buildStatsComment(server = message.server)
        else:
            localEm = CommentBuilder.buildStatsEmbed(server = message.server)
            await Discord.client.send_message(message.channel, embed=localEm)
            return None
    elif re.search('({!stats.*?}|{{!stats.*?}}|<!stats.*?>|<<!stats.*?>>)', cleanMessage, re.S) is not None:
        if not canEmbed:
            messageReply = CommentBuilder.buildStatsComment()
        else:
            localEm = CommentBuilder.buildStatsEmbed()
            await Discord.client.send_message(message.channel, embed=localEm)
            return None
    else:
        
        #The basic algorithm here is:
        #If it's an expanded request, build a reply using the data in the braces, clear the arrays, add the reply to the relevant array and ignore everything else.
        #If it's a normal request, build a reply using the data in the braces, add the reply to the relevant array.
        
        #Counts the number of expanded results vs total results. If it's not just a single expanded result, they all get turned into normal requests.
        numOfRequest = 0
        numOfExpandedRequest = 0
        forceNormal = False
        expandedAllowed = DatabaseHandler.checkServerConfig('allowexpanded', message.server.id)
        if expandedAllowed == False:
            forceNormal = True
        for match in re.finditer("\{{2}([^}]*)\}{2}|\<{2}([^>]*)\>{2}", cleanMessage, re.S):
            numOfRequest += 1
            numOfExpandedRequest += 1
            print("Request found: {}".format(match.group(0)))

        for match in re.finditer("(?<=(?<!\{)\{)([^\{\}]*)(?=\}(?!\}))|(?<=(?<!\<)\<)([^\<\>]*)(?=\>(?!\>))", cleanMessage, re.S):
            numOfRequest += 1
            print("Request found: {}".format(match.group(0)))

        if (numOfExpandedRequest >= 1) and (numOfRequest > 1):
            forceNormal = True
        
        #if numOfRequest != 0:
            #await Discord.client.send_typing(message.channel)
        #Expanded Anime
        for match in re.finditer("\{{2}([^}]*)\}{2}", cleanMessage, re.S):
            reply = ''
            if match.group(1) != '':
                if (forceNormal) or (str(message.channel).lower() in disableexpanded):
                    reply = await DiscordoragiSearch.buildAnimeReply(match.group(1), message, False, canEmbed)
                else:
                    reply = await DiscordoragiSearch.buildAnimeReply(match.group(1), message, True, canEmbed)

                if (reply is not None):
                    animeArray.append(reply)
            else:
                print("Empty request, ignoring")

        #Normal Anime
        for match in re.finditer("(?<=(?<!\{)\{)([^\{\}]*)(?=\}(?!\}))", cleanMessage, re.S):
            if match.group(1) != '':
                reply = await DiscordoragiSearch.buildAnimeReply(match.group(1), message, False, canEmbed)

                if (reply is not None):
                    animeArray.append(reply)
                else:
                    print('Could not find anime')
            else:
                print("Empty request, ignoring")


        #Expanded Manga
        #NORMAL EXPANDED
        for match in re.finditer("\<{2}([^>]*)\>{2}(?!(:|\>))", cleanMessage, re.S):
            if match.group(1) != '':
                reply = ''

                if (forceNormal) or (str(message.channel).lower() in disableexpanded):
                    reply = await DiscordoragiSearch.buildMangaReply(match.group(1), message, False, canEmbed)
                else:
                    reply = await DiscordoragiSearch.buildMangaReply(match.group(1), message, True, canEmbed)

                if (reply is not None):
                    mangaArray.append(reply)
            else:
                print("Empty request, ignoring")

        #AUTHOR SEARCH EXPANDED
        for match in re.finditer("\<{2}([^>]*)\>{2}:\(([^)]+)\)", cleanMessage, re.S):
            if match.group(1) != '':
                reply = ''

                if (forceNormal) or (str(message.server).lower() in disableexpanded):
                    reply = await DiscordoragiSearch.buildMangaReplyWithAuthor(match.group(1), match.group(2), message, False, canEmbed)
                else:
                    reply = await DiscordoragiSearch.buildMangaReplyWithAuthor(match.group(1), match.group(2), message, True, canEmbed)

                if (reply is not None):
                    mangaArray.append(reply)
            else:
                print("Empty request, ignoring")

        #Normal Manga
        #NORMAL
        for match in re.finditer("(?<=(?<!\<)\<)([^\<\>]+)\>(?!(:|\>))", cleanMessage, re.S):
            if match.group(1) != '':
                reply = await DiscordoragiSearch.buildMangaReply(match.group(1), message, False, canEmbed)

                if (reply is not None):
                    mangaArray.append(reply)
            else:
                print("Empty request, ignoring")

        #AUTHOR SEARCH
        for match in re.finditer("(?<=(?<!\<)\<)([^\<\>]*)\>:\(([^)]+)\)", cleanMessage, re.S):
            reply = await DiscordoragiSearch.buildMangaReplyWithAuthor(match.group(1), match.group(2), message, False, canEmbed)

            if (reply is not None):
                mangaArray.append(reply)

        #Expanded LN
        for match in re.finditer("\]{2}([^]]*)\[{2}", cleanMessage, re.S):
            if match.group(1) != '':
                reply = ''

                if (forceNormal) or (str(message.server).lower() in disableexpanded):
                    reply = await DiscordoragiSearch.buildLightNovelReply(match.group(1), False, message, canEmbed)
                else:
                    reply = await DiscordoragiSearch.buildLightNovelReply(match.group(1), True, message, canEmbed)                    

                if (reply is not None):
                    lnArray.append(reply)
            else:
                print("Empty request, ignoring")

        #Normal LN  
        for match in re.finditer("(?<=(?<!\])\])([^\]\[]*)(?=\[(?!\[))", cleanMessage, re.S):
            if match.group(1) != '':
                reply = await DiscordoragiSearch.buildLightNovelReply(match.group(1), False, message, canEmbed)
                
                if (reply is not None):
                    lnArray.append(reply)
            else:
                print("Empty request, ignoring")

        #Here is where we create the final reply to be posted

        #The final message reply. We add stuff to this progressively.
        postedAnimeTitles = []
        postedMangaTitles = []
        postedLNTitles = []
    
        messageReply = ''
        #Basically just to keep track of people posting the same title multiple times (e.g. {Nisekoi}{Nisekoi}{Nisekoi})
        postedAnimeTitles = []
        postedMangaTitles = []
        postedLNTitles = []
        #Adding all the anime to the final message. If there's manga too we split up all the paragraphs and indent them in Reddit markup by adding a '>', then recombine them
        for i, animeReply in enumerate(animeArray):
            if not (i is 0):
                messageReply += '\n\n'
            if not (animeReply['title'] in postedAnimeTitles):
                postedAnimeTitles.append(animeReply['title'])
                if not canEmbed:
                    messageReply += animeReply['comment']
                else:
                    messageReply = 'n/a'
        if mangaArray:
            messageReply += '\n\n'
        #Adding all the manga to the final message
        for i, mangaReply in enumerate(mangaArray):
            if not (i is 0):
                messageReply += '\n\n'
            if not (mangaReply['title'] in postedMangaTitles):
                postedMangaTitles.append(mangaReply['title'])
                if not canEmbed:
                    messageReply += mangaReply['comment']
                else: 
                    messageReply = 'n/a'
        if lnArray:
            messageReply += '\n\n'
        #Adding all the manga to the final comment
        for i, lnReply in enumerate(lnArray):
            if not (i is 0):
                commentReply += '\n\n'
            
            if not (lnReply['title'] in postedLNTitles):
                postedLNTitles.append(lnReply['title'])
                if not canEmbed:
                    messageReply += lnReply['comment']
                else:
                    messageReply = 'N/A'
        #If there are more than 10 requests, shorten them all
        if not (messageReply is '') and (len(animeArray) + len(mangaArray) >= 10):
            messageReply = re.sub(r"\^\((.*?)\)", "", messageReply, flags=re.M)
    #If there was actually something found, add the signature and post the message to Reddit. Then, add the message to the "already seen" database.
    if not (messageReply is ''):

        if is_edit:
            if not canEmbed:
                await Discord.client.send_message(message.channel, messageReply)
            else:
                for i, animeReply in enumerate(animeArray):
                    await Discord.client.send_message(message.channel, embed=animeReply['embed'])
                for i, mangaReply in enumerate(mangaArray):
                    await Discord.client.send_message(message.channel, embed=mangaReply['embed'])
                for i, lnReply in enumerate(lnArray):
                    await Discord.client.send_message(message.channel, embed=lnReply['embed'])
        else:
            try:
                print("Message created.\n")
                if not canEmbed:
                    await Discord.client.send_message(message.channel, messageReply)
                else:
                    for i, animeReply in enumerate(animeArray):
                        await Discord.client.send_message(message.channel, embed=animeReply['embed'])
                    for i, mangaReply in enumerate(mangaArray):
                        await Discord.client.send_message(message.channel, embed=mangaReply['embed'])
                    for i, lnReply in enumerate(lnArray):
                        await Discord.client.send_message(message.channel, embed=lnReply['embed'])
            except discord.errors.Forbidden:
                print('Request from banned channel: ' + str(message.channel) + '\n')
            except Exception as e:
                print(e)
                traceback.print_exc()
            except:
                traceback.print_exc()
    else:
        try:
            if is_edit:
                return None
            else:
                DatabaseHandler.addMessage(message.id, message.author.id, message.server.id, False)
        except:
            traceback.print_exc()

#Overwrite on_message so we can run our stuff
@Discord.client.event
async def on_message(message):
    from DiscordoragiSearch import isValidMessage #local import here to fix attribute not found error
    print('Message recieved')
    #Is the message valid (i.e. it's not made by Discordoragi and I haven't seen it already). If no, try to add it to the "already seen pile" and skip to the next message. If yes, keep going.
    if not (isValidMessage(message)):
        try:
            if not (DatabaseHandler.messageExists(message.id)):
                DatabaseHandler.addMessage(message.id, message.author.id, message.server.id, False)
        except Exception:
            traceback.print_exc()
            pass
    else:
        await process_message(message)
            
# ------------------------------------#
#Here's the stuff that actually gets run

#Initialise Discord.
print('Starting Bot')
Discord.run()
