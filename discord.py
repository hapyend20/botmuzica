#!/usr/bin/python3

""" This bot is written for romanian users, but the comments are in english. 
    Also, this is my first python project, so the code isn't "ideal" """

""" This bot is designed to be hosted on a Linux based OS, if you want to 
    make it work under Windows you need te make a few tweaks. 
    Feel free to make pull requests if you want to make this "Frankensteined" bot
    better.    
"""

"""
MIT Licence:
Copyright 2017 Tirel Antony

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal 
in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
DEALINGS IN THE SOFTWARE.

"""
import sys
import random
import math
import os
import discord
import asyncio
import urllib.request
import urllib.parse
import re
from discord.ext import commands
import collections
from bs4 import BeautifulSoup
import requests

version = 1.0

if not discord.opus.is_loaded():
    try:
        import opuslib
        discord.opus.load_opus('opus')
    except:
        print('OpusLib nu a fost gasit. Bot-ul nu va putea sa intre in nici un voice channel. ')


#Varialbes for the ".gluma" command

said_1 = False
said_2 = False
said_3 = False
said_4 = False
said_5 = False
said_6 = False 
said_7 = False
said_8 = False
said_9 = False

client = commands.Bot(command_prefix=".")


@client.event
async def on_ready():
    if len(sys.argv) > 1:
        """
        This is the implementation for emergency messages that will be send to all Discord servers that have this bot.
        In an ideal world all Linux servers will have 100% uptime, but back to reality(there goes gravity), we have to be able to
        send some kind of feedback when we are about to perform updates / close the server.
        """    
        for server in client.servers:
            for text_channel in server.channels:
                if text_channel.permissions_for(server.me).send_messages:
                    await client.send_message(text_channel, str(sys.argv[1]))
                    break
    else:
        print('Discord Python API v. {}\nRoBot in actiune. \nTotal servere Discord care folosesc bot-ul: {}'.format(discord.__version__, len(client.servers)))
    

class GetInfo:
    def __init__(self, user_voice_ch_id, user_server_id, message):
        self.user_voice_ch_id = message.author.voice_channel.id
        self.user_server_id = message.author.server.id
        self.message_content = message.content
        self.message = message
        self.channel = client.get_channel(self.user_voice_ch_id)


