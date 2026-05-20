import os   #used to read spotify keys from env
from dotenv import load_dotenv
import spotipy   #spotify python api library
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()   #loads env variables


#this creates spotify authenticated client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),

    scope="user-read-playback-state,user-modify-playback-state,user-read-currently-playing"
))


def play_music():
    #resumes current spotify playback
    try:
        sp.start_playback()
        return "Resuming your Spotify music now."
    except:
        return "Spotify playback could not be started."


def pause_music():
    #pauses current playing track
    try:
        sp.pause_playback()
        return "Music paused."
    except:
        return "Unable to pause Spotify."


def next_song():
    #skips to next track
    try:
        sp.next_track()
        return "Skipping to the next song."
    except:
        return "Unable to skip track."


def previous_song():
    #goes back to previous track
    try:
        sp.previous_track()
        return "Playing previous song."
    except:
        return "Unable to go to previous track."


def play_specific_song(song_name):
    #searches spotify song by name and starts playing best match
    try:
        results = sp.search(q=song_name, type="track", limit=1)

        tracks = results["tracks"]["items"]

        if len(tracks) == 0:
            return "I could not find that song on Spotify."

        track_uri = tracks[0]["uri"]
        track_name = tracks[0]["name"]
        artist_name = tracks[0]["artists"][0]["name"]

        sp.start_playback(uris=[track_uri])

        return f"Playing {track_name} by {artist_name}."

    except:
        return "Spotify could not play that song."