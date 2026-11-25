---
title: "Capturing Facebook OAuth tokens through iOS custom URL schemes"
category: "Web Security"
tags: [web-security, oauth, ios, facebook, bug-bounty]
read_time: "5 min read"
thumb: fboauth-thumb
dek: "Facebook Login sent access tokens back to iOS apps through a custom URL scheme built from the app ID, and any iOS app can claim any URL scheme. Facebook allowed that redirect even for apps that had no iOS app at all. Facebook paid a $1,000 bounty."
---

In early 2015 I reported an issue in how Facebook Login handed OAuth access tokens back to iOS apps. A malicious app on the phone could pose as any Facebook Platform app, including one with no iOS app at all, and receive the access token meant for that app. Facebook Security agreed it was worth fixing part of it and paid a $1,000 bounty.

## How Facebook Login returned to iOS apps

When an iOS app uses Facebook Login, the login happens outside the app, in Safari or the Facebook app. When it finishes, Facebook needs a way to hand the result back to the app that asked. On iOS that's done with a custom URL scheme. Every Facebook app gets one derived from its app ID:

```
fb<APP_ID>://authorize
```

The app registers `fb<APP_ID>` as a URL scheme in its `Info.plist`, Facebook redirects to `fb<APP_ID>://authorize#access_token=...`, and iOS opens the app with that URL, token included.

The problem is what iOS guarantees about custom URL schemes: nothing. No one owns a scheme. Any app can declare any scheme in its `Info.plist`. If two installed apps claim the same one, which app gets opened isn't defined.

{% include fig.html name="fboauth-routing" num="1" caption="Where iOS delivers the token redirect. When the target app has no iOS app, the malicious app is the only one claiming the scheme, so it always wins." %}

## The attack

App IDs aren't secret. They show up in login URLs and page source for any site or app that uses Facebook Login. So:

1. A malicious iOS app registers the URL scheme `fb<APP_ID>`, where `APP_ID` belongs to some other Facebook app, the target.
2. The malicious app opens the Facebook OAuth dialog for the target app, with `redirect_uri=fb<APP_ID>://authorize`.
3. The user sees a login dialog for the target app, which is a real app with its real name on it, and logs in.
4. Facebook redirects to `fb<APP_ID>://authorize` with the access token in the URL.
5. iOS opens the app that claimed that scheme, the malicious one, and it reads the token.

{% include fig.html name="fboauth-sequence" num="2" caption="The full attack. Steps 1 to 4 are an ordinary Facebook Login for the target app; the token goes astray at steps 5 to 7." %}

The malicious app now holds the user's access token for the target app, with whatever permissions the target app was granted, and can call the Graph API as that app on the user's behalf.

The part that made this worse: the target didn't need to be an iOS app. Facebook accepted the `fb<APP_ID>://` mobile redirect for every app, including apps that had never said they supported a mobile interface. A website that only ever used Facebook Login on the web could still have its tokens sent to whichever iOS app claimed its scheme. If the real app isn't on the phone, the malicious one is the only app claiming the scheme, so there's no ambiguity about where the token goes.

## What the malicious app looks like

The attacking app needs very little. This is a reconstruction for illustration, not my original PoC: `123456789` stands in for the target's app ID, and the code is Objective-C from that era.

Claim the target's scheme in `Info.plist`:

```xml
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleURLSchemes</key>
    <array>
      <string>fb123456789</string>
    </array>
  </dict>
</array>
```

Open the target's login dialog, then wait for iOS to hand back the redirect:

```objc
// Steps 1-2: open Facebook's OAuth dialog for the target app
NSString *dialog = @"https://m.facebook.com/dialog/oauth"
                    "?client_id=123456789"
                    "&redirect_uri=fb123456789%3A%2F%2Fauthorize"
                    "&response_type=token";
[[UIApplication sharedApplication] openURL:[NSURL URLWithString:dialog]];

// Step 7: iOS opens us, because we claimed fb123456789
- (BOOL)application:(UIApplication *)application
            openURL:(NSURL *)url
  sourceApplication:(NSString *)sourceApplication
         annotation:(id)annotation {
    // url is fb123456789://authorize#access_token=...&expires_in=...
    NSLog(@"captured: %@", url.fragment);
    return YES;
}
```

That's the whole attack: one string in `Info.plist` and one URL. Nothing in it needs the target app's secret, and nothing ties the redirect back to the app that asked for it.

## Facebook's response

Facebook's security team worked through it with the Platform team. Their conclusion had two parts.

On the general problem, they considered it hard to fully lock down. OAuth has no concept of a "platform specific" return URI, and custom URL schemes are just how the mobile ecosystem works. If they saw an app doing this in the wild to impersonate a Platform app, they said they could lock down the affected Facebook app and work with Apple and Google against the abusive app. Taken together, they considered the risk fairly well mitigated.

On the specific gap, they agreed. My report showed that Facebook enabled mobile redirect URIs even for apps that hadn't indicated mobile support, and they said they planned to look at locking that down. That's what the bounty was for: $1,000.

## Timeline

- **Early 2015:** reported to Facebook as "oauth token capture due to custom url scheme in ios apps".
- **February 2015:** I followed up asking for an update.
- **27 February 2015:** Facebook replied with their findings and awarded a $1,000 bounty, asking that I not discuss the details until the issue had been patched.