class YoutubePlayer(GetInfo):
    voice_dict = {}
    player_dict = {}
    paused_state = {}
    user_votes = {}
    non_queue_owner = {}
    vote_pending = {}
    def __init__(self, youtube_url, user_voice_ch_id, user_server_id, message):
        self.youtube_url = youtube_url
        super().__init__(user_voice_ch_id, user_server_id, message)

    # Create a voice object that is unique per server. Isn't that cool? 
    async def create_voice_object(self, add_in_queue):
        try:
            voice = await client.join_voice_channel(self.channel)
            YoutubePlayer.voice_dict[self.user_server_id] = voice
            self.non_queue_owner[self.user_server_id] = self.message.author
            return voice
        except: 
            if self.youtube_url and add_in_queue:
                Playlist.add_to_playlist(self.user_server_id, self.youtube_url, self.message)
                await client.send_message(self.message.channel, 'Sigur, adaug in playlist {}'.format(self.youtube_url))

            return False

    async def create_youtube_player(self, voice, youtube_url, message):
        try:
            player = await voice.create_ytdl_player(youtube_url)
            player.start()
        except:
            if voice:
                await client.send_message(self.message.channel, 'URL-ul YouTube este invalid. Ori exista o problema cu drepturile de autor, ori link-ul este gresit.')
                await exit_voice_channel(1, voice)
            return False
        if player.duration:
            song_time = player.duration
        else:
            """This is a dirty hack to play YouTube live streams without crashing
            I forgot that live streams existed. Who is watching YouTube live streams anyway...
            So when I feel like tweaking this, I will. Trust me.
            PS: 3600s = 1h, so in the range of 1-4 hours of stream the bot will 
            get bored and exit the voice channel. 10/10 IGN. 
            """
            song_time = random_int_gen(3600, 12800)
            print('Numar generat random pentru live stream: {}'.format(song_time))


        YoutubePlayer.player_dict[self.user_server_id] = player
        print('player: {}'.format(YoutubePlayer.player_dict[self.user_server_id]))
        return song_time

    """
    Resource management for non-rack mounted servers with
    compute power level less than 9000
    """
    def destroy_youtube_player(self):
        current_song = Playlist.queue_dict.get(self.user_server_id)
        current_owner = Playlist.owner_dict.get(self.user_server_id)
        if current_song and current_owner:
            try:
                current_song.pop(0)
                current_owner.pop(0)
            except IndexError:
                pass
            YoutubePlayer.player_dict[self.user_server_id].stop()
            if len(current_song) == 0:
                Playlist.queue_dict.pop(self.user_server_id)
                Playlist.owner_dict.pop(self.user_server_id)

        

    async def output_trakcs(self):
        server_tracks = Playlist.queue_dict.get(self.user_server_id)
        if server_tracks:
            str_song = ', '.join(server_tracks)
            await client.send_message(self.message.channel, 'Total melodii: {}, URL: {}'.format(len(server_tracks), str_song))
    
        else:
            await client.send_message(self.message.channel, 'Total melodii: 0')


    #Finally, play some music, grab a beer and relax.
    async def play_youtube_url(self):
        if self.youtube_url:
            if self.youtube_url.startswith('https://www.youtube.com/watch?v=') or self.youtube_url.startswith('http://www.youtube.com/watch?v=') or self.youtube_url.startswith('https://youtu.be/') or self.youtube_url.startswith('http://youtu.be/'):
                voice = await self.create_voice_object(True)
                player = await self.create_youtube_player(voice, self.youtube_url, self.message)
                if player != False:
                    await client.send_message(self.message.channel, 'Sigur, adaug in playlist {}'.format(self.youtube_url))
                    song_time = player
                    current_player = self.player_dict.get(self.user_server_id)
                    await exit_voice_channel(song_time, voice)
                    await self.play_queued_song(None)
                    if self.player_dict.get(self.user_server_id) == current_player:
                        self.destroy_youtube_player()

              #If a song is in queue, play it.
            
    async def play_queued_song(self, skip_url):
        while True:
            if not skip_url:
                check_next_song = Playlist.queue_dict.get(self.user_server_id, False)
                was_skipped = False
            else:
                check_next_song = skip_url
                was_skipped = True
            print('check {}'.format(check_next_song))
            if check_next_song:
                voice = await self.create_voice_object(False)
                # For whatever reason, create_youtube_player is not working here.
                # For now, I will repeat that code, untill I can figure this out.
                try:
                    if skip_url == None:
                        player = await voice.create_ytdl_player(check_next_song[0])
                    else:
                        player = await voice.create_ytdl_player(check_next_song)
                    player.start()
                except:
                    if voice and was_skipped:
                        await client.send_message(self.message.channel, 'URL-ul YouTube este invalid. Ori exista o problema cu drepturile de autor, ori link-ul este gresit.')
                        await ForceExit(None, self.user_voice_ch_id, self.user_server_id, self.message).voice_force_exit(False)
                        self.destroy_youtube_player()

                    elif voice and not was_skipped:
                        await ForceExit(None, self.user_server_id, self.user_server_id, self.message).voice_force_exit(False)
                        self.destroy_youtube_player()

                    else:
                        #TODO This is a problem. Log that.
                        pass
                    break
                song_time = int(player.duration)
                YoutubePlayer.player_dict[self.user_server_id] = player
                await exit_voice_channel(song_time, voice)
                if was_skipped:
                    skip_url = None
                else:
                    self.destroy_youtube_player()
            else:
                break

    async def skip_song(self):
        server_queue = Playlist.queue_dict.get(self.user_server_id)
        owner_queue = Playlist.owner_dict.get(self.user_server_id)
        if server_queue and owner_queue and len(server_queue) >=1:
            if await self.democracy(self.message, True): 
                await ForceExit(None, self.user_voice_ch_id, self.user_server_id, self.message).voice_force_exit(False)
                song_to_remove = server_queue.pop(0)
                owner_queue.pop(0)
                await self.play_queued_song(song_to_remove)
            
        else:
            await client.send_message(self.message.channel, 'Nu exista nici o melodie in playlist. Nu fi timid, adauga.')
            return
    
    async def remove_song(self, user_input):
        if user_input.startswith('https://') and Playlist.queue_dict.get(self.user_server_id) and await self.democracy(self.message, True):
            counter = 0 
            for tracks in Playlist.queue_dict[self.user_server_id]:
                found_song = Playlist.queue_dict[self.user_server_id][counter]
                if found_song == user_input:
                    succes = Playlist.queue_dict[self.user_server_id].pop(counter)
                    Playlist.owner_dict[self.user_server_id].pop(counter)
                    return succes
                else:
                    counter += 1

        elif not Playlist.queue_dict.get(self.user_server_id):
            await client.send_message(self.message.channel, 'Nu exista nici o melodie in playlist.')
            return False

        else:
            try:
                index = int(user_input)
                is_int = True
            except:
                is_int = False
          
            if is_int:
                #The user did all the work for me. Just remove the index provided...
                if Playlist.queue_dict.get(self.user_server_id) and await self.democracy(self.message, True):
                    number_of_songs = len(Playlist.queue_dict.get(self.user_server_id))
                    if Playlist.queue_dict.get(self.user_server_id):
                        if number_of_songs >= index and index > 0 and number_of_songs > 0:
                            removed_index = Playlist.queue_dict[self.user_server_id].pop(index - 1)
                            Playlist.owner_dict[self.user_server_id].pop(index - 1)
                            return removed_index

                        else:
                            await client.send_message(self.message.channel, 'Nu exista nici o melodie in playlist cu index-ul mentionat de tine')
                            return False

            elif not is_int:
                #This is my time to shine. Time for some detective action
                if await self.democracy(self.message, True):
                    search_url = await YoutubeSearch(user_input, self.message).search_youtube_url(self.user_server_id, 1)
                    counter = 0
                    if Playlist.queue_dict.get(self.user_server_id):
                        for tracks in Playlist.queue_dict[self.user_server_id]:
                            search_in_queue = Playlist.queue_dict[self.user_server_id][counter]
                            if search_url == search_in_queue:
                                removed_index = Playlist.queue_dict[self.user_server_id].pop(counter)
                                Playlist.owner_dict[self.user_server_id].pop(counter)
                                return removed_index
                            else:
                                counter += 1
                        else:
                           await client.send_message(self.message.channel, 'Nu am gasti nici o melodie in queue cu keyword-ul mentionat de tine. Verifica daca melodia chiar exista in playlsit, sau incearca din nou.') 
                           return False

        
    async def pause_song(self):
        get_player = self.player_dict.get(self.user_server_id)
        if get_player and not self.paused_state.get(self.user_server_id):
            get_player.pause()
            self.paused_state[self.user_server_id] = True

        elif get_player and self.paused_state.get(self.user_server_id):
            self.paused_state.pop(self.user_server_id)
            get_player.resume()
            
        else:
            await client.send_message(self.message.channel, 'Sunt pe stop, daca vrei sa fiu pe pauza trebuie sa pui o melodie.')
            return

    async def democracy(self, message, scan_once):
        """
        Simple vote method for voice related administrative tasks.
        """

        """
        Check to see if the one trying to execute a administrative voice command has the right to do so before checking if another vote is pending. 
        This is useful if a vote already started and than the owner showed to authorise the request, so he/she has unlimited power of that request.
        It is very important to check if another vote is pending for security reasons. Otherwise trolls can just start another vote for the same
        or different action before the previous votes expired, so all the previous votes are gone. We hate trolls, right?!?
        """
        if self.non_queue_owner.get(self.user_server_id) != self.message.author:
            if self.vote_pending.get(self.user_server_id):
                await client.send_message(self.message.channel, 'Exista momentan o alta actiune care necesita votare, actiune propusa de: {} Te rog sa astepti pana cand majoritatea voteaza actiunea anterioara sau pana cand aceasta expira'.format(self.vote_pending[self.user_server_id]))
                return False
            
        if self.user_votes.get(self.user_server_id): # Remove junk if needed
            self.user_votes.pop(self.user_server_id)
        voice_members = len(self.channel.voice_members) - 1 # We subtract 1 because the original lenght includes the bot in the counting. 
                                                            #The bot should not be counted, only humans have poweeeer!!!! 
        if voice_members:
            if voice_members <= 2: 
                """There sould be just two more member left. In this case,
                there is no need for wasting processing power."""
                return True

            elif scan_once and Playlist.owner_dict.get(self.user_server_id):
                if Playlist.owner_dict[self.user_server_id][0] == message.author:
                    # He/She is the DJ. Unlimited power is needed.
                    print('owner')
                    return True

            elif not scan_once: # That means we need to leave forever, not just skip a song. Sad, isn't it?
                counter = 0
                same_owner = 0
                if Playlist.owner_dict.get(self.user_server_id):
                    for owners in Playlist.owner_dict.get(self.user_server_id):
                        if Playlist.owner_dict.get(self.user_server_id)[counter] == message.author:
                            same_owner +=1
                            counter +=1
                        else:
                            await client.send_message(self.message.channel, 'Imi pare rau, dar nu ai drept asupra tuturor melodiilor din playlist. Traim intr-o tara democratica.')
                            await self.democracy(message, True)
                            

                    if len(Playlist.owner_dict.get(self.user_server_id)) == same_owner:
                        return True
                else: # This means that the current playing song is the only one in queue.
                    if self.non_queue_owner.get(self.user_server_id) == message.author:
                        return True
                    else:
                        await self.democracy(message, True)
                
            self.vote_pending[self.user_server_id] = self.message.author
            votes_req = voice_members // 2 # ~ 33% of the members, because it's floor division.
            await client.send_message(self.message.channel, 'Voturi necesare: {} , ".vot" pentru a vota. 60 de secunde ramase...'.format(votes_req))
            state = self.user_votes.get(self.user_server_id)
            x = 0
            while x < 30: # ~ 60 sec vote time.
                if self.user_votes.get(self.user_server_id):
                    if len(self.user_votes[self.user_server_id]) == votes_req:
                        if self.vote_pending.get(self.user_server_id):
                            self.vote_pending.pop(self.user_server_id)
                        return True
                    else:
                        if state != self.user_votes.get(self.user_server_id): # If a user has voted send feedback to the text channel.
                            state = self.user_votes.get(self.user_server_id)
                            await client.send_message(self.message.channel, 'Voturi: {} / {} , ".vot" pentru a vota. {} de secunde ramase...'.format(len(state), votes_req, 60-x*2))
                x +=1
                await asyncio.sleep(2)
            else:
                if self.vote_pending.get(self.user_server_id):
                    self.vote_pending.pop(self.user_server_id) # The time has expired
                await client.send_message(self.message.channel, 'Tic-tac, n-ati votat.')
                if self.user_votes.get(self.user_server_id):
                    self.user_votes.pop(self.user_server_id)
                return False



