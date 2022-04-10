def get_env_data_as_dict(path: str) -> dict:
    f = open('.env')
    lines = f.readlines()
    env_dict = {}
    for line in lines:
        if not line.startswith('#') or not line.strip():
            key, value = line.strip().split('=')
            env_dict[key] = value
    return env_dict


import discord
from bs4 import BeautifulSoup
import requests
import random

client = discord.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('$movie'):
        msg = message.content
        words = msg.replace('$movie', '').split(' ')
        cmd_words = [cmd_word for cmd_word in words if cmd_word.strip()]
        if len(cmd_words) == 0 or '-help' in cmd_words:
            await message.channel.send('help message\nmultiline')
            return
        genre = cmd_words[0]
        if '-' in genre:
            genre = cmd_words[0].replace('-', ',')
        embed = get_movie(genre)
        # time_start = cmd_words[1]
        # time_end = cmd_words[2]
        # imdb_min_rating = cmd_words[3]
        await message.channel.send(embed=embed)


def get_movie(genre):
    start = random.randint(1, 200)
    page = requests.get('https://www.imdb.com/search/title/?title_type=feature&genres={}&start={}&ref_=adv_nxt'.format(
        genre,start))  # Getting page HTML through request
    soup = BeautifulSoup(page.content, 'html.parser')  # Parsing content using beautifulsoup
    movies = soup.find_all('div', class_="lister-item mode-advanced")
    movie = movies[random.randint(0, 49)]
    title_anchor = movie.find_next('div', class_="lister-item-content").find_next('a')
    movie_name = title_anchor.get_text(strip=True)
    movie_imdb_link = 'https://www.imdb.com/' + title_anchor.attrs['href']
    movie_thumbnail = movie.find_next('a').find_next('img').attrs['loadlate']
    movie_rating = movie.find_next('span', class_="global-sprite rating-star imdb-rating").find_next('strong').get_text()
    movie_metascore = movie.find_next('div', class_="inline-block ratings-metascore").find_next('span').get_text()
    movie_details_elem = movie.find_all_next('p')
    movie_details = ""
    for elem in movie_details_elem[0].find_all('span'):
        text = elem.get_text().strip()
        if not text == '|':
            movie_details += text + ' | '
    movie_details = movie_details[0:-3]
    movie_plot = movie_details_elem[1].get_text()
    movie_directors = ""
    movie_actors = ""
    span_ghost = movie_details_elem[2].find_next('span', class_="ghost")
    for anchor in span_ghost.find_previous_siblings('a'):
        movie_directors += "[{}](https://www.imdb.com/{})".format(anchor.get_text(), anchor.attrs['href']) + ' | '
    for anchor in span_ghost.find_next_siblings('a'):
        movie_actors += "[{}](https://www.imdb.com/{})".format(anchor.get_text(), anchor.attrs['href']) + ' | '
    movie_directors = movie_directors[:-3]
    movie_actors = movie_actors[:-3]
    movie_details_elem = movie.find_all_next('span', attrs={'name':'nv'})
    movie_votes = movie_details_elem[0].get_text()
    movie_gross = movie_details_elem[1].get_text()
    embed = discord.Embed()  # any kwargs you want here
    page = requests.get(movie_imdb_link)
    soup = BeautifulSoup(page.content, 'html.parser')  # Parsing content using beautifulsoup
    trailer_elem = soup.find('a', class_='ipc-lockup-overlay sc-5ea2f380-2 gdvnDB hero-media__slate-overlay ipc-focusable')
    movie_trailer = 'https://www.imdb.com/' + trailer_elem.attrs['href']
    embed.description = "** Your OneMovie Recommendation **"
    embed.set_image(url=movie_thumbnail)
    embed.add_field(name="\u200b", value="**[{}]({})**".format(movie_name, movie_imdb_link), inline=False)
    embed.add_field(name="\u200b", value="**[Trailer]({})**".format(movie_trailer), inline=False)
    embed.add_field(name="\u200b", value="**{}**".format(movie_details), inline=False)
    embed.add_field(name="\u200b", value="** Plot: **{}".format(movie_plot), inline=False)
    embed.add_field(name="\u200b", value="**IMDB Rating:** {}  ⭐".format(movie_rating), inline=False)
    embed.add_field(name="\u200b", value="**Metascore:** {}  ⭐".format(movie_metascore), inline=False)
    embed.add_field(name="\u200b", value="**Director(s):** {}".format(movie_directors), inline=False)
    embed.add_field(name="\u200b", value="**Actor(s):** {}".format(movie_actors), inline=False)
    embed.add_field(name="\u200b", value="**Votes:** {} | **Gross:** {}".format(movie_votes, movie_gross), inline=False)
    return embed


token = get_env_data_as_dict('.env')['TOKEN']
client.run(token)