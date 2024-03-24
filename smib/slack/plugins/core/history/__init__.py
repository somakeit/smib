from injectable import inject
from slack_bolt import App

app: App = inject(App)


@app.message('hello there')
def hello_there(message, say):
    say(text='General Kenobi', channel=message['channel'])


@app.message('test')
def hello_there(message, say):
    say(text='testing testicle', channel=message['channel'])