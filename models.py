"""Shared message classes. Every agent imports its messages from here (Phase 4).

Agreed vocabulary, so all agents use the same fields:

- Category, one per interviewee quote, drives the weighted demand score:
  compliment, hypothetical, past_behavior, commitment
- Signal label, shown to the founder with a confidence:
  real_signal, politeness, neutral
  (proposed roll-up: past_behavior/commitment -> real_signal,
   compliment/hypothetical -> politeness, otherwise neutral)
- Verdict: keep_going, narrow_down, try_a_new_angle, pivot
"""
from uagents import Model  # noqa: F401