class YoutubeSearch:
    def __init__(self, user_keyword, message):
        self.user_keyword = user_keyword
        self.message = message
        
    
#Method for searching a YouTube url based on keywords
    async def search_youtube_url(self, user_server_id, results_number):
        
            # Modified code form Grant Curell, https://www.codeproject.com/Articles/873060/Python-Search-Youtube-for-Video. License: GPLv3.
            query_string = urllib.parse.urlencode({"search_query" : self.user_keyword})
            html_content = urllib.request.urlopen("https://www.youtube.com/results?" + query_string)
            search_results = re.findall(r'href=\"\/watch\?v=(.{11})', html_content.read().decode())
            if results_number == 1:
                if search_results:
                    return ("https://www.youtube.com/watch?v=" + search_results[0])
                else:
                    await client.send_message(self.message.channel, 'Imi pare rau, dar nu am gasit nici un rezultat cu acest keyword.')
                    return
                # End of copyright
            else:
                search_dict = {}
                counter = 0
                result = search_dict[user_server_id] = []
                for links in search_results[0:results_number]:
                    result.append('https://www.youtube.com/watch?v=' + search_results[counter])
                    counter += 1
                    if len(result) == results_number:
                        print(result)
                        return result

    # Method for searhing multiple songs based on user input. The user is required to enter the song that should be played.
    async def advanced_search(self, user_voice_ch_id, user_server_id, results_number):
        await client.send_message(self.message.channel, 'Feature in BETA! Incep cautarea avansata...')
        returned_youtube_url = await self.search_youtube_url(user_server_id, results_number)
        counter = 0
        song_name_dict = {}
        server_songs_name = song_name_dict[user_server_id] = []
        if returned_youtube_url:
            if len(returned_youtube_url) >= results_number:
                for links in returned_youtube_url:
                    html_source = requests.get(returned_youtube_url[counter]).text
                    Youtube_query = BeautifulSoup(html_source, 'lxml').title.text
                    server_songs_name.append('{}. {}'.format(str(counter + 1), Youtube_query))
                    counter += 1
                    if len(server_songs_name) == results_number:
                        await client.send_message(self.message.channel, 'Am gasit: \n{} .\nAlege una dintre melodii prin a scrie ".alege" si numarul asociat melodiei. 60 de secunde la dispozitie...'.format('\n'.join(server_songs_name)))
                        user_message = await client.wait_for_message(timeout=60, author = self.message.author)
                        if user_message.content.startswith('.alege'):
                            song_index = user_message.content.replace('.alege', '').strip()
                            try:
                                list_index = int(song_index)
                                if list_index <= len(returned_youtube_url):
                                    is_possible = True
                                else:
                                    await client.send_message(self.message.channel, 'Marimea conteaza, dar nu o supraestima. Index-ul este prea mare!')
                            except:
                                is_possible = False

                            if is_possible:
                                await YoutubePlayer(returned_youtube_url[list_index - 1], user_voice_ch_id, user_server_id, self.message).play_youtube_url()
                            else:
                                await client.send_message(self.message.server, 'Imi trebuie numarul melodiei, te roog.')
            else:
                await client.send_message(self.message.channel, 'Nu exista suficiente rezultate pentru o cautare avansata. Te rog sa formulezi alt keyword sau sa folosesti cautarea simpla.(".muzica + keyword")')
        else:
            await client.send_message(self.message.channel, 'Imi pare rau, nu s-a gasit nici un rezultat pe youtube cu un astfel de keyword.')

        

