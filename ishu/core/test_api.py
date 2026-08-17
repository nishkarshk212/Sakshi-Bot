
import requests
import os

# Your API key
API_KEY = "lily_6ttewJtNQfKvIUUhV6mxKwRwEf0CxJhZ"
BACKEND_URL = "https://youtube-api-saas-backend.onrender.com"


def download_song(song_query="tum hi ho", output_file="downloaded_song.mp3"):
    print("=" * 60)
    print(" Song Downloader via YouTube API Proxy")
    print("=" * 60)
    print(f" Searching for: '{song_query}'...")
    print(f"   Using API key: {API_KEY[:15]}...")

    # First search for the song
    search_params = {"api_key": API_KEY, "q": song_query}

    try:
        print(f"\n Step 1: Sending search request...")
        search_response = requests.get(
            f"{BACKEND_URL}/search",
            params=search_params,
            timeout=30
        )

        if not search_response.ok:
            print(f" Search failed! Status {search_response.status_code}")
            print(f"   Error: {search_response.text}")
            return False

        search_data = search_response.json()
        if not search_data.get("results") or len(search_data["results"]) == 0:
            print(" No songs found!")
            return False
            
        video_id = search_data["results"][0]["id"]
        title = search_data["results"][0]["title"]
        print(f" Search successful! Found: {title} (ID: {video_id})")

        # Now try to get audio (using /audio endpoint)
        audio_params = {
            "api_key": API_KEY,
            "id": video_id,
        }

        print(f"\n Step 2: Getting audio stream URL...")
        audio_metadata_response = requests.get(
            f"{BACKEND_URL}/audio",
            params=audio_params,
            timeout=60
        )

        if not audio_metadata_response.ok:
            print(f" Audio metadata failed! Status {audio_metadata_response.status_code}")
            print(f"   Error: {audio_metadata_response.text[:500]}")
            return False

        audio_data = audio_metadata_response.json()
        if "audio" not in audio_data or "best_audio" not in audio_data["audio"] or "url" not in audio_data["audio"]["best_audio"]:
            print(" Failed to find audio stream URL in the response!")
            return False

        stream_url = audio_data["audio"]["best_audio"]["url"]
        
        print(f"\n Step 3: Downloading audio stream...")
        audio_response = requests.get(
            stream_url,
            stream=True,
            timeout=60
        )

        if audio_response.ok:
            total_size = int(audio_response.headers.get('content-length', 0))
            print(f" Starting download to {output_file} (size: {total_size / 1024 / 1024:.2f} MB)...")

            with open(output_file, 'wb') as f:
                downloaded = 0
                for chunk in audio_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r   Downloaded: {percent:.1f}%", end='')

            print(f"\n Download complete! File saved as: {os.path.abspath(output_file)}")
            print("=" * 60)
            return True
        else:
            print(f" Audio download failed! Status {audio_response.status_code}")
            print(f"   Error: {audio_response.text[:500]}")
            return False

    except Exception as e:
        print(f"\n Error: {e}")
        return False

def download_video(song_query="tum hi ho video", output_file="downloaded_video.mp4"):
    print("=" * 60)
    print(" Video Downloader via YouTube API Proxy")
    print("=" * 60)
    print(f" Searching for: '{song_query}'...")
    print(f"   Using API key: {API_KEY[:15]}...")

    search_params = {"api_key": API_KEY, "q": song_query}

    try:
        print(f"\n Step 1: Sending search request...")
        search_response = requests.get(
            f"{BACKEND_URL}/search",
            params=search_params,
            timeout=30
        )

        if not search_response.ok:
            print(f" Search failed! Status {search_response.status_code}")
            return False

        search_data = search_response.json()
        if not search_data.get("results") or len(search_data["results"]) == 0:
            print(" No videos found!")
            return False
            
        video_id = search_data["results"][0]["id"]
        title = search_data["results"][0]["title"]
        print(f" Search successful! Found: {title} (ID: {video_id})")

        video_params = {
            "api_key": API_KEY,
            "id": video_id,
        }

        print(f"\n Step 2: Getting video stream URL...")
        video_metadata_response = requests.get(
            f"{BACKEND_URL}/video",
            params=video_params,
            timeout=60
        )

        if not video_metadata_response.ok:
            print(f" Video metadata failed! Status {video_metadata_response.status_code}")
            return False

        video_data = video_metadata_response.json()
        if "video" not in video_data or "stream_url" not in video_data["video"]:
            print(" Failed to find video stream URL in the response!")
            return False

        stream_url = video_data["video"]["stream_url"]
        
        print(f"\n Step 3: Downloading video stream...")
        video_response = requests.get(
            stream_url,
            stream=True,
            timeout=60
        )

        if video_response.ok:
            total_size = int(video_response.headers.get('content-length', 0))
            print(f" Starting download to {output_file} (size: {total_size / 1024 / 1024:.2f} MB)...")

            with open(output_file, 'wb') as f:
                downloaded = 0
                for chunk in video_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r   Downloaded: {percent:.1f}%", end='')

            print(f"\n Download complete! File saved as: {os.path.abspath(output_file)}")
            print("=" * 60)
            return True
        else:
            print(f" Video download failed! Status {video_response.status_code}")
            return False

    except Exception as e:
        print(f"\n Error: {e}")
        return False


if __name__ == "__main__":
    download_song()
    download_video()
