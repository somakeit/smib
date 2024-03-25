from injectable import inject
from slack_bolt import App

app: App = inject(App)


@app.message('hello there')
def hello_there(message, say):
    say(text='General Kenobi', channel=message['channel'])


def ack_within_3_seconds(ack):
    ack()


@app.message('test')(ack=ack_within_3_seconds)
def test(message, say, ack):
    ack()
    say(text='testing testicle', channel=message['channel'])
    1/0


# app.message('test')(lazy=[test], ack=ack_within_3_seconds)