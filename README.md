## Rainbow-filly-bot

#### To install, you will need Docker and git
```text
git clone https://github.com/MLPch/Rainbow-filly.git
cd Rainbow-filly
```
#### Before install the bot, configure the config file in `./data/config/`

If you want the bot to track updates of artists you like, add the artist tag to the file `./data/artist/list.json`
The file must have the correct json format.

Example:
```json
[
	"artist:psfmer",
	"nendo",
	"scarlett-spectrum",
	"devil sugar"
]
```

The bot will publish new drawings appearing under these tags to the channel that you specify in the file `./data/config/channel.json` in the `"PAINT"` id.

The `./sh/` folder contains bash scripts for easy bot management. 
In the `./sh/_NAME` file, specify a name for the docker image, as well as for the container. If necessary.

#### To install the bot easily, use the command:
```text
bash ./sh/auto-build
```
#### In the future, to launch the bot, use the command:
```text
bash ./sh/start
```
#### You can read more about the commands here: [INSTRUCTIONS-SH.md](https://github.com/MLPch/Rainbow-filly/blob/main/INSTRUCTIONS-SH.md)
<p align="left">
    <a href="https://discord.gg/wGPRmEcQ6s">
        <img src="https://img.shields.io/discord/736277452481101954?color=5865F2&label=Discord&logoColor=5805F4&style=for-the-badge" alt="Discord">
</p>