class Playlist(YoutubePlayer):
    queue_dict = {}
    owner_dict = {}

    @classmethod
    def add_to_playlist(cls, server, song, message):
        if not cls.queue_dict.get(server):
            cls.queue_dict[server] = [song]
            cls.owner_dict[server] = [message.author]
        else:
            cls.queue_dict[server].append(song)
            cls.owner_dict[server].append(message.author)
        

class ForceExit(YoutubePlayer):
    def __init__(self, youtube_url, user_voice_ch_id, user_server_id, message):
        super().__init__(youtube_url, user_voice_ch_id, user_server_id, message)

    async def voice_force_exit(self, clear_queue):
        # I'm sad. You didn't liked my personality, so I'm leaving
        check_conn = await self.create_voice_object(False)
        if not check_conn:
            if await self.democracy(self.message, False):
                get_voice_object = YoutubePlayer.voice_dict[self.user_server_id]
                await exit_voice_channel(1, get_voice_object)
                if clear_queue:
                    if Playlist.queue_dict.get(self.user_server_id):
                        if len(Playlist.queue_dict[self.user_server_id]) > 0:
                            Playlist.queue_dict.pop(self.user_server_id)
                            Playlist.owner_dict.pop(self.user_server_id)
                    self.destroy_youtube_player()
        else:
            await client.send_message(self.message.channel, 'Nu sunt conectat la un voice channel. ')
            await exit_voice_channel(1, check_conn)
            return
        
            
