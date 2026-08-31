---
title: Why the Derivative of ln(x) Is 1/x
category: Mathematics
summary: A short proof from the definition of e, and why the result falls out of the number itself rather than being a rule to memorize.
---

Every calculus student learns that the derivative of ln(x) is 1/x. Most learn it as a rule to apply, not a fact to understand. That's a shame, because the proof is short, and it shows you something real about where the number *e* comes from in the first place.

Start with the definition of a derivative: the derivative of a function f at x is the limit, as h approaches 0, of [f(x+h) − f(x)] / h. Apply that to f(x) = ln(x):

**[ln(x+h) − ln(x)] / h**

Logarithms turn division into subtraction, so ln(x+h) − ln(x) = ln((x+h)/x) = ln(1 + h/x). The expression becomes:

**ln(1 + h/x) / h**

Now substitute u = h/x, so h = ux. As h approaches 0, u also approaches 0 (since x is fixed and nonzero). Rewrite:

**ln(1 + u) / (ux) = (1/x) · [ln(1 + u) / u]**

Everything now hinges on the piece in brackets: what does ln(1 + u)/u approach as u goes to 0? Rewrite it once more using the property that (1/u)·ln(1+u) = ln((1+u)^(1/u)):

**ln[(1 + u)^(1/u)]**

And here's the payoff. As u approaches 0, the expression (1 + u)^(1/u) approaches a specific number — approximately 2.71828 — which is, by definition, *e*. This is in fact one of the standard ways to define *e*: it's the limit of (1 + u)^(1/u) as u → 0, or equivalently the limit of (1 + 1/n)^n as n → ∞. So the bracketed piece approaches ln(e), which equals 1, because ln is defined as the logarithm base e — the function that asks "e to what power gives this number," and the answer for e itself is obviously 1.

Put it together: the whole expression approaches (1/x) · 1 = **1/x**.

The derivative isn't an arbitrary rule bolted onto ln(x). It's a direct consequence of what *e* means. *e* is defined, at its core, as the number that makes this exact limit come out to 1. The natural logarithm is the logarithm with base *e* specifically because that choice is the one that makes the derivative clean. Every other base for a logarithm gives you a derivative with an extra constant multiplied in — the derivative of log₂(x), for instance, is 1/(x·ln 2), because base 2 doesn't have this special relationship with the limit. Base *e* is the one base where the constant is 1, which is another way of saying *e* isn't picked for calculus — calculus is the reason anyone cares about *e* at all.

This also explains something that seems like a coincidence the first time you see it: the function e^x is its own derivative. If y = ln(x) has derivative 1/x, then x = e^y, and differentiating implicitly gives dx/dy = e^y — meaning dy/dx = 1/e^y = 1/x, which checks out, and by symmetry d/dx(e^x) = e^x. These two facts — the derivative of ln(x) is 1/x, and the derivative of e^x is itself — are really the same fact viewed from two directions. Both come from the same limit definition of *e*.

The next time the rule "derivative of ln(x) is 1/x" comes up, it's worth remembering it isn't a rule at all. It's the definition of *e* wearing a different hat.
