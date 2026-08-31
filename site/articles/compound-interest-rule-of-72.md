---
title: The Rule of 72, and Why It's Close Enough
category: Finance
summary: A mental-math shortcut for compound growth, where it comes from, and the one assumption that makes it wrong for volatile returns.
---

If you want to know how long it takes money to double at a given annual growth rate, there's a shortcut that beats pulling out a calculator: divide 72 by the rate. Money growing at 8% a year doubles in about 72/8 = 9 years. At 6%, about 12 years. At 12%, about 6 years. It's fast, it's memorable, and it's accurate enough for most real decisions — but understanding why it works also tells you exactly when to stop trusting it.

The real question the rule answers is: for what n does (1 + r)^n = 2? Take the natural log of both sides: n·ln(1+r) = ln(2). So n = ln(2)/ln(1+r). ln(2) is about 0.693. For small r, ln(1+r) is approximately equal to r itself — this is the standard small-angle-style approximation, and it's good as long as r stays under roughly 15–20%. So n ≈ 0.693/r, or equivalently, n ≈ 69.3/(r as a percentage).

That gives you the Rule of 69.3, which is mathematically the more honest number. Why does everyone use 72 instead? Because 72 has far more divisors — 1, 2, 3, 4, 6, 8, 9, 12 — making the mental division cleaner across the growth rates people actually deal with (6%, 8%, 9%, 12%), while 69.3 divides cleanly by almost nothing. The rule trades a small amount of precision for a large amount of doing math in your head, and for rates in the 6–10% range, that trade barely costs you anything — the Rule of 72 is accurate to within a few percent of the true doubling time in exactly the range most savings and investment returns fall into.

Here's where it breaks: the approximation ln(1+r) ≈ r gets worse as r grows, so the Rule of 72 gets noticeably less accurate at high rates — above about 20% it starts overstating doubling time meaningfully, and at very low rates under 2% it slightly understates it (69 or 70 gives a better answer down there). But the deeper issue isn't the approximation error. It's the assumption sitting underneath the whole calculation: a single, fixed, compounding rate applied every year without interruption.

Real returns don't work that way. A stock portfolio that averages 8% a year might actually go up 25% one year and down 15% the next. The Rule of 72 implicitly assumes smooth compounding, but volatile returns compound worse than their arithmetic average suggests — a well-known result sometimes called "volatility drag." A portfolio that goes up 50% then down 50% is not back where it started; it's down 25% (1.5 × 0.5 = 0.75). The arithmetic average of +50% and −50% is 0%, but the actual outcome is a 25% loss. Apply the Rule of 72 using an arithmetic average return on a volatile asset and you'll get a doubling time that's too optimistic, because the rule has no way to see the difference between a steady 8% and a jagged path that averages 8%.

This is also the reason the Rule of 72 is genuinely reliable for things like fixed-rate savings accounts, bonds held to maturity, or loan interest — cases where the rate really is fixed and compounding really is uninterrupted — and genuinely misleading as a promise about stock market returns, where the number being plugged in is a historical average papering over a much bumpier reality. The math of the rule is sound; the danger is always in what got fed into r.
