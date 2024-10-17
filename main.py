import discord
from bs4 import BeautifulSoup
import requests
import random
import re
# 2147489856

def get_env_data_as_dict(path: str) -> dict:
    f = open('.env')
    lines = f.readlines()
    env_dict = {}
    for line in lines:
        if not line.startswith('#') or not line.strip():
            key, value = line.strip().split('=')
            env_dict[key] = value
    return env_dict

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('$movie'):
        msg = message.content
        pattern = re.compile(r"^\$movie(?: (?:\w+(?:,\w+)*|\w+(?:-\w+)*|-help))?$")
        if not pattern.match(msg):
            embed = discord.Embed(description="")
            embed.set_image(url="https://media.giphy.com/media/Ll2fajzk9DgaY/giphy.gif")
            await message.channel.send(embed=embed)        
            return
        words = msg.replace('$movie', '').split(' ')
        cmd_words = [cmd_word for cmd_word in words if cmd_word.strip()]
        if len(cmd_words) == 0 or '-help' in cmd_words:
            await message.channel.send('Send "$movie<space>genre1,genre2,genre3" or '
                                        '"$movie<space>genre1-genre2" to get your movie recommendation. The genres '
                                        'can be from 1(min) to 3(max).\nExample commands: '
                                        '$movie action, $movie action-comedy '
                                        'or $movie action,comedy,romance.\nSend $movie or $movie -help for help.')
            return
        genre = cmd_words[0]
        if '-' in genre:
            genre = cmd_words[0].replace('-', ',')
        if len(genre.split(','))> 3:
            await message.channel.send("Maximum genre is 3, please try with less genre combination.")
            return

        try:
            embed = get_movie(genre)
            await message.channel.send(embed=embed)
        except Exception as e:
            await message.channel.send(f"```FATAL ERROR! {e}```")





def get_movie(genre):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    page = requests.get(f'https://www.imdb.com/search/title/?title_type=feature&genres={genre}', headers=headers)  # Getting page HTML through request
    soup = BeautifulSoup(page.content, 'html.parser')  # Parsing content using beautifulsoup
    movies = soup.find_all('div', class_="sc-59c7dc1-3 dVCPce dli-parent")
    if not len(movies):
        raise Exception("No movies found!")
    movie = movies[random.randint(0, len(movies) - 1)]
    # checking if movie has an IMDB rating, otherwise getting a different movie
    movie_rating_elem = movie.find_next('span', class_="ipc-rating-star--rating")
    while not movie_rating_elem:
        movie = movies[random.randint(0, len(movies) - 1)]
        movie_rating_elem = movie.find_next('span', class_="ipc-rating-star--rating")
    movie_vote_elem = movie.find_next('span', class_="ipc-rating-star--voteCount")
    movie_info = {}
    movie_info['movie_rating'] = movie_rating_elem.get_text() + f" ({movie_vote_elem.get_text(strip=True)[1:-1]}) votes"
    title_anchor = movie.find_next('a', class_="ipc-title-link-wrapper")   
    movie_info['movie_name'] = title_anchor.find_next('h3', class_="ipc-title__text").get_text(strip=True)[4:]
    movie_info['movie_imdb_link'] = 'https://www.imdb.com/' + title_anchor.attrs['href']
    movie_info['movie_thumbnail'] = movie.find_next('img').attrs['src']
    movie_meta_elem = movie.find_next('span', class_="metacritic-score-box")
    movie_info['movie_meta'] = movie_meta_elem.get_text() if movie_meta_elem else "Not Available"
    movie_details_elem = movie.find_next('div', 'dli-title-metadata')
    movie_info['movie_details'] = ""
    for elem in movie_details_elem.find_all('span'):
        text = elem.get_text().strip()
        movie_info['movie_details'] += text + ' | '        
    movie_info['movie_details'] = movie_info['movie_details'][0:-3] 
    movie_info['movie_plot'] = movie.find_next("div", "ipc-html-content-inner-div").get_text()
    page = requests.get(movie_info['movie_imdb_link'], headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')  # Parsing content using beautifulsoup
    trailer_elem = soup.find('a', href=re.compile("video"))
    movie_info['movie_trailer'] = 'https://www.imdb.com/' + trailer_elem.attrs['href'] if trailer_elem else "I can't find the trailer :("
    def get_movie_personnel(per_type:str):
        if not per_type.endswith('s'):
            per_type += 's?'
        else:
            per_type += '?'
        movie_persons_elem = soup.find('span', string=re.compile(per_type))
        if movie_persons_elem is None:
            movie_persons_elem = soup.find('a', string=re.compile(per_type))
        movie_persons_elem = movie_persons_elem.find_next().contents[0].contents
        movie_persons = ""
        for person in  movie_persons_elem :
            anchor = person.find('a')
            movie_persons += "[{}](https://www.imdb.com/{})".format(anchor.get_text(), anchor.attrs['href']) + ' | '
        movie_persons = movie_persons[:-3]
        return movie_persons

    movie_info['directors'] = get_movie_personnel("Directors")
    movie_info['stars'] = get_movie_personnel("Stars")
    movie_info['writers'] = get_movie_personnel("Writers")

    movie_gross_elem = soup.find('span', string='Gross worldwide')
    if movie_gross_elem:
        movie_info['movie_gross']  = movie_gross_elem.find_next().find('span', class_="ipc-metadata-list-item__list-content-item").get_text()
    else:
        movie_info['movie_gross'] = "I don't think this novie is released yet..."
    embed = discord.Embed()  # any kwargs you want here
    embed.description = "** Your OneMovie Recommendation **"
    embed.set_image(url=movie_info['movie_thumbnail'])
    embed.add_field(name="\u200b", value=f"**[{movie_info['movie_name']}]({ movie_info['movie_imdb_link']})**", inline=False)
    embed.add_field(name="\u200b", value=f"**[Trailer]({movie_info['movie_trailer']})**", inline=False)
    embed.add_field(name="\u200b", value=f"**{movie_info['movie_details']}**", inline=False)
    embed.add_field(name="\u200b", value=f"** Plot: **{movie_info['movie_plot']}", inline=False)
    embed.add_field(name="\u200b", value=f"**IMDB Rating:** {movie_info['movie_rating']}  ⭐", inline=False)
    embed.add_field(name="\u200b", value=f"**Metascore:** {movie_info['movie_meta']}  ⭐", inline=False)
    embed.add_field(name="\u200b", value=f"**Director(s):** {movie_info['directors']}", inline=False)
    embed.add_field(name="\u200b", value=f"**Star(s):** {movie_info['stars']}", inline=False)
    embed.add_field(name="\u200b", value=f"**Gross (Worldwide):** {movie_info['movie_gross']}", inline=False)
    return embed


token = get_env_data_as_dict('.env')['TOKEN']
client.run(token)
