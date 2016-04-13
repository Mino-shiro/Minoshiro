'''
AnimeBot.py
Acts as the "main" file and ties all the other functionality together.
'''

import discord as dapi
import re
import traceback
import requests
import time

import Search
import CommentBuilder
import DatabaseHandler
import Config

TIME_BETWEEN_PM_CHECKS = 60 #in seconds

try:
    import Config
    USEREMAIL = Config.useremail
    PASSWORD = Config.password
    CHANNELLIST = Config.get_formatted_channel_list()
except ImportError:
    pass

client = dapi.Client()

#the servers where expanded requests are disabled
disableexpanded = ['']

#servers I'm actively avoiding
exiled = ['']

#Sets up Discord API
def setupDiscord():
    try:
        print('Setting up Discord')
        await client.start(USEREMAIL, PASSWORD)
        print('Discord successfully set up')
    except Exception as e:
        print('Error with setting up Discord: ' + str(e))

#function for processing edit requests
def process_edits():
    for msg in reddit.get_unread(limit=None):
        if (msg.subject == 'username mention'):
            if (('{' and '}') in msg.body) or (('<' and '>') in msg.body):
                try:
                    if str(msg.subreddit).lower() in exiled:
                        print('Edit request from exiled subreddit: ' + str(msg.subreddit) + '\n')
                        msg.mark_as_read()
                        continue

                    mentionedComment = reddit.get_info(thing_id=msg.name)
                    mentionedComment.refresh()

                    if not (DatabaseHandler.messageExists(mentionedComment.id)):
                        if str(mentionedComment.subreddit).lower() in Config.subredditlist:
                            continue

                    replies = mentionedComment.replies

                    ownComments = []
                    commentToEdit = None

                    for reply in replies:
                        if (reply.author.name == 'Roboragi'):
                            ownComments.append(reply)

                    for comment in ownComments:
                        if 'http://www.reddit.com/r/Roboragi/wiki/index' in comment.body:
                            commentToEdit = comment

                    commentReply = process_comment(mentionedComment, True)

                    try:
                        if (commentReply):
                            if commentToEdit:
                                commentToEdit.edit(commentReply)
                                print('Comment edited.\n')
                            else:
                                mentionedComment.reply(commentReply)
                                print('Comment made.\n')
                    except praw.errors.Forbidden:
                        print('Edit equest from banned subreddit: ' + str(msg.subreddit) + '\n')

                    msg.mark_as_read()

                except Exception as e:
                    print(e)

