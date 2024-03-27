from pprint import pprint, pp

from injectable import inject
from slack_bolt import App

app: App = inject(App)


@app.message('hello there')
def hello_there(message, say):
    say(text='General Kenobi', channel=message['channel'])


def ack_within_3_seconds(ack):
    ack()


@app.message('test')
def test(message, say, ack):
    ack()
    say(text='testing testicle', channel=message['channel'])


@app.event('http_get_zero')
def get_zero(event, say):
    say(channel='random', text='zero')
    1 / 0

@app.event('http_get_test')
def get_zero(event, say, resp):
    say(channel='random', text="testing 123")
    print(resp)

# app.message('test')(lazy=[test], ack=ack_within_3_seconds)
