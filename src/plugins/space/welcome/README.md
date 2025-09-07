# How to change the welcome message
The welcome message is defined in the `welcome.json` file in the `src/plugins/space/welcome` directory.
It is in the Slack Blocks format, and you can build your own/modify this one in the [Slack Block Kit Builder](https://app.slack.com/block-kit-builder).

To add import the `welcome.json` message into the Slack Block Kit Builder:
1. Copy the entire json file into the text area beneath the 'blocks' json object
```json
{
  "blocks": "Paste your json here"
}
```
2. This will render the message and show any errors on the webpage
3. Modify it as you see fit
4. Copy the json back into the `welcome.json` file, remembering to remove the outer `blocks` object, leaving just the json array.


