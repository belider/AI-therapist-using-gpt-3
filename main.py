import multiprocessing
import subprocess

flask_process = multiprocessing.Process(
    target=subprocess.run,
    kwargs={
        'args': 'python3 flask_server.py',
        'shell': True
    })


bot_process = multiprocessing.Process(
    target=subprocess.run,
    kwargs={
        'args': 'python3 bot.py',
        'shell': True
    })


if __name__ == '__main__':
    flask_process.start()
    bot_process.start()