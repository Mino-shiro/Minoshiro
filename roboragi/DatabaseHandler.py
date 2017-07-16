'''
DatabaseHandler.py
Handles all connections to the database. The database runs on PostgreSQL and is connected to via psycopg2.
'''

import psycopg2
from math import sqrt
import traceback
import discord

DBNAME = ''
DBUSER = ''
DBPASSWORD = ''
DBHOST = ''

try:
    import Config
    DBNAME = Config.dbname
    DBUSER = Config.dbuser
    DBPASSWORD = Config.dbpassword
    DBHOST = Config.dbhost
except ImportError:
    pass

conn = psycopg2.connect("dbname='" + DBNAME + "' user='" + DBUSER + "' host='" + DBHOST + "' password='" + DBPASSWORD + "'")
cur = conn.cursor()

#Sets up the database and creates the databases if they haven't already been made.
def setup():
    try:
        conn = psycopg2.connect("dbname='" + DBNAME + "' user='" + DBUSER + "' host='" + DBHOST + "' password='" + DBPASSWORD + "'")
    except:
        print("Unable to connect to the database")

    cur = conn.cursor()

    #Create requests table
    try:
        cur.execute('CREATE TABLE requests ( id SERIAL PRIMARY KEY, name varchar(320), type varchar(16), requester varchar(50), server varchar(50), requesttimestamp timestamp DEFAULT current_timestamp)')
        conn.commit()
    except Exception as e:
        #traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()

    #Create messages table
    try:
        cur.execute('CREATE TABLE messages ( messageid varchar(32) PRIMARY KEY, requester varchar(50), server varchar(50), hadRequest boolean)')
        conn.commit()
    except Exception as e:
        #traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()

setup()

#--------------------------------------#

# Adds a message to the "already seen" database. Also handles submissions, which have a similar ID structure.
def addMessage(messageid, requester, serverid, hadRequest):
    try:
        server = serverid.lower()
        
        cur.execute('INSERT INTO messages (messageid, requester, server, hadRequest) VALUES (%s, %s, %s, %s)', (messageid, requester, server, hadRequest))
        conn.commit()
    except Exception as e:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()

#Returns true if the message/submission has already been checked.
def messageExists(messageid):
    try:
        cur.execute('SELECT * FROM messages WHERE messageid = %s', (messageid,))
        if (cur.fetchone()) is None:
            conn.commit()
            return False
        else:
            conn.commit()
            return True
    except Exception as e:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()
        return True
        
#Adds a request to the request-tracking database. rType is either "Anime" or "Manga".
def addRequest(name, rType, requester, serverid):
    try:
        server = serverid.lower()

        if ('nihilate' not in server):
            cur.execute('INSERT INTO requests (name, type, requester, server) VALUES (%s, %s, %s, %s)', (name, rType, requester, server))
            conn.commit()
    except Exception as e:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()

#Returns an object which contains data about the overall database stats (i.e. ALL servers).
def getBasicStats(serverID, top_media_number=5, top_username_number=5):
    try:
        basicStatDict = {}

        cur.execute("SELECT COUNT(1) FROM messages")
        totalComments = int(cur.fetchone()[0])
        basicStatDict['totalComments'] = totalComments
        
        cur.execute("SELECT COUNT(1) FROM requests;")
        total = int(cur.fetchone()[0])
        basicStatDict['total'] = total
        
        cur.execute("SELECT COUNT(1) FROM (SELECT DISTINCT name FROM requests) as temp;")
        dNames = int(cur.fetchone()[0])
        basicStatDict['uniqueNames'] = dNames

        cur.execute("SELECT COUNT(1) FROM (SELECT DISTINCT server FROM requests) as temp;")
        dSubreddits = int(cur.fetchone()[0])
        basicStatDict['uniqueSubreddits'] = dSubreddits

        meanValue = float(total)/dNames
        basicStatDict['meanValuePerRequest'] = meanValue

        variance = 0
        cur.execute("SELECT name, count(name) FROM requests GROUP by name")
        for entry in cur.fetchall():
            variance += (entry[1] - meanValue) * (entry[1] - meanValue)

        variance = variance / dNames
        stdDev = sqrt(variance)
        basicStatDict['standardDeviation'] = stdDev

        cur.execute("SELECT name, type, COUNT(name) FROM requests GROUP BY name, type ORDER BY COUNT(name) DESC, name ASC LIMIT %s", (top_media_number,))
        topRequests = cur.fetchall()
        basicStatDict['topRequests'] = []
        for request in topRequests:
            basicStatDict['topRequests'].append(request)

        cur.execute("SELECT requester, COUNT(requester), server, COUNT(server) FROM requests WHERE server = %s GROUP BY requester, server ORDER BY COUNT(requester) DESC, requester ASC, COUNT(server) DESC, server ASC LIMIT %s", (serverID, top_username_number,))
        topRequesters = cur.fetchall()
        basicStatDict['topRequesters'] = []
        for requester in topRequesters:
            basicStatDict['topRequesters'].append(requester)

        conn.commit()
        return basicStatDict
        
    except Exception as e:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()
        return None

