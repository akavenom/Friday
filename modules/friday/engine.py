import h5py
import pickle
import random

def split_list(artists, seperator):
	for i in range(len(artists)):
		artists += artists[i].split(seperator)
	for artist in artists:
		if artist.split(seperator) != [artist]:
			artists.remove(artist)
	return artists


def individualize(artists):
	for seperator in (",", "+", "&", "Featuring"):	
		artists = split_list(artists, seperator)
	for i in range(len(artists)):
		artists[i] = artists[i].strip()
	artists = list(set(artists))
	return artists


def caps_alpha_numeric(string):
	string = string.upper()
	string = list(string)
	for i in range(len(string)):
		if (not string[i].isalnum()) or string[i] == " ":
			string[i] = " "
	string = "".join(string)
	return string


def tweets_have(user, string):
	if "sentences_tone" in user["tone"].keys():
		tweets_tone = user["tone"]["sentences_tone"]
		tweets = [sentences["text"] for sentences in tweets_tone]
		for i in range(len(tweets)):
			if string in tweets[i] or caps_alpha_numeric(string) in tweets[i]:
				return True, tweets_tone[i]["tones"]
	return False, None


def recommend(user):
	songs, liked, disliked = None, None, None
	with open("data/friday/songs.bin", "rb") as file:
		songs = pickle.load(file)

	all_songs = []
	all_artists = []
	liked_artists = {}
	disliked_artists = {}
	liked_genre = {}
	disliked_genre = {}
	pool = []

	for genre in songs.keys():
		for song in songs[genre]:
			# giving "greatest of all time" songs a preference
			if genre == "goat":
				if list(song + [0]) not in all_songs:
					all_songs.append(song + [1])
			else:
				if list(song + [0]) not in all_songs:
					all_songs.append(song + [0])

			artists = individualize([song[0].split("~")[1].strip()])
			for artist in artists:
				if artist not in all_artists:
					all_artists.append(artist)

	for song in user["liked"]:
		artists = individualize([song[0].split("~")[1].strip()])
		for artist in artists:
			if artist in liked_artists.keys():
				liked_artists[artist] += 1
			else:
				liked_artists[artist] = 1
		if song[2] in liked_genre.keys():
			liked_genre[song[2]] += 1
		else:
			liked_genre[song[2]] = 1

	for song in user["disliked"]:
		artists = individualize([song[0].split("~")[1].strip()])
		for artist in artists:
			if artist in disliked_artists.keys():
				disliked_artists[artist] += 1
			else:
				disliked_artists[artist] = 1
		if song[2] in disliked_genre.keys():
			disliked_genre[song[2]] += 1
		else:
			disliked_genre[song[2]] = 1


	"""
	Criteria of picking songs
	
	Likelyhood of a song being picked is based upon 4 aspects
	1. User's mentions of songs/artists/genres in tweets along with the sentiment of the tweet
	2. Overall sentiment of user's tweets
	3. User's liked and disliked songs
	4. Randomness
	"""

	for song in all_songs:
		if "tone" in user.keys():
			# mentions in tweets
			negatives = ["anger", "sadness"]
			positives = ["joy"]

			artists = individualize([song[0].split("~")[1].strip()])

			## check the mention of this song's genre
			they_do, tones = tweets_have(user, song[2])	
			if they_do:
				tone_ids = [t["tone_id"] for t in tones]
				if any([pos in tone_ids for pos in positives]):
					print(song[0], " +{} score because of positive genre mention in tweets".format((liked_genre[max(liked_genre)] if len(liked_genre) else 0) + 1.5))
					song[3] += (liked_genre[max(liked_genre)] if len(liked_genre) else 0) + 1.5
				elif any([neg in tone_ids for neg in negatives]):
					print(song[0], " -{} score because of negative genre mention in tweets".format(0.25))
					song[3] -= 0.25
				else:
					print(song[0], " +{} score because of genre mention in tweets".format((liked_genre[max(liked_genre)] if len(liked_genre) else 0) + 1))
					song[3] += (liked_genre[max(liked_genre)] if len(liked_genre) else 0) + 1

			## check the mention of this song's artist's name
			artists = individualize([song[0].split("~")[1].strip()])
			for artist in artists:
				they_do, tones = tweets_have(user, artist)
				if they_do:
					tone_ids = [t["tone_id"] for t in tones]
					if any([pos in tone_ids for pos in positives]):
						print(song[0], " +{} score because of positive artist mention in tweets".format((liked_artists[max(liked_artists)] if len(liked_artists) else 0) * 3 + 4))
						song[3] += (liked_artists[max(liked_artists)] if len(liked_artists) else 0) * 3 + 4
					elif any([neg in tone_ids for neg in negatives]):
						print(song[0], " -{} score because of negative artist mention in tweets".format(1))
						song[3] -= 1
					else:
						print(song[0], " +{} score because of artist mention in tweets".format((liked_artists[max(liked_artists)] if len(liked_artists) else 0) * 3 + 3))
						song[3] += (liked_artists[max(liked_artists)] if len(liked_artists) else 0) * 3 + 3

			## check the mention of this song's name
			they_do, tones = tweets_have(user, song[0].split("~")[0].strip())
			if they_do:
				tone_ids = [t["tone_id"] for t in tones]
				for s in all_songs:
					### judge other songs based on artists
					artists = individualize([song[0].split("~")[1].strip()])
					for artist in artists:
						if artist in s[0]:
							if any([pos in tone_ids for pos in positives]):
								print(song[0], " +{} score because of positive song mention of same artist in tweets".format((liked_artists[max(liked_artists)] if len(liked_artists) else 0) * 3 + 4))
								s[3] += (liked_artists[max(liked_artists)] if len(liked_artists) else 0) * 3 + 4
							elif any([neg in tone_ids for neg in negatives]):
								print(song[0], " -{} score because of negative song mention of same artist in tweets".format(1))
								s[3] -= 1
							else:
								print(song[0], " +{} score because of song mention of same artist in tweets".format((liked_artists[max(liked_artists)] if len(liked_artists) else 0) * 3 + 2))
								s[3] += (liked_artists[max(liked_artists)] if len(liked_artists) else 0) * 3 + 3
					if s[2] == song[2]:
						if any([pos in tone_ids for pos in positives]):
							print(song[0], " +{} score because of positive song of same genre mention in tweets".format((liked_genre[max(liked_genre)] if len(liked_genre) else 0) + 1.5))
							s[3] += (liked_genre[max(liked_genre)] if len(liked_genre) else 0) + 1.5
						elif any([neg in tone_ids for neg in negatives]):
							print(song[0], " -{} score because of negative song of same genre mention in tweets".format(0.25))
							s[3] -= 0.25
						else:
							print(song[0], " +{} score because of song of same genre mention in tweets".format((liked_genre[max(liked_genre)] if len(liked_genre) else 0) + 1))
							s[3] += (liked_genre[max(liked_genre)] if len(liked_genre) else 0) + 1

			# overall sentiment of the tweets
			link = {
				"anger": ("hip-hop", "rock", "edm"),
				"fear": (),                        ## neutral sentiment in this context
				"joy": ("hip-hop", "rock", "edm", "pop", "country"),
				"sadness": ("classical", "rock", "pop", "jazz", "country"),
				"analytical": ("classical", "jazz", "country"),
				"confident": (),                   ## neutral sentiment in this context
				"tentative": ()                    ## neutral sentiment in this context
			}
			overall_sentiment = user["tone_24_hours"]["document_tone"]["tones"]

			for sentiment in overall_sentiment:
				if song[2] in link[sentiment["tone_id"]]:
					print(song[0], "{} for {} overall tone".format(round(sentiment["score"] * 2), sentiment["tone_id"]))
					song[3] += round(sentiment["score"] * 2)

		# likes and dislikes
		## likes
		artists = individualize([song[0].split("~")[1].strip()])
		for artist in artists:
			if artist in liked_artists.keys():
				print(song[0], " +{} for liking artist {}".format(3 * liked_artists[artist], artist))
				song[3] += 4 * liked_artists[artist]
		if song[2] in liked_genre.keys():
			print(song[0], " +{} for liking genre {}".format(0.75 * liked_genre[song[2]], song[2]))
			song[3] += 0.75 * liked_genre[song[2]]

		## dislikes
		artists = individualize([song[0].split("~")[1].strip()])
		for artist in artists:
			if artist in disliked_artists.keys():
				print(song[0], " -{} for disliking artist {}".format(1 * disliked_artists[artist], artist))
				song[3] -= 1 * disliked_artists[artist]
		if song[2] in disliked_genre.keys():
			print(song[0], " -{} for disliking genre {}".format(0.2 * disliked_genre[song[2]], song[2]))
			song[3] -= 0.2 * disliked_genre[song[2]]		

	# normalizing scores to convert scores into probabilities
	lowest = min([s[3] for s in all_songs])
	if lowest <= 0:
		for song in all_songs:
			song[3] -= lowest - 1
	highest = max([s[3] for s in all_songs])
	print("Final probabilities:-")
	for song in all_songs:
		print("score:", song[3])
		song[3] = song[3] / highest
		print(song[0], "| final probability:", song[3], "highest:", highest)

	if "songs" in user.keys():
		del user["songs"]
	user["songs"] = []

	# picking 10 songs
	print("10 picked songs:-")
	for i in range(10):
		while True:
			draw = random.uniform(0, 1)
			pool = []
			for song in all_songs:
				if song not in user["songs"] and draw <= song[3]:
					pool.append(song)
			if len(pool) > 0:
				break
		idx = random.randint(0, len(pool) - 1)
		user["songs"].append(pool[idx])
		print("Picked", pool[idx][0], "for probability", pool[idx][3])
	return user