#process dat message
def process_message(message, is_edit=False):
    #Anime/Manga requests that are found go into separate arrays
    animeArray = []
    mangaArray = []

    #ignores all "code" markup (i.e. anything between backticks)
    cleanMessage = re.sub(r"\`(?s)(.*?)\`", "", message.clean_content)

    #The basic algorithm here is:
    #If it's an expanded request, build a reply using the data in the braces, clear the arrays, add the reply to the relevant array and ignore everything else.
    #If it's a normal request, build a reply using the data in the braces, add the reply to the relevant array.

    #Counts the number of expanded results vs total results. If it's not just a single expanded result, they all get turned into normal requests.
    numOfRequest = 0
    numOfExpandedRequest = 0
    forceNormal = False
    for match in re.finditer("\{{2}([^}]*)\}{2}|\<{2}([^>]*)\>{2}", cleanMessage, re.S):
        numOfRequest += 1
        numOfExpandedRequest += 1

    for match in re.finditer("(?<=(?<!\{)\{)([^\{\}]*)(?=\}(?!\}))|(?<=(?<!\<)\<)([^\<\>]*)(?=\>(?!\>))", cleanMessage, re.S):
        numOfRequest += 1

    if (numOfExpandedRequest >= 1) and (numOfRequest > 1):
        forceNormal = True

    #Expanded Anime
    for match in re.finditer("\{{2}([^}]*)\}{2}", cleanMessage, re.S):
        reply = ''
        if (forceNormal) or (str(message.channel).lower() in disableexpanded):
            reply = Search.buildAnimeReply(match.group(1), False)
        else:
            reply = Search.buildAnimeReply(match.group(1), True)

        if (reply is not None):
            animeArray.append(reply)

    #Normal Anime
    for match in re.finditer("(?<=(?<!\{)\{)([^\{\}]*)(?=\}(?!\}))", cleanMessage, re.S):
        reply = Search.buildAnimeReply(match.group(1), False)

        if (reply is not None):
            animeArray.append(reply)

    #Expanded Manga
    #NORMAL EXPANDED
    for match in re.finditer("\<{2}([^>]*)\>{2}(?!(:|\>))", cleanMessage, re.S):
        reply = ''

        if (forceNormal) or (str(message.channel).lower() in disableexpanded):
            reply = Search.buildMangaReply(match.group(1), False)
        else:
            reply = Search.buildMangaReply(match.group(1), True)

        if (reply is not None):
            mangaArray.append(reply)

    #AUTHOR SEARCH EXPANDED
    for match in re.finditer("\<{2}([^>]*)\>{2}:\(([^)]+)\)", cleanMessage, re.S):
        reply = ''

        if (forceNormal) or (str(message.channel).lower() in disableexpanded):
            reply = Search.buildMangaReplyWithAuthor(match.group(1), match.group(2), False)
        else:
            reply = Search.buildMangaReplyWithAuthor(match.group(1), match.group(2), True)

        if (reply is not None):
            mangaArray.append(reply)

    #Normal Manga
    #NORMAL
    for match in re.finditer("(?<=(?<!\<)\<)([^\<\>]+)\>(?!(:|\>))", cleanMessage, re.S):
        reply = Search.buildMangaReply(match.group(1), False)

        if (reply is not None):
            mangaArray.append(reply)

    #AUTHOR SEARCH
    for match in re.finditer("(?<=(?<!\<)\<)([^\<\>]*)\>:\(([^)]+)\)", cleanMessage, re.S):
        reply = Search.buildMangaReplyWithAuthor(match.group(1), match.group(2), False)

        if (reply is not None):
            mangaArray.append(reply)

    #Here is where we create the final reply to be posted

    #The final message reply. We add stuff to this progressively.
    messageReply = ''

    #Basically just to keep track of people posting the same title multiple times (e.g. {Nisekoi}{Nisekoi}{Nisekoi})
    postedAnimeTitles = []
    postedMangaTitles = []

    #Adding all the anime to the final message. If there's manga too we split up all the paragraphs and indent them in Reddit markup by adding a '>', then recombine them
    for i, animeReply in enumerate(animeArray):
        if not (i is 0):
            messageReply += '\n\n'

        if not (animeReply['title'] in postedAnimeTitles):
            postedAnimeTitles.append(animeReply['title'])
            messageReply += animeReply['message']


    if mangaArray:
        messageReply += '\n\n'

    #Adding all the manga to the final message
    for i, mangaReply in enumerate(mangaArray):
        if not (i is 0):
            messageReply += '\n\n'

        if not (mangaReply['title'] in postedMangaTitles):
            postedMangaTitles.append(mangaReply['title'])
            messageReply += mangaReply['message']

    #If there are more than 10 requests, shorten them all
    if not (messageReply is '') and (len(animeArray) + len(mangaArray) >= 10):
        messageReply = re.sub(r"\^\((.*?)\)", "", messageReply, flags=re.M)

    #If there was actually something found, add the signature and post the message to Reddit. Then, add the message to the "already seen" database.
    if not (messageReply is ''):
        messageReply += Config.getSignature(message.permalink)

    if is_edit:
        return messageReply
    else:
        try:
            print("message made.\n")
            return messageReply
        except praw.errors.Forbidden:
            print('Request from banned subreddit: ' + str(message.channel) + '\n')
        except Exception:
            traceback.print_exc()

        try:
            DatabaseHandler.addMessage(message.id, message.author.name, message.channel, True)
        except:
            traceback.print_exc()
    else:
        try:
            if is_edit:
                return None
            else:
                DatabaseHandler.addMessage(message.id, message.author.name, message.channel, False)
        except:
            traceback.print_exc()


#The main function
def start():
    print('Starting message stream:')
    for message in client.messages:
        #Is the message valid (i.e. it's not made by Roboragi and I haven't seen it already). If no, try to add it to the "already seen pile" and skip to the next message. If yes, keep going.
        if not (Search.isValidmessage(message)):
            try:
                if not (DatabaseHandler.messageExists(message.id)):
                    DatabaseHandler.addMessage(message.id, message.author.name, message.channel, False)
            except:
                pass
            continue

        process_message(message)

#Overwrite on_message so we can run our stuff
def dapi.on_message(message):
	print('Message recieved')
	for channel in CHANNELLIST:
		if(str(message.chanel).lower() == channel.lower()):
			#Is the message valid (i.e. it's not made by Roboragi and I haven't seen it already). If no, try to add it to the "already seen pile" and skip to the next message. If yes, keep going.
			if not (Search.isValidmessage(message)):
				try:
					if not (DatabaseHandler.messageExists(message.id)):
						DatabaseHandler.addMessage(message.id, message.author.name, message.channel, False)
				except:
					pass
				continue
				
			process_message(message)
			
# ------------------------------------#
#Here's the stuff that actually gets run

#Initialise Discord.
setupDiscord()