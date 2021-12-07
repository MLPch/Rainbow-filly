# Rainbow-filly-bot

Before launching the bot, configure the config file in `./data/config/`

To install, you will need Docker:
`sudo apt-get update && sudo apt-get install docker'

Don't forget to move the terminal entry point to the bot folder:
cd /home/[user dir]/Rainbow-filly-bot/

To install the bot easily, use the command:
`~bash ./sh/auto-build'

In the future, to launch the bot, use the command:
`~bash ./sh/start'

If you want the bot to track updates of artists you like, add the artist tag to the file './data/artist/list.json'
The file must have the correct json format.
The tag must correspond to how the tag is specified in the browser address bar when searching on DB without the prefix 'artist:'.
Examples:
''[
	"psfmer",
	"nendo",
	"scarlett-spectrum",
	"devil+sugar"
]''

The bot will publish new drawings appearing under these tags to the channel that you specify in the file './data/config/channel.json' in the "PAINT" key.

The './sh/' folder contains bash scripts for easy bot management. 
In the './sh/_NAME' file, specify a name for the docker image, as well as for the container. If necessary.