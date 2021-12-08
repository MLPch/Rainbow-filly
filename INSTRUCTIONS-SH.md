### Instructions for quick commands

### Concept
All quick commands are bash scripts, in which the commands are simplified for convenience and ease of managing the docker and the container with the bot.
You can work with docker directly if it is convenient for you.
The terminal entry point should be located in the root folder of the bot.
The `./sh/_NAME` file specifies the name for the image and container being created. Change them if required.
#### Common view of the command:
```bash
bash ./sh/[command]
```
#### In order to build a suitable image for the bot, run the command:
```bash
bash ./sh/build
```
For further work of the bot, you need to register the mounting points, as well as create and demonize its container. 
#### For the first run, use the command:
```bash
bash ./sh/run
```
The bot will be ready and running now.
#### In order to stop the container from working with the bot, use the command:
```bash
bash ./sh/stop
```
#### In the future, to launch the bot, you must use the command:
```bash
bash ./sh/start
```
#### In order to launch a container with a bot and monitor its execution log, use the command:
```bash
bash ./sh/start-log
```
#### You can also connect to an already running container and access the terminal of the running container with the command:
```bash
bash ./sh/t
```
#### If you want to restart the container use the command:
```bash
bash ./sh/restart
```
#### In order for the container to start automatically after restarting the host system, use the command:
```bash
bash ./sh/unstoppable
```
#### To stop and delete containers, use the command:
```bash
bash ./sh/del
```
#### To delete all images associated with the name specified in the `_NAME` file, use the command:
```bash
bash ./sh/del-all-images
```
### Automatic commands
These commands are used when you need to assemble the container for the first time and launch the bot. Or reassembly of the image and the container as a whole.
#### To simply create an image and then a container and launch the bot, use the command:
```bash
bash ./sh/auto-build
```
#### To completely delete all containers associated with the bot, as well as images, use the command:
```bash
bash ./sh/auto-del
```
#### To completely remove the container and image, and then simply build and run them, use the command:
```bash
bash ./sh/auto-rebuild
```
