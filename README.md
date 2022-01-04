# DJ Livestream - OBS Python Script

## OBS Companion for LNBits DJ Livestream Plugin
* Connect to any LNBits instance
* Show DJ Livestream QR Code
* Show amounts/comments from streamers' LNURL-Pay tips
* Show animations based on a tip amount.

## Setup
* open terminal & install pyenv and then python 3.9.5
`brew install pyenv`  
`CONFIGURE_OPTS=--enable-shared pyenv install 3.9.5`  
Make a note on the installed folder name e.g. `/Users/pseudozach/.pyenv/versions/3.9.5`  

* Go to OBS > Tools > Scripts > Python Settings  
Select the folder noted above `/Users/pseudozach/.pyenv/versions/3.9.5`  

* Download and unzip this repo.
Go to OBS > Tools > Scripts  
Add dj-livestream.py

* Enter required info:
LNBits URL: `https://legend.lnbits.com`  
LNBits Invoice Key: `xxx`  
Regular Tip Animation File Location: `/Users/pseudozach/Documents/obs-djlivestream/images/bitcoin.gif`
...

## Known issues
- OBS scripts are limited in what they can do and in order to show comments/animation as tips come in I considered a few options:  
Can't use SSE because there's no webserver to host js  
Can't use webhooks because dj livestream app doesn't have it.  
So we're querying lnbits /api/v1/payments every x seconds and checking the last successful payment for amount & comment. When using an old lnbits wallet with a lot of invoices this can be slow.