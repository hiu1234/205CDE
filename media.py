import ffmpeg
import sys
import json

def media_process(path):
	json = {}
	try:
		info = ffmpeg.probe(path)
	except :
		print("media analyze error")
		return(json)
		
	duration = 0
	duration = info["format"]["duration"]
	json["duration"] = float(duration)

	if(info["format"].get("tags")):
		lowered = {tag.lower(): key for tag, key in info["format"]["tags"].items()}
		title = lowered.get("title")
		if title:
			json["title"] = title
		artist = lowered.get("artist")
		if artist:
			json["artist"] = artist
		album = lowered.get("album")
		if album:
			json["album"] = album

	return(json)

if __name__ == "__main__":
	test = media_process(sys.argv[1])
	print(test)