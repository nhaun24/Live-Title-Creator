import tkinter as tk
from tkinter import ttk
import configparser
from tkcalendar import DateEntry
import tkinter.messagebox as messagebox
import pyperclip

from googleapiclient.discovery import build
from google.oauth2 import service_account

import requests


def save_entry():
    date = entry_date.get()
    title = entry_title.get()
    scripture = entry_scripture.get()
    speaker = combo_speaker.get()

    # Generate stream title
    stream_title = generate_stream_title(date, title, scripture, speaker)
    output_box.configure(state="normal")
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, stream_title)
    output_box.configure(state="disabled")


def generate_stream_title(date, title, scripture, speaker):
    stream_title = f"{date} - {speaker}: {title} ({scripture})"
    return stream_title


def copy_to_clipboard():
    stream_title = output_box.get("1.0", tk.END).strip()
    pyperclip.copy(stream_title)
    messagebox.showinfo("Copy to Clipboard", "Stream Title copied to clipboard.")


def create_streams():
    stream_title = output_box.get("1.0", tk.END).strip()
    scheduled_time = '2023-06-10T12:00:00.000Z'  # Replace with the desired scheduled time

    try:
        youtube = build_youtube_client()
        youtube_broadcast_id = create_youtube_broadcast(youtube, stream_title, scheduled_time)
        set_youtube_stream_title(youtube, youtube_broadcast_id, stream_title)
        messagebox.showinfo("YouTube Stream Created", "YouTube Stream created successfully!")

        facebook_access_token = get_facebook_access_token()
        facebook_stream_id = create_facebook_stream(facebook_access_token, stream_title, scheduled_time)
        set_facebook_stream_title(facebook_access_token, facebook_stream_id, stream_title)
        messagebox.showinfo("Facebook Stream Created", "Facebook Stream created successfully!")
    except Exception as e:
        messagebox.showerror("Stream Creation Error", str(e))


def build_youtube_client():
    credentials = service_account.Credentials.from_service_account_file('path/to/credentials.json')
    youtube = build('youtube', 'v3', credentials=credentials)
    return youtube


def create_youtube_broadcast(youtube, title, scheduled_time):
    live_broadcast = youtube.liveBroadcasts().insert(
        part='snippet,status,contentDetails',
        body={
            'snippet': {
                'title': title,
                'scheduledStartTime': scheduled_time,
            },
            'status': {
                'privacyStatus': 'private',
            },
            'contentDetails': {
                'monitorStream': {
                    'enableMonitorStream': False,
                },
            },
        }
    ).execute()

    broadcast_id = live_broadcast['id']
    return broadcast_id


def set_youtube_stream_title(youtube, broadcast_id, stream_title):
    youtube.liveBroadcasts().update(
        part='snippet',
        body={
            'id': broadcast_id,
            'snippet': {
                'title': stream_title,
            },
        }
    ).execute()


def get_facebook_access_token():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config.get('Facebook', 'ACCESS_TOKEN')


def create_facebook_stream(access_token, title, scheduled_time):
    url = f'https://graph.facebook.com/v14.0/me/live_videos?access_token={access_token}'

    params = {
        'title': title,
        'scheduled_time': scheduled_time,
        'status': 'SCHEDULED'
    }

    response = requests.post(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to create Facebook stream. Error: {response.json().get('error', {}).get('message')}")

    data = response.json()
    stream_id = data['id']
    return stream_id


def set_facebook_stream_title(access_token, stream_id, title):
    url = f'https://graph.facebook.com/v14.0/{stream_id}?access_token={access_token}'

    params = {
        'title': title
    }

    response = requests.post(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to set Facebook stream title. Error: {response.json().get('error', {}).get('message')}")


root = tk.Tk()
root.title("Sermon Details")
root.geometry("400x650")
root.resizable(False, False)

# Set the background color of the root window
root.configure(background="#303030")

# Load configuration file
config = configparser.ConfigParser()
config.read("config.ini")

# Create the form elements
style = ttk.Style()
style.theme_use("clam")

style.configure("TLabel", background="#303030", foreground="#FFFFFF")
style.configure("TEntry", background="#505050", foreground="#FFFFFF")
style.configure("TButton", background="#FF9800", foreground="#FFFFFF")

# Title lines
title_label1 = ttk.Label(root, text="Herrin Second Baptist Church", font=("Helvetica", 16),
                         background="#303030", foreground="#FFFFFF")
title_label1.pack(pady=10)

title_label2 = ttk.Label(root, text=""" "Where every member is a minister" """, font=("Helvetica", 12),
                         background="#303030", foreground="#FFFFFF")
title_label2.pack()

label_date = ttk.Label(root, text="Date:")
label_date.pack(pady=10)
entry_date = DateEntry(root, background="#505050", foreground="#FFFFFF", date_pattern="yyyy-mm-dd")
entry_date.pack()

label_title = ttk.Label(root, text="Title:")
label_title.pack(pady=10)
entry_title = ttk.Entry(root)
entry_title.pack()

label_scripture = ttk.Label(root, text="Scripture:")
label_scripture.pack(pady=10)
entry_scripture = ttk.Entry(root)
entry_scripture.pack()

label_speaker = ttk.Label(root, text="Speaker:")
label_speaker.pack(pady=10)
combo_speaker = ttk.Combobox(root, values=config.options('Speakers'))
combo_speaker.pack()

button_save = ttk.Button(root, text="Save", command=save_entry)
button_save.pack(pady=10)

output_label = ttk.Label(root, text="Stream Title:")
output_label.pack(pady=10)
output_box = tk.Text(root, height=2, width=40, background="#505050", foreground="#FFFFFF")
output_box.configure(state="disabled")
output_box.pack()

button_copy = ttk.Button(root, text="Copy to Clipboard", command=copy_to_clipboard)
button_copy.pack(pady=10)

button_create_streams = ttk.Button(root, text="Create Streams", command=create_streams)
button_create_streams.pack(pady=10)

root.mainloop()
