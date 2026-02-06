---
title: URL Shortener Basics – Base62, Bitly Style, and Snowflake IDs
date: 2026-02-06
categories: [system-design, backend]
tags: [url-shortener, base62, snowflake, bitly]
---

A URL shortener (like Bitly, TinyURL) converts long links into short, shareable ones (e.g., hilailght.com/abc123 → long-article-url). The core challenge is generating **unique, short, collision-free codes** at scale without a central bottleneck.

### Common Approaches for Short Code Generation

1. **Simple Hashing (e.g., MD5/SHA of URL)**  
   Take hash → truncate → encode. Problem: collisions possible (two URLs same short code), needs check/regen. Not ideal for high scale.

2. **What Bitly & Most Modern Shorteners Use**  
   - Generate unique numeric **ID** first (not from URL content).  
   - Convert ID to short string using **Base62** encoding (chars: 0-9, a-z, A-Z — 62 options, URL-safe, no +/= like Base64).  
   - Base64 includes + / = → not great for URLs (needs escaping).  
   - Base62 is preferred: denser than Base36, case-sensitive, very compact.  
   Example: number 123456789 → Base62 might become "3x7pQ".

   Bitly-style services avoid pure random strings (collision risk via birthday paradox). Instead: monotonic/unique IDs → Base62.

3. **Snowflake-Style ID Generation (Distributed, Scalable)**  
   Twitter's Snowflake (used by many systems, including shorteners): 64-bit ID, no central DB hit.  
   Structure (typical):  
   - 41–42 bits: timestamp (ms since custom epoch) → sortable by time.  
   - 10 bits: machine/datacenter ID.  
   - 12 bits: sequence number (per ms, up to 4096).  

   Result: globally unique 64-bit int, generated locally on any server.  
   Encode this 64-bit number to **Base62** → ~10–11 chars (62^10 ≈ 839 billion, 62^11 huge).  
   For shorter codes (7 chars ≈ 3.5 trillion combos), use adjusted bits or range allocation.  
   Advantages:  
   - No coordination needed → scales horizontally.  
   - Time-ordered IDs → good for analytics.  
   - Zero collisions by design.

### Quick Example Flow
- User submits long URL.  
- Server generates Snowflake ID (e.g., 18446744073709551615).  
- Convert to Base62: e.g., "Lygb" (shortened).  
- Store mapping: short code → long URL (in DB like PostgreSQL/Redis).  
- Redirect: hilailght.com/Lygb → 301 to original.

This is clean, scalable, and avoids the pitfalls of hashing or pure random. For our site, if we ever build one, Snowflake + Base62 is a solid choice.

Learning system design one concept at a time!