#Returns an object which contains request-specifc data. Basically just used for the expanded comments.
def getRequestStats(requestName, type):
    try:
        basicRequestDict = {}

        requestType = type

        cur.execute("SELECT COUNT(*) FROM requests")
        total = int(cur.fetchone()[0])
        
        cur.execute("SELECT COUNT(*) FROM requests WHERE name = %s AND type = %s", (requestName, requestType))
        requestTotal = int(cur.fetchone()[0])
        basicRequestDict['total'] = requestTotal

        if requestTotal == 0:
            return None

        cur.execute("SELECT COUNT(DISTINCT server) FROM requests WHERE name = %s AND type = %s", (requestName, requestType))
        dSubreddits = int(cur.fetchone()[0])
        basicRequestDict['uniqueSubreddits'] = dSubreddits

        totalAsPercentage = (float(requestTotal)/total) * 100
        basicRequestDict['totalAsPercentage'] = totalAsPercentage

        conn.commit()
        return basicRequestDict
        
    except:
        cur.execute('ROLLBACK')
        conn.commit()
        return None

#Returns an object which contains data about the overall database stats (i.e. ALL servers).
def getUserStats(username, top_media_number=5):
    try:
        basicUserStatDict = {}
        username = str(username).lower()
        
        """
        cur.execute("SELECT COUNT(1) FROM messages where LOWER(requester) = %s", (username,))
        totalUserComments = int(cur.fetchone()[0])
        basicUserStatDict['totalUserComments'] = totalUserComments

        
        cur.execute("SELECT COUNT(1) FROM messages")
        totalNumComments = int(cur.fetchone()[0])
        totalCommentsAsPercentage = (float(totalUserComments)/totalNumComments) * 100
        basicUserStatDict['totalUserCommentsAsPercentage'] = totalCommentsAsPercentage
         """

        cur.execute("SELECT COUNT(*) FROM requests where LOWER(requester) = %s", (username,))
        totalUserRequests = int(cur.fetchone()[0])
        basicUserStatDict['totalUserRequests'] = totalUserRequests
        
        cur.execute("SELECT COUNT(1) FROM requests")
        totalNumRequests = int(cur.fetchone()[0])
        totalRequestsAsPercentage = (float(totalUserRequests)/totalNumRequests) * 100
        basicUserStatDict['totalUserRequestsAsPercentage'] = totalRequestsAsPercentage
        
        cur.execute('''SELECT row FROM
            (SELECT requester, count(1), ROW_NUMBER() over (order by count(1) desc) as row
                from requests
                group by requester) as overallrequestrank 
            where lower(requester) = %s''', (username,))
        overallRequestRank = int(cur.fetchone()[0])
        basicUserStatDict['overallRequestRank'] = overallRequestRank

        cur.execute("SELECT COUNT(DISTINCT (name, type)) FROM requests WHERE LOWER(requester) = %s", (username,))
        uniqueRequests = int(cur.fetchone()[0])
        basicUserStatDict['uniqueRequests'] = uniqueRequests

        
        cur.execute('''select r.server, count(r.server), total.totalcount from requests r
            inner join (select server, count(server) as totalcount from requests
            group by server) total on total.server = r.server
            where LOWER(requester) = %s
            group by r.server, total.totalcount
            order by count(r.server) desc
            limit 1
            ''', (username,))
        favouriteSubredditStats = cur.fetchone()
        favouriteSubreddit = str(favouriteSubredditStats[0])
        favouriteSubredditCount = int(favouriteSubredditStats[1])
        favouriteSubredditOverallCount = int(favouriteSubredditStats[2])
        basicUserStatDict['favouriteSubreddit'] = favouriteSubreddit
        basicUserStatDict['favouriteSubredditCount'] = favouriteSubredditCount
        basicUserStatDict['favouriteSubredditCountAsPercentage'] = (float(favouriteSubredditCount)/favouriteSubredditOverallCount) * 100
        
        cur.execute('''SELECT name, type, COUNT(name) FROM requests where LOWER(requester) = %s
        GROUP BY name, type ORDER BY COUNT(name) DESC, name ASC LIMIT %s''', (username, top_media_number))
        topRequests = cur.fetchall()
        basicUserStatDict['topRequests'] = []
        for request in topRequests:
            basicUserStatDict['topRequests'].append(request)

        conn.commit()
        return basicUserStatDict
        
    except Exception as e:
        cur.execute('ROLLBACK')
        conn.commit()
        return None
        
