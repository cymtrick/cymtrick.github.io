---
title: "A Story of mishandling the Chunked Data"
category: "Web Security"
tags: [web-security, php, apache]
thumb: php-thumb
read_time: "4 min read"
dek: "How a chunked request with an oversized Content-Length made PHP's Apache handler leak the request body into the response, and the one-line fix in sapi_apache2.c."
---

First of all, What's a chunked data?

> Chunked transfer encoding is a streaming data transfer mechanism available in version 1.1 of the Hypertext Transfer Protocol (HTTP). In chunked transfer encoding, the data stream is divided into a series of non-overlapping "chunks". The chunks are sent out and received independently of one another. No knowledge of the data stream outside the currently-being-processed chunk is necessary for both the sender and the receiver at any given time.

How is the chunk processed?

> If a Transfer-Encoding field with a value of "chunked" is specified in an HTTP message (either a request sent by a client or the response from the server), the body of the message consists of an unspecified number of chunks, a terminating chunk, trailer, and a final CRLF sequence (i.e. carriage return followed by line feed).
> Each chunk starts with the number of octets of the data it embeds expressed as a hexadecimal number in ASCII followed by optional parameters (chunk extension) and a terminating CRLF sequence, followed by the chunk data. The chunk is terminated by CRLF. If chunk extensions are provided, the chunk size is terminated by a semicolon and followed by the parameters,
> each also delimited by semicolons.

What's the problem here with PHP and Apache then ?

See, Apache didn't upgrade to HTTP/2.0, which means still the Chunked Transfer Encoding exists. When header field has the option as
Transfer-Encoding: chunked and improper Content-Length that is more than required. The request body mysteriously appears in the
Response body.

The input gets into Apache's "bucket brigade", even though PHP is not sending it there directly
(in fact, it never sees the input since Apache doesn't let it to read it, throwing an error in ap_http_filter instead):

```
#0  apr_brigade_write (b=0x7f5115c18810, flush=0x5574844fcef0 <ap_filter_flush>, ctx=0x7f5115c1a548,
    str=0x557484546fc0 "<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML 2.0//EN\">\n<html><head>\n<title>", nbyte=71) at ./buckets/apr_brigade.c:433
#1  0x00005574844feebc in buffer_output (r=<optimized out>, str=<optimized out>, len=<optimized out>) at protocol.c:1898
#2  0x0000557484500d9e in ap_rvputs (r=r@entry=0x7f5115c190a0) at protocol.c:2022
#3  0x000055748452dde0 in ap_send_error_response (r=0x7f5115c190a0, recursive_error=0) at http_protocol.c:1539
#4  0x0000557484532eb6 in ap_http_header_filter (f=0x7f5115c1a570, b=0x7f5115c186e0) at http_filters.c:1335
#5  0x0000557484500832 in ap_content_length_filter (f=0x7f5115c1a548, b=0x7f5115c186e0) at protocol.c:1769
#6  0x000055748453415a in ap_byterange_filter (f=0x7f5115c1a520, bb=0x7f5115c186e0) at byterange_filter.c:494
#7  0x00007f51130855f4 in deflate_out_filter (f=<optimized out>, bb=0x7f5115c186e0) at mod_deflate.c:831
#8  0x00007f511285f10a in filter_harness (f=0x7f5115c17860, bb=0x7f5115c186e0) at mod_filter.c:323
#9  0x00005574845312df in ap_http_filter (f=<optimized out>, b=0x7f5115c18540, mode=<optimized out>, block=<optimized out>, readbytes=16384)
    at http_filters.c:555
#10 0x00007f5111cf941f in php_apache_sapi_read_post (buf=0x7fffa5bf0500 "", count_bytes=16384) at ./sapi/apache2handler/sapi_apache2.c:198
#11 0x00007f5111c09d28 in sapi_read_post_block (buffer=buffer@entry=0x7fffa5bf0500 "", buflen=buflen@entry=16384) at ./main/SAPI.c:248
#12 0x00007f5111c0a77d in sapi_deactivate () at ./main/SAPI.c:513
#13 0x00007f5111c00ab9 in php_request_shutdown (dummy=dummy@entry=0x0) at ./main/main.c:1863
```

{% include fig.html name="php-chunked-flow" num="1" caption="The path from a malformed chunked request to a response that echoes the request body." %}

So, what's a bucket brigade?

### Buckets

A bucket is a container for data. Buckets can contain any type of data.
Although the most common case is a block of memory, a bucket may instead contain a file on disc, or even be fed a data stream from a dynamic source such as a separate program.
Different bucket types exist to hold different kinds of data and the methods for handling it. In OOP terms, the apr_bucket is an abstract base class from which actual bucket types are derived.
There are several different types of data bucket, as well as metadata buckets. We will describe these at the end of this article.

### Brigades

In normal use, there is no such thing as a freestanding bucket: they are contained in bucket brigades.
A brigade is a container that may hold any number of buckets in a ring structure.
The brigade serves to enable flexible and efficient manipulation of data, and is the unit that gets passed to and
from your filter.

> Bucket memory gets intialized way above and waits till the chunked data enters into the memory stream before even it is destroyed.
> Now, the brigade memory is mishandled into the way of response brigade memory.

Handlers responsible for this vulnerability is sapi_apache2.c:

```c
	if (!parent_req) {
		php_apache_request_dtor(r);
		ctx->request_processed = 1;
		bucket = apr_bucket_eos_create(r->connection->bucket_alloc);
		APR_BRIGADE_INSERT_TAIL(brigade, bucket);
```

Patch:

```c
	if (!parent_req) {
		php_apache_request_dtor(r);
		ctx->request_processed = 1;
		bucket = apr_bucket_eos_create(r->connection->bucket_alloc);
		brigade = apr_brigade_create(r->pool, r->connection->bucket_alloc);
		APR_BRIGADE_INSERT_TAIL(brigade, bucket);
```

{% include fig.html name="php-brigade-patch" num="2" caption="What the one-line patch changes: the end-of-stream bucket goes into a fresh brigade instead of the one that still holds leftover data." %}

Fix added to security repo as 65bc4f464e6a85aad3f578e9d55520601cbdeccf and to <https://gist.github.com/smalyshev/e956dbae936df9a7594750caae8a7cf2>

<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/syE9GAlA22s" title="Video demonstration" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe></div>
