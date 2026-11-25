---
title: "Stored XSS in iCloud Notes"
category: "Web Security"
tags: [web-security, xss, apple, icloud]
read_time: "4 min read"
dek: "In 2014, iCloud Notes on icloud.com turned anything that looked like scheme:/something into a clickable link, including javascript: URLs. A line break hidden behind a // comment was enough to get script running on icloud.com without touching a proxy."
---

This one goes back to October 2014. I was poking at the web version of iCloud Notes at `icloud.com/#notes`, in Firefox, and found a way to store a `javascript:` link inside a note that ran on `icloud.com` when clicked. I reported it to Apple Product Security on 4 October 2014. Here's how it worked and how the report went.

## How Notes turned text into links

Notes had an auto-linker. As you typed, JavaScript on the page turned anything that looked like a URL into a link, and every keystroke fired an AJAX request that saved the note to the server.

So I started feeding it things to see what it would and wouldn't link:

- `www.SOMETHING` became a link, as long as it started with `www.`
- `http://SOMETHING` became a link
- `SOMETHING://SOMETHING` became a link
- `SOMETHING:/SOMETHING` became a link
- `SOMETHING:SOMETHING` did not

The rule looked like "any scheme, as long as a slash follows the colon". It didn't check which scheme, which means `javascript:` was fair game. The only thing in the way was the slash, because `javascript:alert(0)` has no slash after the colon and was left as plain text.

## First version: the slash and a proxy

I typed `javascript:/alert(0)`. Notes happily linked it, and the save request carried:

```html
<a href='javascript:/alert(0)'>
```

That link doesn't do anything useful on its own: `/alert(0)` isn't valid JavaScript. But the link was built on the client and sent to the server in the save request, so I caught that request in an intercepting proxy and edited it to:

```html
<a href='javascript:alert(0)'>
```

The server accepted it and the JSON response came back successful. The note now held a working `javascript:` link. Swapping `alert(0)` for `alert(document.cookie)` showed it running with access to the page's cookies. That's what I sent in the first report.

## Second version: no proxy needed

Needing a proxy to edit the request made the bug weaker than it should be, so I kept going. On 20 November I sent Apple a version that works from the note editor alone:

```
javascript://%0D%0Aalert(document.domain)+20/10
```

This passes the auto-linker because it has `://` after the scheme. When the link is clicked, the browser URL-decodes everything after `javascript:` and runs it as script:

- `//` starts a JavaScript comment, so whatever follows on that line is ignored.
- `%0D%0A` decodes to a carriage return and line feed, which ends the comment.
- `alert(document.domain)+20/10` sits on the next line and runs. The `+20/10` is plain arithmetic hanging off the end, and it makes the whole thing read a bit more like a URL.

Because the link is saved into the note, it stays there and fires on `icloud.com` every time it's clicked. In the video, the `document.cookie` version pops an alert with the session cookies, including `X-APPLE-WEB-ID` and `X-APPLE-WEBAUTH-VALIDATE`, and the `document.domain` version shows `www.icloud.com`.

## Video

This is the proof of concept I sent with the second report, recorded on 20 November 2014. It shows the links in a note, the cookie alert, and the `document.domain` alert. One note title in the sidebar has been covered up because it contained personal details.

<video class="post-video" controls preload="metadata" playsinline poster="{{ '/assets/video/icloud-notes-xss.jpg' | relative_url }}">
  <source src="{{ '/assets/video/icloud-notes-xss.mp4' | relative_url }}" type="video/mp4">
  <a href="{{ '/assets/video/icloud-notes-xss.mp4' | relative_url }}">Download the video (MP4, 1.3 MB)</a>
</video>

## Timeline

- **4 October 2014:** reported to Apple Product Security.
- **15 October 2014:** a security analyst confirmed the report was being investigated and asked me to keep it private in the meantime.
- **20 November 2014:** sent the no-proxy payload and the video.
- **21 November 2014:** Apple replied that they were still investigating and asked me not to disclose until any updates were available.
- **24 November 2014:** asked for a status update, and whether there was a reward or hall of fame credit.
- **29 November 2014:** Apple asked whether I could still reproduce the issue. I couldn't.
- **3 December 2014:** told Apple I could no longer reproduce it and the issue could be closed.
- **8 December 2014:** asked when I'd be listed in Apple's hall of fame.
- **12 December 2014:** Apple replied that they credit researchers after an issue has been fully addressed.

That's where the thread ends.
