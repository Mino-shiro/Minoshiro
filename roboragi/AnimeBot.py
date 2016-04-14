'''
AnimeBot.py
Acts as the "main" file and ties all the other functionality together.
'''

import discord
import asyncio
import re
import traceback
import requests
import time

import Search
import CommentBuilder
import DatabaseHandler
import Config

try:
	import Config
	print('Getting Config Info')
	USEREMAIL = Config.useremail
	PASSWORD = Config.password
except ImportError:
	pass

client = discord.Client()

#the servers where expanded requests are disabled
disableexpanded = ['']

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

#Overwrite on_message so we can run our stuff
@client.event
async def on_message(message):
	print('Message recieved')
	#Is the message valid (i.e. it's not made by Discordoragi and I haven't seen it already). If no, try to add it to the "already seen pile" and skip to the next message. If yes, keep going.
	if not (Search.isValidmessage(message)):
		try:
			if not (DatabaseHandler.messageExists(message.id)):
				DatabaseHandler.addMessage(message.id, message.author.name, message.channel, False)
		except:
			pass
		
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
				await client.send_message(message.channel, messageReply)
			else:
				try:
					print("message made.\n")
					await client.send_message(message.channel, messageReply)
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
			
# ------------------------------------#
#Here's the stuff that actually gets run

#Initialise Discord.
print('Starting Bot')
client.run('MTcwMTUxMzA0MDkyNTgxODg5.CfEhQA.Jdj992DvWSXdlOLXBJGnAPrgV3I')