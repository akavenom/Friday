from modules.twitter_interface import tweets
from modules import watson
from modules.friday import engine
import os
import pickle
import h5py


root_path = str(os.path.realpath(__file__))
root_path = root_path[:len(root_path) - 9]


def load_session():
	with open(root_path + "data/friday/session.sav", "rb") as file:
		user = pickle.load(file)
	return user


def end_session(user):
	# clean user information before saving if the user doesn't want to be remembered
	if not user["logged_in"]:
		user["first_name"] = ""
		user["last_name"] = ""
		user["username"] = ""
		user["access_key"] = "0" * 100
		user["access_secret"] = ""

	with open(root_path + "data/friday/session.sav", "wb") as file:
		pickle.dump(user, file)

def load_likes_and_dislikes(user):
	with h5py.File(root_path + "data/friday/likes.hdf5", "r") as file:
		user["liked"] = []
		for song in file[user["username"]]:
			user["liked"].append([song[0].decode("utf8"), song[1].decode("utf8"), song[2].decode("utf8"), 0])
	with h5py.File(root_path + "data/friday/dislikes.hdf5", "r") as file:
		user["disliked"] = []
		for song in file[user["username"]]:
			user["disliked"].append([song[0].decode("utf8"), song[1].decode("utf8"), song[2].decode("utf8"), 0])
	print(user["liked"])
	return user

def save_likes_and_dislikes(user):
	for i in range(len(user["liked"])):
		user["liked"][i].pop(3)
	for i in range(len(user["disliked"])):
		user["disliked"][i].pop(3)
	with h5py.File(root_path + "data/friday/likes.hdf5", "a") as file:
		del file[user["username"]]
		file.create_dataset(user["username"], data=user["liked"])

	with h5py.File(root_path + "data/friday/dislikes.hdf5", "a") as file:
		del file[user["username"]]
		file.create_dataset(user["username"], data=user["disliked"])

def check_login(user):
	if not user["logged_in"]:
		from modules.friday import loginator
		user = loginator.login(user)
		if user["first_name"] == "" and user["last_name"] == "":
			print("Bye!")
			exit()
		print("Signed in as", user["first_name"], user["last_name"])

def save_user_keys(user):
	database = None
	with h5py.File(root_path + "data/friday/users.hdf5", "r") as users_file:
		database = users_file["users"]
		for i in range(len(database)):
			if database[i][2] == user["username"].encode("utf8"):
				database[i][4] = user["access_key"].encode("utf8")
				database[i][5] = user["access_secret"].encode("utf8")
				break
	with h5py.File(root_path + "data/friday/users.hdf5", "w") as users_file:
		d = users_file.create_dataset("users", data=database)

def main():
	while True:
		user = load_session()

		check_login(user)

		user = load_likes_and_dislikes(user)

		got_new_keys, user = tweets.get_tweets(user)
		if got_new_keys:
			print("Saving user access tokens")
			save_user_keys(user)

		user = watson.analyzer.analyze(user)

		user = engine.recommend(user)

		from modules.friday import main
		user = friday.main.run(user)
		
		save_likes_and_dislikes(user)
		end_session(user)

		if not user["logged_out"]:
			break

if __name__ == "__main__":
	main()