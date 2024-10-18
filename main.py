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
        msg = message.content.strip()
        cat_sub_pattern = f"(adventure|action|thriller|horror|comedy|musical|romance|drama|fantasy)"
        query_pattern = re.compile(r"^\$movie( "+cat_sub_pattern+r")((,|-)"+cat_sub_pattern+r"){0,2}$")    
        help_pattern = re.compile(r"^\$movie( -help)?$")
        if help_pattern.fullmatch(msg):            
            help_text = """Send `$movie` or `$movie -help` for help.

                           Example commands: 
                           `movie action`
                           `movie action-comedy`
                           `$movie action,comedy,romance`
                           
                           All IMDB supported categories: `adventure`, `action`, `thriller`, `horror`, `comedy`, `musical`, `romance`, `drama`, and `fantasy`"""
            embed = discord.Embed(description=help_text)
            await message.channel.send(embed=embed)
            return
        elif not query_pattern.fullmatch(msg):
            embed = discord.Embed(description="")
            embed.set_image(url="https://media.giphy.com/media/Ll2fajzk9DgaY/giphy.gif")
            await message.channel.send(embed=embed)        
            return
        else:
            embed = discord.Embed(description="Finding one movie for you...")
            embed.set_image(url='https://media.tenor.com/-7y3iwiiuW0AAAAi/load-loading.gif')
            await message.channel.send(embed=embed)        
        words = msg.replace('$movie', '').split(' ')
        cmd_words = [cmd_word for cmd_word in words if cmd_word.strip()]
        genre = cmd_words[0]
        if '-' in genre:
            genre = cmd_words[0].replace('-', ',')
        if len(genre.split(','))> 3:
            await message.channel.send("Maximum genre is 3, please try with less genre combination.")
            return

        embed = get_movie(genre)
        await message.channel.send(embed=embed)





def get_movie(genre):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    page = requests.get(f'https://www.imdb.com/search/title/?title_type=feature&genres={genre}', headers=headers)  # Getting page HTML through request
    soup = BeautifulSoup(page.content, 'html.parser')  # Parsing content using beautifulsoup
    movie_elem_list = soup.find_all('div', class_="dli-parent")
    if not len(movie_elem_list):
        raise Exception("No movies found!")
    movie_elem = movie_elem_list[random.randint(0, len(movie_elem_list) - 1)]
    # checking if movie has an IMDB rating, otherwise getting a different movie
    movie_rating_elem = movie_elem.find_next('span', class_="ipc-rating-star--rating")
    while not movie_rating_elem:
        movie_elem = movie_elem_list[random.randint(0, len(movie_elem_list) - 1)]
        movie_rating_elem = movie_elem.find_next('span', class_="ipc-rating-star--rating")
    movie_vote_elem = movie_elem.find_next('span', class_="ipc-rating-star--voteCount")
    movie = {}
    movie['movie_rating'] = movie_rating_elem.get_text() + f" ({movie_vote_elem.get_text(strip=True)[1:-1]}) votes"
    title_anchor = movie_elem.find_next('a', class_="ipc-title-link-wrapper")   
    movie['movie_name'] = title_anchor.find_next('h3', class_="ipc-title__text").get_text(strip=True)[3:]
    movie['movie_imdb_link'] = 'https://www.imdb.com/' + title_anchor.attrs['href']
    movie['movie_thumbnail'] = movie_elem.find_next('img').attrs['src']
    movie_meta_elem = movie_elem.find_next('span', class_="metacritic-score-box")
    movie['movie_meta'] = movie_meta_elem.get_text() if movie_meta_elem else "Not Available"
    movie_details_elem = movie_elem.find_next('div', 'dli-title-metadata')
    movie['movie_details'] = ""
    for elem in movie_details_elem.find_all('span'):
        text = elem.get_text().strip()
        movie['movie_details'] += text + ' | '        
    movie['movie_details'] = movie['movie_details'][0:-3] 
    movie['movie_plot'] = movie_elem.find_next("div", "ipc-html-content-inner-div").get_text()
    page = requests.get(movie['movie_imdb_link'], headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')  # Parsing content using beautifulsoup
    trailer_elem = soup.find('a', href=re.compile("video"))
    movie['movie_trailer'] = 'https://www.imdb.com/' + trailer_elem.attrs['href'] if trailer_elem else "I can't find the trailer :("
    def get_movie_personnel(per_type:str):
        try:
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
        except Exception as e:
            movie_persons = str(e)
        return movie_persons

    movie['directors'] = get_movie_personnel("Directors")
    movie['stars'] = get_movie_personnel("Stars")
    movie['writers'] = get_movie_personnel("Writers")

    movie_gross_elem = soup.find('span', string='Gross worldwide')
    if movie_gross_elem:
        movie['movie_gross']  = movie_gross_elem.find_next().find('span', class_="ipc-metadata-list-item__list-content-item").get_text()
    else:
        movie['movie_gross'] = "I don't think this movie is released yet..."
    embed = discord.Embed()  # any kwargs you want here
    embed.description = "** Your OneMovie Recommendation **"
    embed.set_image(url=movie['movie_thumbnail'])
    embed.add_field(name="\u200b", value=f"**[{movie['movie_name']}]({ movie['movie_imdb_link']})**", inline=False)
    embed.add_field(name="\u200b", value=f"**[Trailer]({movie['movie_trailer']})**", inline=False)
    embed.add_field(name="\u200b", value=f"**{movie['movie_details']}**", inline=False)
    embed.add_field(name="\u200b", value=f"** Plot: **{movie['movie_plot']}", inline=False)
    embed.add_field(name="\u200b", value=f"**IMDB Rating:** {movie['movie_rating']}  ⭐", inline=False)
    embed.add_field(name="\u200b", value=f"**Metascore:** {movie['movie_meta']}  ⭐", inline=False)
    embed.add_field(name="\u200b", value=f"**Director(s):** {movie['directors']}", inline=False)
    embed.add_field(name="\u200b", value=f"**Star(s):** {movie['stars']}", inline=False)
    embed.add_field(name="\u200b", value=f"**Gross (Worldwide):** {movie['movie_gross']}", inline=False)
    return embed


token = get_env_data_as_dict('.env')['TOKEN']
client.run(token)