#Similar to getBasicStats - returns an object which contains data about a specific server.
def getSubredditStats(server, top_media_number=5, top_username_number=5):
    try:
        basicSubredditDict = {}
        print(server.name+"\n")
        print(server.id+"\n")
        serverID = server.id

        """
        cur.execute("SELECT COUNT(*) FROM messages WHERE server = %s", (serverID,))
        totalComments = int(cur.fetchone()[0])
        basicSubredditDict['totalComments'] = totalComments
        """

        cur.execute("SELECT COUNT(*) FROM requests;")
        total = int(cur.fetchone()[0])
        
        cur.execute("SELECT COUNT(*) FROM requests WHERE server = %s", (serverID,))
        sTotal = int(cur.fetchone()[0])
        basicSubredditDict['total'] = sTotal

        if sTotal == 0:
            return None

        cur.execute("SELECT COUNT(DISTINCT (name, type)) FROM requests WHERE server = %s", (serverID,))
        dNames = int(cur.fetchone()[0])
        basicSubredditDict['uniqueNames'] = dNames

        totalAsPercentage = (float(sTotal)/total) * 100
        basicSubredditDict['totalAsPercentage'] = totalAsPercentage
        
        meanValue = float(sTotal)/dNames
        basicSubredditDict['meanValuePerRequest'] = meanValue

        variance = 0
        cur.execute("SELECT name, type, count(name) FROM requests WHERE server = %s GROUP by name, type", (serverID,))
        for entry in cur.fetchall():
            variance += (entry[2] - meanValue) * (entry[2] - meanValue)

        variance = variance / dNames
        stdDev = sqrt(variance)
        basicSubredditDict['standardDeviation'] = stdDev

        cur.execute("SELECT name, type, COUNT(name) FROM requests WHERE server = %s GROUP BY name, type ORDER BY COUNT(name) DESC, name ASC LIMIT %s", (serverID, top_media_number))
        topRequests = cur.fetchall()
        basicSubredditDict['topRequests'] = []
        for request in topRequests:
            basicSubredditDict['topRequests'].append(request)
        
        cur.execute("SELECT requester, COUNT(requester) FROM requests WHERE server = %s GROUP BY requester ORDER BY COUNT(requester) DESC, requester ASC LIMIT %s", (serverID, top_username_number))
        topRequesters = cur.fetchall()
        basicSubredditDict['topRequesters'] = []
        for requester in topRequesters:
            basicSubredditDict['topRequesters'].append(requester)

        conn.commit()
        
        return basicSubredditDict
    except Exception as e:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()
        return None
