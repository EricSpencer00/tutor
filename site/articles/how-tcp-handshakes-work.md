---
title: The Three-Way Handshake, and Why It Needs Exactly Three
category: Computing
summary: SYN, SYN-ACK, ACK — the minimum number of messages two strangers need to agree they can both send and receive, explained from first principles.
---

Every TCP connection on the internet — every web page load, every SSH session, every API call — opens with the same three-message ritual before a single byte of real data moves. It's called the three-way handshake, and the "three" isn't an arbitrary protocol choice. It's the minimum needed to solve a genuine problem: two computers that have never talked before need to agree they can both send to each other and both receive from each other, over a network where any message might get lost.

Call the two sides client and server. The client wants to open a connection.

**Message 1: SYN.** The client sends a packet with the SYN (synchronize) flag set and a random starting sequence number, call it X. This says: "I want to talk, and my messages to you will be numbered starting from X." At this point the client knows nothing about the server — it doesn't even know if the server received the message.

**Message 2: SYN-ACK.** If the server is listening and accepts, it replies with two things bundled into one packet: an ACK (acknowledgment) of the client's SYN, confirming "I got your message starting at X, I'm expecting X+1 next," and its own SYN with its own random sequence number Y, saying "and here's where *my* messages to you will start." This single packet does double duty — it's both a reply and a request.

**Message 3: ACK.** The client acknowledges the server's SYN: "Got your Y, expecting Y+1 next." Now both sides have confirmed both directions, and data can flow.

Why can't this be done in two messages? Because after message 2, the server has proven it received the client's SYN, but the client hasn't yet proven anything back to the server. If data started flowing right after message 2, the server would be sending real data to a client that might not exist — the original SYN could have been a spoofed packet, or the client might have given up and disappeared. Message 3 is the server's confirmation that the client is really there, actively participating, not just a stray packet. Two messages can confirm one direction is working; you need a third to confirm the second direction back.

Could it be four? In principle, acknowledging the client's SYN and sending the server's own SYN could be two separate packets instead of one combined SYN-ACK. TCP just combines them as an optimization, since they're going the same direction at the same moment anyway — no reason to pay for two round trips of latency when one will do.

This structure is also why a common attack, the **SYN flood**, works the way it does. An attacker sends a huge number of SYN packets, often with spoofed source addresses, and never completes the handshake. The server allocates a small amount of memory for each half-open connection while it waits for the final ACK — and if enough SYNs arrive without their matching ACKs, that memory fills up and the server can't accept real connections. Defenses like SYN cookies work by making the server *not* store any state after message 1: it encodes the connection info directly into the sequence number of its SYN-ACK, so it only allocates real memory once the final ACK proves the client is genuine, not before.

The handshake also explains why TCP feels "reliable" in a way that just firing off packets doesn't. Sequence numbers, established here in messages 1 and 2, are what let both sides detect a lost or out-of-order packet later in the conversation and ask for it again. The handshake isn't just a greeting — it's where the bookkeeping that makes the rest of the connection trustworthy gets set up.
