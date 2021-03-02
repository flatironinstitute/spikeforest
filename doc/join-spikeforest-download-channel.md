## Joining the spikeforest-download kachery-p2p channel

After you have installed kachery-p2p and have started a kachery-p2p daemon on your computer, you can join the spikeforest-download channel by running:

```bash
kachery-p2p-join-channel https://gist.githubusercontent.com/magland/0a732d4562ec87d0f1b9baf7eed2718d/raw/spikeforest-download-channel.yaml
```

You can see which channels you have joined by running:

```bash
kachery-p2p-get-channels
```

You can leave a channel via:

```bash
kachery-p2p-leave-channel <channel-url>
```

Unless your kachery node is listed as an authorized node in the above .yaml file, you will not be able to share/upload content to the spikeforest-download channel, but you will be able to download SpikeForest data from the public nodes that are on this channel. If you are willing to volunteer to be an additional public node on this channel (to help host the SpikeForest data), please contect us and we will add your node to the list of authorized nodes.