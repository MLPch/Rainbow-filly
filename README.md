## Rainbow-filly-bot

##### To install, you will need Docker and git:
```text
sudo apt-get update && sudo apt-get install docker git
git clone https://github.com/MLPch/Rainbow-filly.git
```

##### Don't forget to move the terminal entry point to the bot folder:
```text
cd Rainbow-filly
```

##### Before install the bot, configure the config file in `./data/config/`

##### To install the bot easily, use the command:
```text
bash ./sh/auto-build
```

##### In the future, to launch the bot, use the command:
```text
bash ./sh/start
```

If you want the bot to track updates of artists you like, add the artist tag to the file `./data/artist/list.json`
The file must have the correct json format.
The tag must correspond to how the tag is specified in the browser address bar when searching on DB without the prefix 'artist:'.

##### Example:
```json
[
	"psfmer",
	"nendo",
	"scarlett-spectrum",
	"devil+sugar"
]
```

The bot will publish new drawings appearing under these tags to the channel that you specify in the file `./data/config/channel.json` in the `"PAINT"` id.

The `./sh/` folder contains bash scripts for easy bot management. 
In the `./sh/_NAME` file, specify a name for the docker image, as well as for the container. If necessary.


<p align="left">
    <a href="https://discord.gg/wGPRmEcQ6s">
        <img src="https://img.shields.io/discord/736277452481101954?color=5865F2&label=Discord&logoColor=5805F4&style=for-the-badge" alt="Discord">
</p>