async def play_audio_file(audio_file, get_voice_channel_id, audio_duration):
    try:
        voice = await client.join_voice_channel(get_voice_channel_id)
        player = voice.create_ffmpeg_player(audio_file)
        player.start()
        await exit_voice_channel(audio_duration, voice)
    except:
        return False


async def exit_voice_channel(exit_time, voice_connection):
    await asyncio.sleep(exit_time)
    await voice_connection.disconnect()


def random_int_gen(input_number1, input_number2):
    output_rand = random.randrange(input_number1, input_number2)
    return output_rand
            

def reset_jokes():
    #Acces the variables declared uptop.
    global said_1
    global said_2
    global said_3
    global said_4
    global said_5
    global said_6
    global said_7
    global said_8
    global said_9

    # If all the jokes were said...

    if said_1 == True and said_2 == True and said_3 == True and said_4 == True and said_5 == True and said_6 == True and said_7 == True and said_8 == True :
        # Than reset the booleans to False, in order to say the same jokes again... I know, this bot is all a joke...
        said_1 = False
        said_2 = False
        said_3 = False
        said_4 = False
        said_5 = False
        said_6 = False
        said_7 = False
        said_8 = False
        said_9 = False

      
# When the user types a command...

@client.event
async def on_message(message):

    try:
        info = GetInfo(message.author.voice_channel.id, message.author.server.id, message)
        could_get_user_info = True
    except AttributeError:
        could_get_user_info = False

    if message.content.startswith('.test'):
        test = await client.send_message(message.channel, "Da, functionez!")
        
    elif message.content.startswith('.debug'):
        await YoutubeSearch('maica-ta', message).search_youtube_url(info.user_server_id, 5)

    elif message.content.startswith('.vot'):
        
        context = YoutubePlayer(None, info.user_voice_ch_id, info.user_server_id, message)
        if not context.user_votes.get(info.user_server_id) and context.voice_dict.get(info.user_server_id):
            context.user_votes[info.user_server_id] = [message.author]
        elif context.user_votes.get(info.user_server_id) and context.voice_dict.get(info.user_server_id):
            counter = 0
            for votes in context.user_votes[info.user_server_id]: # Checks if the vote is duplicate
                if context.user_votes[info.user_server_id][counter] == message.author:
                    await client.send_message(info.message.channel, 'Ai votat deja.')
                    return
                else:
                    counter += 1
            else:
                context.user_votes[info.user_server_id].append(message.author)
        
        else:
            await client.send_message(info.message.channel, 'Esti cetatean European si ai drepturi, dar acum n-ai ce sa votezi.')

    elif message.content.startswith('.amuzant'):
        start_playing_file = await play_audio_file('amuzant.mp3', info.channel, 5)
        if not start_playing_file:
            await client.send_message(message.channel, 'Sunt un simplu bot, nu pot sa intru in voice channel inca o data.')

    elif message.content.startswith('.taie'):
        start_playing_file = await play_audio_file('taie.mp3', info.channel, 3)
        if not start_playing_file:
            await client.send_message(message.channel, 'Sunt un simplu bot, nu pot sa intru in voice channel inca o data.')

    elif message.content.startswith('.muzica'):
        if not could_get_user_info:
            await client.send_message(message.channel, 'Nu sunt suficient de inteligent pentru a-mi da seama in ce voice channel ar trebui sa intru daca nu esti conectat la unul. Te rog conecteaza-te si invoca-ma din nou, sunt pregatit sa petrecem.')
            return False
            
        output_url = info.message_content.replace('.muzica', '').strip()
        if output_url == '':
            await client.send_message(message.channel, 'Te rog indica-mi ce melodie trebuie sa pun, ori introducand cuvintele cheie pentru o cautare pe YouTube, ori printr-un link.')
        elif output_url.startswith('-s'):
            final_user_keyword = output_url.replace('-s', '').strip()
            await YoutubeSearch(final_user_keyword, info.message).advanced_search(info.user_voice_ch_id ,info.user_server_id, 5)

        elif output_url.startswith('https://www.youtube.com/watch?v=') or output_url.startswith('http://www.youtube.com/watch?v=') or output_url.startswith('https://youtu.be/') or output_url.startswith('http://youtu.be/'):
            await YoutubePlayer(output_url, info.user_voice_ch_id, info.user_server_id, message).play_youtube_url() 

        else:
            await client.send_message(message.channel, 'Caut pe YouTube: "{}"'.format(output_url))
            returned_youtube_url = await YoutubeSearch(output_url, message).search_youtube_url(info.user_server_id, 1)
            await YoutubePlayer(returned_youtube_url, info.user_voice_ch_id, info.user_server_id, message).play_youtube_url()
             

    elif message.content.startswith('.versiune'):
        global version
        await client.send_message(message.channel, 'RoBot v. {} Discord.py API v. {}'.format(version, discord.__version__))

    elif message.content.startswith('.jet'):
        await ForceExit(None, info.user_voice_ch_id, info.user_server_id, message).voice_force_exit(True)

    elif message.content.startswith('.sari'):
        await YoutubePlayer(None, info.user_voice_ch_id, info.user_server_id, message).skip_song()   
        
    elif message.content.startswith('.playlist'):
        await YoutubePlayer(None, info.user_voice_ch_id, info.user_server_id, message).output_trakcs()

    elif message.content.startswith('.sterge'):
        usr_input = message.content.replace('.sterge', '').strip()
        if usr_input != '':
            remove = await YoutubePlayer(None, info.user_voice_ch_id, info.user_server_id, message).remove_song(usr_input)
            if remove:
                await client.send_message(info.message.channel, 'Am sters: {}'.format(remove)) 
        else:
            await client.send_message(info.message.channel, 'Te rog sa imi spui ce vrei sa sterg.')

    elif message.content.startswith('.pauza'):
        await YoutubePlayer(None, info.user_voice_ch_id, info.user_server_id, message).pause_song()
           
        
    elif message.content.startswith('.gluma'):
        random_joke = random_int_gen(1, 9)
        reset_jokes()
        global said_1
        global said_2
        global said_3
        global said_4
        global said_5                
        global said_6
        global said_7
        global said_8
        global said_9

        # If the same random number was generated, generate another in order for the bot to respond

        while random_joke == 1 and said_1 == True or random_joke == 2 and said_2 == True or random_joke == 3 and said_3 == True or random_joke == 4 and said_4 == True or random_joke == 5 and said_5 == True or random_joke == 6 and said_6 == True or random_joke ==7 and said_7 == True or random_joke == 8 and said_8 == True:       
            random_joke = random_int_gen(1, 9)
        # When the user types more than one ".gluma" command, do not repeat the joke.
        if random_joke == 1 and said_1 == False :
            #The first joke
            await client.send_message(message.channel, 'Cum face masina de politie a dinozaurilor? NINO NINO DANONINO, Dar cea de pompieri? NINO NINO FireDINO')
            said_1 = True
                        
        elif random_joke == 2 and said_2 == False :
            
            await client.send_message(message.channel, 'De ce nu alearga melcul ?!?')
            await asyncio.sleep(2)
            await client.send_message(message.channel, 'Pentru ca ii falfaie ochii')
            said_2 = True
            
            
        elif random_joke == 3 and said_3 == False :
            await client.send_message(message.channel, 'De ce nu se uita melcul in priza?')
            await asyncio.sleep(2)
            await client.send_message(message.channel, 'Pentru ca se curenteaza')
            said_3 = True
            

        elif random_joke == 4 and said_4 == False :
            await client.send_message(message.channel, 'Tata, pot face baie daca am diaree?')
            await asyncio.sleep(2)
            await client.send_message(message.channel, 'Da, daca ai destula')
            said_4 = True
          

        elif random_joke == 5 and said_5 == False :
            await client.send_message(message.channel, 'Era seara iar Alina trebuia sa faca baie, dar ii era lene... ')
            await asyncio.sleep(1)
            await client.send_message(message.channel, 'Mama: -Alina, de ce nu vrei sa faci baie?')
            await asyncio.sleep(2)
            await client.send_message(message.channel, 'Alina: Pentru ca e uda')
            said_5 = True
            
        
        elif random_joke == 6 and said_6 == False:
            await client.send_message(message.channel, 'Alexandra: -Mama, tata s-a imbatat')
            await asyncio.sleep(1)
            await client.send_message(message.channel, 'Mama: -De unde stii?')
            await asyncio.sleep(1)
            await client.send_message(message.channel, 'Alexandra: -Barbiereste oglinda din baie')
            said_6 = True
            

        elif random_joke == 7 and said_7 == False :
            await client.send_message(message.channel, '-Alex, stii bancul cu ieputele din baie?')
            await asyncio.sleep(1)
            await client.send_message(message.channel, 'Alex: -Nu')
            await asyncio.sleep(1)
            await client.send_message(message.channel, 'Nici eu, era usa inchisa...')
            said_7 = True
           

        elif random_joke == 8 and said_8 == False:
            await client.send_message(message.channel, 'Stii ce face ursul dupa ce se trezeste din hibernat?')
            await asyncio.sleep(2)
            await client.send_message(message.channel, 'Fute o laba')
            said_8 = True

    elif message.content.startswith('.comenzi'):
        await client.send_message(message.channel, 'Comenzi: \n .test - Verifica daca functionez. \n .amuzant - Bot-ul intra in voice channel-ul in care se afla si utilizatorul care a invocat bot-ul \n si reda un material audio(recomandabil folosita in cazul in care un memnru din server face o gluma proasta) \n .gluma - Nu mai este nevoie de explicatie \n .muzi_youtube / cuvant cheie - bot-ul insta in voice channel-ul in care se afla \n si utilizatorul care l-a invocat si reda audio-u mentionat.')
               
# Run the bot. Put your own discord Token code in 'quotes'.

client.run('Your TOKEN')
